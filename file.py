from flask import Flask
from flask import request
from flask import render_template
from flask import make_response
from flask import redirect
from flask import url_for
import os, os.path
import json
import string
import random
import redis
import hashlib
import jwt
import datetime
import requests
from authlib.flask.client import OAuth
from six.moves.urllib.parse import urlencode


curr_dir = os.getcwd()


with open('config.json') as f:
    config = json.load(f)


app = Flask(__name__, static_url_path='/checinsm/file/static')
app.secret_key = config['app_secretkey']

app.config['SECRET_KEY'] = config["SECRET_KEY_JWT"]
app.config['base_api_url'] = config["base_api_url"]
app.config["base_app_url"] = config["base_app_url"]
app.config["auth0_callback_url"] = config["auth0_callback_url"]
app.config["auth0_client_id"] = config["auth0_client_id"]
app.config["auth0_base_url"] = config["auth0_base_url"]

oauth = OAuth(app)

shared_dict = dict()

redis = redis.Redis()

auth0 = oauth.register(
    'auth0',
    client_id = app.config["auth0_client_id"],
    client_secret = config["auth0_secret"],
    api_base_url = app.config["auth0_base_url"],
    access_token_url = app.config["auth0_base_url"]+'/oauth/token',
    authorize_url = app.config["auth0_base_url"]+'/authorize',
    client_kwargs={
        'scope': 'openid profile',
    },
)


@app.route('/checinsm/file/')
def index():
    return render_template('index.html')


@app.route('/checinsm/file/login')
def login():
    return auth0.authorize_redirect(redirect_uri=app.config["auth0_callback_url"], audience=app.config["auth0_base_url"]+'/userinfo')


@app.route('/checinsm/file/callback')
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    return log_the_user_in(userinfo['name'])


@app.route('/checinsm/file/logout', methods=['GET'])
def logout():
    username = username_from_cookie(request.cookies.get('userID'))
    delete_user_token(username)
    params = {'returnTo': url_for('index', _external=True), 'client_id': app.config["auth0_client_id"]}
    resp = redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))
    resp.set_cookie('userID', '', expires=0)#, secure=True, httponly=True)
    return resp


@app.route('/checinsm/file/list')
def list():
    username = username_from_cookie(request.cookies.get('userID'))
    if username is None:
        return redirect(url_for('login'))

    files = files_name_url(username)

    return render_template('list.html', files=files, can_upload=can_upload(username), jwt=make_jwt(username), upload_url=app.config['base_api_url']+"/upload", username=username)

@app.route('/checinsm/file/upload')
def upload():
    username = username_from_cookie(request.cookies.get('userID'))
    if username is None:
        return redirect(url_for('login'))

    return render_template('upload.html', can_upload=can_upload(username), jwt=make_jwt(username), upload_url=app.config['base_api_url']+"/upload", username=username)


@app.route('/checinsm/file/files/<username>/<filename>', methods=['GET'])
def download(username, filename):
    cookie_username = username_from_cookie(request.cookies.get('userID'))
    if cookie_username is None:
        return redirect(url_for('login'))
    if cookie_username != username:
        return render_template('fileerr.html', error="You're trying to download not your files. You rebel ;)", username=cookie_username)
    jwt = make_jwt(username)
    return redirect(f'{app.config["base_api_url"]}/files/{username}/{filename}?jwt={jwt}', code=301)


@app.route('/checinsm/file/share', methods=['GET'])
def share():
    cookie_username = username_from_cookie(request.cookies.get('userID'))
    if cookie_username is None:
        return redirect(url_for('login'))
    filename = request.args.get('file')
    # if not filename in files_name_url(cookie_username):
    #     return render_template('fileerr.html', error='Nie masz takiego pliku!')
    file_uname = cookie_username+"/"+filename
    m = hashlib.md5()
    m.update(file_uname.encode('utf-8'))
    file_md5 = m.hexdigest()
    if file_md5 not in shared_dict:
        shared_dict[file_md5] = file_uname
    return render_template('share.html', filename=filename, username=cookie_username, link=f'{app.config["base_app_url"]}/download/{file_md5}')


@app.route('/checinsm/file/download/<filehash>', methods=['GET'])
def dowload_share(filehash):
    file = shared_dict.get(filehash)
    if not file:
        return render_template('fileerr.html', error='Cannot fild that file')
    jwt = make_jwt('shared')
    return redirect(f'{app.config["base_api_url"]}/files/{file}?jwt={jwt}', code=301)


def valid_login(username, password):
    redis_password = redis.get('checinsm:user:'+username+':password').decode('utf-8')
    redis_salt = redis.get('checinsm:user:' + username + ':salt').decode('utf-8')

    if not redis_password or not redis_salt:
        return False

    hashed_password = hashlib.sha3_256(password.encode('utf-8') + redis_salt.encode('utf-8')).hexdigest()
    if redis_password == hashed_password:
        return True
    return False


def log_the_user_in(username):
    import datetime
    expire_date = datetime.datetime.now() + datetime.timedelta(days=1)
    cookie = insert_user_token(username)
    resp = redirect(url_for('list'))
    resp.set_cookie('userID', cookie)#, expires=expire_date, secure=True, httponly=True)
    return resp


def insert_user_token(username):
    token = token_generate()
    redis.set('checinsm:token:'+token+':username', username)
    return token


def delete_user_token(username):
    if not username:
        return
    redis.delete('checinsm:user:'+username+':token')


def username_from_cookie(cookie):
    if not cookie:
        return None
    return redis.get('checinsm:token:'+cookie+':username').decode('utf-8')


def token_generate():
    import uuid
    return str(uuid.uuid4().hex)


def can_upload(username):
    files = files_list(username)
    if len(files) < 5:
        return True
    return False


def files_list(username):
    path = './files/'+username
    if not os.path.exists(path):
        os.makedirs(path)
    return os.listdir(path)


def files_name_url(username):
    files = files_list(username)

    output = []

    for file in files:
        file_data = {}
        file_data["url"] = f'files/{username}/{file}'
        file_data["filename"] = file
        file_data["mini"] = None

        if file.endswith(('.png', '.jpg', '.jpeg')):
            file_data["mini"] = 'static/mini/'+file
            
        output.append(file_data)

    return output


def make_jwt(username, expiration_minutes=3):
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes)
    return jwt.encode({'username': username, 'exp' : expiry}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)