import os
import requests
import operator
import re
import nltk
from datetime import datetime, timedelta
import time
from flask import Flask,request,json,jsonify,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import redis
from rq import Queue, Worker, Retry
from rq.job import Job
import utils
from stop_words import stops
from collections import Counter
from bs4 import BeautifulSoup

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)
q = Queue(connection=conn)



app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import *

def count_and_save_words(url):
    errors = []

    try:
        r = requests.get(url)
    except:
        errors.append(
            "Unable to get URL. Please make sure it's valid and try again."
        )
        return {"error": errors}

    # text processing
    raw = BeautifulSoup(r.text, 'html.parser').get_text()
    nltk.data.path.append('./nltk_data/')  # set the path
    tokens = nltk.word_tokenize(raw)
    text = nltk.Text(tokens)

    # remove punctuation, count raw words
    nonPunct = re.compile('.*[A-Za-z].*')
    raw_words = [w for w in text if nonPunct.match(w)]
    raw_word_count = Counter(raw_words)

    # stop words
    no_stop_words = [w for w in raw_words if w.lower() not in stops]
    no_stop_words_count = Counter(no_stop_words)

    # save the results
    try:
        result = Result(
            url=url,
            result_all=raw_word_count,
            result_no_stop_words=no_stop_words_count
        )
        db.session.add(result)
        db.session.commit()
        return result.id
    except:
        errors.append("Unable to add item to database.")
        return {"error": errors}


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

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


@app.route('/start', methods=['POST'])
def get_counts():
    # this import solves a rq bug which currently exists
    from app import count_and_save_words

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
def get_results(job_key):

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



if __name__ == '__main__':
    app.run
