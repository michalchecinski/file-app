from flask import Flask
from flask import session
from flask import request
from flask import make_response
from flask import send_from_directory
from flask import abort
from werkzeug.utils import secure_filename
import os, os.path
import json
from flask import jsonify

app = Flask(__name__, static_url_path='/checinsm/file/static')
app.secret_key = b'jf764o;03n?mv9936bv?le874nb;s.'

@app.route('/checinsm/dl/files/<username>/<filename>', methods=['GET'])
def download(username, filename):
    cookie_username = username_from_cookie(request.cookies.get('userID'))
    if cookie_username is None:
        abort(401)
    if cookie_username != username:
        abort(403)
    root_dir = os.path.dirname(os.getcwd())+'/file'
    return send_from_directory(os.path.join(root_dir, 'files', username), filename, as_attachment=True)


@app.route('/checinsm/dl/upload', methods=['POST'])
def upload():
    username = username_from_cookie(request.cookies.get('userID'))
    if username is None:
        abort(401)

    print(request.files)
    if can_upload_files(username) == False:
        return "You cannot upload more files"
    if request.method == 'POST':
        f = request.files['file']
        f.save('files/' + username +'/' + secure_filename(f.filename))
    return "Success"


@app.route('/checinsm/dl/list', methods=['GET'])
def list():
    username = username_from_cookie(request.cookies.get('userID'))
    if username is None:
        abort(401)

    files = files_list(username)
    return jsonify(files)


def username_from_cookie(cookie):
    with open('users.json', 'r') as j:
        datastore = json.load(j)

    for row in datastore['users']:
        if row['token'] == cookie:
            return row['username']
    return None


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
