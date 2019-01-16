from flask import Flask
from flask import request
from flask import make_response
from flask import send_from_directory
from flask import redirect
from werkzeug.utils import secure_filename
import os, os.path
from flask import jsonify
import jwt
from functools import wraps
from datetime import datetime
import requests
import json
import pika


with open('config.json') as f:
    config = json.load(f)


app = Flask(__name__)
app.secret_key = b'jf764o;03n?mv9936bv?le874nb;s.'
app.config['SECRET_KEY'] = config['SECRET_KEY']
app.config["base_app_url"] = config["base_app_url"]
app.config["notification_url"] = config["notification_url"]
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB max upload size

exchange = 'checinsm-minify'
exchange_type = 'direct'
routing_key = ''

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.form.get('jwt') or request.args.get('jwt')

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = data['username']
            expiration = datetime.utcfromtimestamp(data['exp'])
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        if expiration < datetime.utcnow():
            return jsonify({'message' : 'Token is invalid! Token Expired!'}), 401

        if not current_user:
            return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/checinsm/dl/files/<username>/<filename>', methods=['GET'])
@token_required
def download(current_user, username, filename):
    if current_user != username and current_user != 'shared':
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    root_dir = os.path.dirname(os.getcwd())+'/file'
    return send_from_directory(os.path.join(root_dir, 'files', username), filename, as_attachment=True)


@app.route('/checinsm/dl/upload', methods=['POST'])
@token_required
def upload(current_user):
    if can_upload_files(current_user) == False:
        return make_response("You cannot upload more files", 403)
    if request.method == 'POST':
        f = request.files['file']
        path = 'files/' + current_user +'/' + secure_filename(f.filename)
        f.save(path)
        data = {'filename':secure_filename(f.filename)}
        requests.post(app.config["notification_url"]+'/'+current_user, data=data, verify=False)
        send_minify(path, f.filename)
    #return make_response('Success', 200)
    return redirect(f'{app.config["base_app_url"]}/list', code=301)


def can_upload_files(username):
    files = files_list(username)
    if len(files) < 5:
        return True
    return False


def files_list(username):
    path = './files/'+username
    if not os.path.exists(path):
        os.makedirs(path)
    return os.listdir(path)

def send_minify(path, filename):
    if filename.endswith(('.png', '.jpg', '.jpeg')):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        channel.exchange_declare(exchange=exchange,
                                exchange_type=exchange_type)
        channel.basic_publish(exchange=exchange,
                            routing_key=routing_key,
                            body=path)
        connection.close()



if __name__ == "__main__":
    app.run("0.0.0.0", 4500)