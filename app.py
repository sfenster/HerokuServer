from flask import Flask,request,json
import os

app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)

@app.route('/')
def hello():
    secret_key = app.config.get("SECRET_KEY")
    return f"The configured secret key is {secret_key}."

@app.route('/githubIssue',methods=['POST'])
def githubIssue():
    data = request.json
    print(f'Issue {data["issue"]["title"]} {data["action"]}')
    print(f'{data["issue"]["body"]}')
    print(f'{data["issue"]["url"]}')
    return data

if __name__ == '__main__':
    app.run(debug=True)
