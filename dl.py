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


app = Flask(__name__)
app.secret_key = b'jf764o;03n?mv9936bv?le874nb;s.'
app.config['SECRET_KEY'] = 'giNyIS8Tc9oQR1GIiq6nvhyzg9MOkvMHBilwv16W_rE'
app.config["base_app_url"] = 'http://localhost:5000/checinsm/file'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB max upload size

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
    if current_user != username:
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
        f.save('files/' + current_user +'/' + secure_filename(f.filename))
    #return make_response('Success', 200)
    return redirect(f'{app.config["base_app_url"]}/list', code=301)


# @app.route('/checinsm/dl/canUpload', methods=['GET'])
# @token_required
# def can_upload(current_user):
#     return jsonify({"can_upload" : can_upload_files(current_user)})


# @app.route('/checinsm/dl/list', methods=['GET'])
# @token_required
# def list(current_user):
#     files = files_list(current_user)

#     output = []

#     for file in files:
#         file_data = {}
#         file_data["url"] = f'{request.url_root}checinsm/dl/files/{current_user}/{file}'
#         file_data["filename"] = file
#         output.append(file_data)
#     return jsonify({'files': output})


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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4500, debug=True)