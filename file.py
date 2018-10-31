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

curr_dir = os.getcwd()

print(os.path.join(curr_dir, 'static'))

app = Flask(__name__, static_url_path='/static/')
app.secret_key = b'jf764o;do7?mv9936bv?lkgt67;s.'

app.config['SECRET_KEY'] = 'giNyIS8Tc9oQR1GIiq6nvhyzg9MOkvMHBilwv16W_rE'
app.config['base_api_url'] = 'http://localhost:4500/checinsm/dl'
app.config["base_app_url"] = 'http://localhost:5000/checinsm/file'

redis = redis.Redis()

def register_user(username, password):
    if redis.get('checinsm:user:'+username+':password'):
        return False
    salt = ''.join(random.choices(string.ascii_letters+string.digits, k=16))
    passwd = hashlib.sha3_256(password.encode('utf-8')+salt.encode('utf-8')).hexdigest()
    redis.set('checinsm:user:'+username+':password', passwd)
    redis.set('checinsm:user:'+username+':salt', salt)
    return True

register_user('michal', 'haslo')


@app.route('/checinsm/file/')
def index():
    return render_template('index.html')


@app.route('/checinsm/file/login', methods=['POST', 'GET'])
def login():
    username = username_from_cookie(request.cookies.get('userID'))
    if username:
        return redirect(url_for('list'))
        
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            return log_the_user_in(request.form['username'])
        else:
            error = 'Invalid username/password'
    return render_template('login.html', error=error)


@app.route('/checinsm/file/register', methods=['POST', 'GET'])
def register():
    username = username_from_cookie(request.cookies.get('userID'))
    if username:
        return redirect(url_for('list'))
        
    error = None
    if request.method == 'POST':
        if register_user(request.form['username'], request.form['password']):
            return redirect(url_for('login'))
        else:
            error = 'Username exists in app already'
    return render_template('register.html', error=error)


@app.route('/checinsm/file/logout', methods=['GET'])
def logout():
    username = username_from_cookie(request.cookies.get('userID'))
    delete_user_token(username)
    resp = make_response(render_template('logout.html'))
    resp.set_cookie('userID', '', expires=0, secure=True, httponly=True)
    return resp


@app.route('/checinsm/file/list')
def list():
    username = username_from_cookie(request.cookies.get('userID'))
    if username is None:
        return render_template('login.html', error='Musisz sie najpierw zalogować')

    files = files_name_url(username)

    return render_template('list.html', files=files, can_upload=can_upload(username), jwt=make_jwt(username), upload_url=app.config['base_api_url']+"/upload")


@app.route('/checinsm/file/files/<username>/<filename>', methods=['GET'])
def download(username, filename):
    cookie_username = username_from_cookie(request.cookies.get('userID'))
    if cookie_username is None:
        return render_template('login.html', error='Musisz sie najpierw zalogować')
    if cookie_username != username:
        return render_template('fileerr.html', error='Nieładnie tak pobierać nieswoje pliki!')
    jwt = make_jwt(username)
    return redirect(f'{app.config["base_api_url"]}/files/{username}/{filename}?jwt={jwt}', code=301)


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
    resp.set_cookie('userID', cookie, expires=expire_date)#, secure=True, httponly=True)
    return resp


def insert_user_token(username):
    token = token_generate()
    redis.set('checinsm:token:'+token+':username', username)
    return token


def delete_user_token(username):
    if not username:
        return
    redis.set('checinsm:user:'+username+':token', '')


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
        file_data["url"] = f'{app.config["base_app_url"]}/files/{username}/{file}'
        file_data["filename"] = file
        output.append(file_data)

    return output


def make_jwt(username, expiration_minutes=3):
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes)
    return jwt.encode({'username': username, 'exp' : expiry}, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
