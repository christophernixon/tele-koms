"""Messaging application server."""
from flask import Flask, request, render_template, redirect
from typing import List
import json

app = Flask(__name__)

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

@app.route('/messages', methods=['POST'])
def add_message():
    """Add a message to the message_database."""
    req_data = request.get_json()
    message = req_data['message']
    message_database.append(message)
    print("Recieved message: '{0}' and added it to message database.".format(message))
    return redirect('/')

@app.route('/allmessages', methods=['GET'])
def get_messages():
    """Dump message database."""
    database_dump = ''.join(message_database)
    return render_template("index.html", message="All messages:"+database_dump)

if __name__ == "__main__":
    app.run(debug=True)
