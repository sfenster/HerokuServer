from flask import Flask,request,json,jsonify,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import config
from rq import Queue
from rq.job import Job
from worker import conn
from utils import count_words_at_url
from werkzeug.utils import import_string


q = Queue(connection=conn)
result = q.enqueue(count_words_at_url, 'http://heroku.com')


app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from models import Result

@app.route('/')
def hello():
    debug_status = app.config.get('DEBUG')
    dev_status = app.config.get('DEVELOPMENT')
    config_flaskenv = app.config.get('FLASK_ENV')
    secret_key = app.config.get("SECRET_KEY")
    return f"The config DEBUG status is: {debug_status}."
    #return f"The configured secret key is {secret_key}."

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
@app.route('/redis/', methods=['GET', 'POST'])
def testredis():
        return render_template('index.html')

@app.route('/start', methods=['POST'])
def get_counts():
    # this import solves a rq bug which currently exists
    #from app import count_and_save_words

    # get url
    data = json.loads(request.data.decode())
    url = data["url"]
    print("URL from form = " + url)
    if not url[:8].startswith(('https://', 'http://')):
        url = 'http://' + url
    # start job
    job = q.enqueue_call(
        func=count_words_at_url, args=(url,), result_ttl=5000
    )
    # return created job id
    return job.get_id()


@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):

    job = Job.fetch(job_key, connection=conn)

    if job.is_finished:
        #result = Result.query.filter_by(id=job.result).first()
        #results = sorted(
        #    result.result_no_stop_words.items(),
        #    key=operator.itemgetter(1),
        #    reverse=True
        #)[:10]
        #return jsonify(results)
        print("Job fetch result: " + str(job.result))
        return str(job.result)
    else:
        return "Nay!", 202

if __name__ == '__main__':
    app.run
