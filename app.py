import os
import requests
import operator
import re
import nltk
from datetime import datetime, timedelta
import time
from flask import Flask,request,json,jsonify,render_template,flash,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import redis
from rq import Queue, Worker, Retry
from rq.job import Job
from utils import count_and_save_words
from handler import run_actions
from stop_words import stops
from collections import Counter
from bs4 import BeautifulSoup
from pathlib import Path
from flask_login import current_user,login_user,LoginManager,logout_user,login_required


FILE_DIR = Path(__file__).resolve().parent
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)
q = Queue(connection=conn)


app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

from models import *
from forms import *

def run_workflow(name, webhook_data):
    #Get path of json workflow file matching webhook path, load file, get actions, call enqueue_action() to run
    workflow_path = FILE_DIR / f"workflows/{name}.json"
    with open(workflow_path) as f:
        config = json.load(f)

    actions = config["actions"]
    enqueued_jobs = []
    errors = []
    for action in actions:
        #enqueue_action(action=action, webhook_data=webhook_data)
        #print (action)
        rf = action['action_data']['required_fields'] if 'required_fields' in action['action_data'] else {}
        of = action['action_data']['optional_fields'] if 'optional_fields' in action['action_data'] else {}
        error = False
        for f in rf:
            if f not in webhook_data:
                print(f"ERROR: missing required field {f}; {action['type']} action not enqueued.")
                errors.append({action['type']: f"ERROR: missing required field '{f}'; '{action['type']}' action not enqueued."})
                error=True
                break

        for d in webhook_data:
            if d not in of and d not in rf:
                print(f"ERROR: {d} is not an allowed field; {action['type']} action not enqueued.")
                errors.append({action['type']: f"ERROR: '{d}' is not an allowed field; '{action['type']}' action not enqueued."})
                error = True
                break

        if error == False:
            job = q.enqueue_call(
                func=run_actions, args=(action, webhook_data,), result_ttl=5000
            )
            enqueued_jobs.append({action['type']:job.get_id()})
    for job in enqueued_jobs: print(f"JOB: {job}")
    return {"enqueued_jobs": enqueued_jobs, "errors": errors}



def enqueue_action(action, webhook_data):
    #format dict with webhook data and action step data, enqueue in Redis
    message_data = {
        "webhook_data": webhook_data,
        "action": action,
    }
    job = q.enqueue_call(
        func=run_actions, args=(message_data,), result_ttl=5000
    )
    # return created job id
    print (job.get_id())


#=========WEBHOOK-TO-JOB-QUEUE ENDPOINTS=========



@app.route('/webhook/<path:path>', methods=['GET', 'POST'])
def webhooks_trigger(path):
    config_path = FILE_DIR / f"workflows/{path}.json"
    if config_path.is_file():
        type = request.headers['Content-Type'] if 'Content-Type' in request.headers else ""
        if "json" in type:
            resp = run_workflow(path, request.json)
            return f"Success! We have found the workflow '{path}' and received the following JSON post: \n{request.json} \n \
                Webhook response = {resp}"
        else:
            resp = run_workflow(path, request.args)
            return f"Success! We have found the workflow '{path}' and received the following post parameters: \n{request.args} \n \
                Webhook response = {resp}"

    return f"Workflow: {config_path} not found"


@app.route("/jobs/<job_key>", methods=['GET'])
def get_results(job_key):
        job = Job.fetch(job_key, connection=conn)

        print("Job is finished: ", job.is_finished)
        if job.is_finished:
            return jsonify(job.result)
        else:
            return "Job is not finished", 202

@app.route('/swoogo', methods=['GET'])
def get_registrants():

    auth_url = "https://www.swoogo.com/api/v1/oauth2/token.json"
    b64_key_secret = "UlR3TTJ5SlRDTjFCaWg5bmxLcEhoOnY3NDJkWVk5d1BKbGVrU2d2VlJZSmFQYTBoWGNsdkdpZnZCcElBREdKcA=="
    auth_headers = {'Content-Type':'application/x-www-form-urlencoded', 'Authorization':'Basic ' + b64_key_secret}
    auth_data = {'grant_type':'client_credentials'}

    auth_resp = requests.post(url=auth_url, headers=auth_headers, data=auth_data).json()

    req_url = 'https://www.swoogo.com/api/v1/registrants.json'
    req_headers = {"Authorization": f"Bearer {auth_resp['access_token']}"}
    id = request.args.get("id", None)
    if id:
        req_params = {'event_id':id}
        response = requests.get(url=req_url, headers=req_headers, params=req_params).json()
    else:
        response = "Please provide an Event ID."

    return response



#=========WORDCOUNT ENDPOINTS=========

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
def index():
    #user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/wordcount', methods=['GET', 'POST'])
@login_required
def wordcount():
    return render_template('wordcount.html')


@app.route('/start', methods=['POST'])
def get_counts():
    # this import solves a rq bug which currently exists
    #from app import count_and_save_words

    # get url
    data = json.loads(request.data.decode())
    url = data["url"]
    if not url[:8].startswith(('https://', 'http://')):
        url = 'http://' + url
    # start job
    job = q.enqueue_call(
        func=count_and_save_words, args=(url,), result_ttl=5000
    )
    # return created job id
    return job.get_id()


@app.route("/results/<job_key>", methods=['GET'])
def get_count_results(job_key):

    job = Job.fetch(job_key, connection=conn)

    print("Job is finished: ", job.is_finished)
    if job.is_finished:
        print("result : ", Result.query.filter_by(id=job.result).first())
        result = Result.query.filter_by(id=job.result).first()
        print("Result items: ", list(result.result_no_stop_words.items())[:10])
        results = sorted(
            result.result_no_stop_words.items(),
            key=operator.itemgetter(1),
            reverse=True
        )[:10]
        return jsonify(results)
    else:
        return "Nay!", 202




#=========OTHER TEST ENDPOINTS=========


@app.route('/name')
def return_name():
    return "Hello World!"


@app.route('/name/<name>')
def hello_name(name):
    return "Hello {}!".format(name)


@app.route('/post/', methods=['POST'])
def post_something():
    param = request.values.get('name')
    print(param)
    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
    if param:
        return jsonify({
            "Message": f"Welcome {param} to our awesome platform!!",
            # Add this option to distinct the POST request
            "METHOD" : "POST"
        })
    else:
        return jsonify({
            "ERROR": "no name found, please send a name."
        })


@app.route('/tasks', methods=['GET'])
def queue_tasks():
    job = q.enqueue(utils.print_task, 5, retry=Retry(max=2))
    job2 = q.enqueue_in(timedelta(seconds=10), utils.print_numbers, 5)
    # return created job id
    return "Job IDs: " + str(job.get_id()) + ", " + str(job2.get_id())



@app.route('/githubIssue',methods=['POST'])
def githubIssue():
    data = request.json
    print(f'Issue {data["issue"]["title"]} {data["action"]}')
    print(f'{data["issue"]["body"]}')
    print(f'{data["issue"]["url"]}')
    return data


@app.route('/getmsg/', methods=['GET'])
def respond():
    # Retrieve the name from url parameter
    name = request.args.get("name", None)

    # For debugging
    print(f"got name {name}")

    response = {}

    # Check if user sent a name at all
    if not name:
        response["ERROR"] = "no name found, please send a name."
    # Check if the user entered a number not a name
    elif str(name).isdigit():
        response["ERROR"] = "name can't be numeric."
    # Now the user entered a valid name
    else:
        response["MESSAGE"] = f"Welcome {name} to our awesome platform!!"

    # Return the response in json format
    return jsonify(response)



if __name__ == '__main__':
    app.run
