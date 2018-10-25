from flask import Flask
from flask import session
from flask import request
from flask import render_template
from flask import make_response
from flask import redirect
from flask import url_for
from flask import flash
from flask import send_from_directory
from werkzeug.utils import secure_filename
import os, os.path
import json

app = Flask(__name__, static_url_path='/checinsm/file/static')
app.secret_key = b'jf764o;03n?mv9936bv?le874nb;s.'

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


@app.route('/checinsm/file/logout', methods=['GET'])
def logout():
    resp = make_response(render_template('logout.html'))
    resp.set_cookie('userID', '', expires=0, secure=True, httponly=True)
    return resp


@app.route('/checinsm/file/files/<username>/<filename>', methods=['GET'])
def download(username, filename):
    cookie_username = username_from_cookie(request.cookies.get('userID'))
    if cookie_username is None:
        return render_template('login.html', error='Musisz sie najpierw zalogować')
    if cookie_username != username:
        return render_template('fileerr.html', error='Nie ładnie tak grzebać w nieswoich plikach!')
    root_dir = os.path.dirname(os.getcwd())+'/file'
    return send_from_directory(os.path.join(root_dir, 'files', username), filename, as_attachment=True)


@app.route('/checinsm/file/upload', methods=['POST'])
def upload():
    username = username_from_cookie(request.cookies.get('userID'))
    if username is None:
        return render_template('login.html', error='Musisz sie najpierw zalogować')

    print(request.files)
    if can_upload_files(username) == False:
        return "You cannot upload more files"
    if request.method == 'POST':
        f = request.files['file']
        f.save('files/' + username +'/' + secure_filename(f.filename))
    return redirect(url_for('list'))


@app.route('/checinsm/file/list')
def list():
    username = username_from_cookie(request.cookies.get('userID'))
    if username is None:
        return render_template('login.html', error='Musisz sie najpierw zalogować')

    files = files_list(username)
    return render_template('list.html', files=files, username=username, can_upload=can_upload(username, files))


def valid_login(username, password):
    with open('users.json', 'r') as j:
        datastore = json.load(j)

    for row in datastore['users']:
        if row['username'] == username:
            if row['password'] == password:
                return True
    return False


def log_the_user_in(username):
    import datetime
    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(days=30)
    cookie = cookie_insert(username)
    resp = redirect(url_for('list'))
    resp.set_cookie('userID', cookie, expires=expire_date, secure=True, httponly=True)
    return resp


def cookie_insert(username):
    token = token_generate()
    with open('users.json', 'r') as j:
        datastore = json.load(j)

    for row in datastore['users']:
        if row['username'] == username:
            row['token'] = token

    with open('users.json', 'w') as f:
        json.dump(datastore, f)

    return token


def username_from_cookie(cookie):
    with open('users.json', 'r') as j:
        datastore = json.load(j)

    for row in datastore['users']:
        if row['token'] == cookie:
            return row['username']
    return None


def token_generate():
    import uuid
    return str(uuid.uuid4().hex)


def can_upload_files(username):
    files = files_list(username)
    if len(files) < 5:
        return True
    return False


def can_upload(username, files):
    if len(files) < 5:
        return True
    return False

    
def files_list(username):
    path = './files/'+username
    if not os.path.exists(path):
        os.makedirs(path)
    return os.listdir(path)
