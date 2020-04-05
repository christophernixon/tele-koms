"""Messaging application server."""
from flask import Flask, request, render_template, redirect, make_response, jsonify
from typing import List, Dict
import json
import datetime
import jwt
import os

app = Flask(__name__)

user_database: Dict[str, Dict[str, str]] = {}
message_database: List[str] = []  

@app.route('/', methods=['GET'])
def index():
    """Return landing page."""
    return render_template("index.html", message="Testing Landing Page")

@app.route('/ping', methods=['GET'])
def ping():
    """Register a GET request by printing to console."""
    print("PING to server.")
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    """Log in a user."""
    # get the post data
    post_data = request.get_json()
    try:
        # fetch the user data
        user_email = post_data.get('email')
        user = check_for_user(user_email)
        if user:
            auth_token = encode_auth_token(user_database[user_email]['id'])
            if auth_token:
                responseObject = {
                    'status': 'success',
                    'message': 'Successfully logged in.',
                    'auth_token': auth_token.decode()
                }
                return make_response(jsonify(responseObject)), 200
        else:
            responseObject = {
                'status': 'fail',
                'message': 'User does not exist.'
            }
            return make_response(jsonify(responseObject)), 404
    except Exception as e:
        print(e)
        responseObject = {
            'status': 'fail',
            'message': 'Try again'
        }
        return make_response(jsonify(responseObject)), 500

@app.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    # get the post data
    post_data = request.get_json()
    # check if user already exists
    if 'email' in post_data:
        user = check_for_user(post_data.get('email'))
    else:
        responseObject = {
                'status': 'fail',
                'message': 'No email supplied.'
            }
        return make_response(jsonify(responseObject)), 401
    if not user:
        try:
            username = post_data.get('username')
            user_email = post_data.get('email')
            # insert the user to user_database
            add_user(user_email, username)
            # generate the auth token
            auth_token = encode_auth_token(user_database[user_email]['id'])
            responseObject = {
                'status': 'success',
                'message': 'Successfully registered.',
                'auth_token': auth_token.decode()
            }
            return make_response(jsonify(responseObject)), 201
        except Exception as e:
            responseObject = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.'
            }
            return make_response(jsonify(responseObject)), 401
    else:
        responseObject = {
            'status': 'fail',
            'message': 'User already exists. Please Log in.',
        }
        return make_response(jsonify(responseObject)), 202

@app.route('/messages', methods=['POST'])
def add_message():
    """Add a message to the message_database."""
    req_data = request.get_json()
    if 'auth_token' in req_data:
        auth_token = req_data['auth_token']
        resp = decode_auth_token(auth_token)
        if not isinstance(resp, str):
            message = req_data['message']
            message_database.append(message)
            print("Recieved message: '{0}' and added it to message database.".format(message))
            return redirect('/')
        responseObject = {
            'status': 'fail',
            'message': resp
        }
        return make_response(jsonify(responseObject)), 401
    else:
        responseObject = {
                'status': 'fail',
                'message': 'No auth token found, please log in first.'
            }
        return make_response(jsonify(responseObject)), 401

@app.route('/allmessages', methods=['GET'])
def get_messages():
    """Dump message database."""
    req_data = request.get_json()
    if 'auth_token' in req_data:
        auth_token = req_data['auth_token']
        resp = decode_auth_token(auth_token)
        if not isinstance(resp, str):
            database_dump = ''.join(message_database)
            return render_template("index.html", message="All messages:"+database_dump)
        responseObject = {
            'status': 'fail',
            'message': resp
        }
        return make_response(jsonify(responseObject)), 401
    else:
        responseObject = {
                'status': 'fail',
                'message': 'No auth token found, please log in first.'
            }
        return make_response(jsonify(responseObject)), 401
    

def add_user(email, username):
    """Add a user to the user database."""
    # Find max user id
    max_id = 0
    for tmp_email in user_database:
        if int(tmp_email[id]) > max_id:
            max_id = int(tmp_email[id])
    
    # Add user to database
    tmp_dict: Dict[str, str] = {}
    tmp_dict['id'] = max_id + 1
    tmp_dict['username'] = username
    user_database[email] = tmp_dict


def check_for_user(email):
    """Check user database for a particular email, if found return associated username."""
    if email in user_database:
        return user_database[email]
    else:
        return None

def encode_auth_token(user_id):
    """Generate the Auth Token.

    :return: string
    """
    try:
        SECRET_KEY = os.getenv('SECRET_KEY')
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=1, seconds=0),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        return e

def decode_auth_token(auth_token):
    """Decode the auth token.

    :param auth_token:
    :return: integer|string
    """
    try:
        SECRET_KEY = os.getenv('SECRET_KEY')
        payload = jwt.decode(auth_token, SECRET_KEY)
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

if __name__ == "__main__":
    app.run(debug=True)
