"""Messaging application server."""
from flask import Flask, request, render_template, redirect

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Return landing page."""
    return render_template("index.html", message="Testing Landing Page")


@app.route('/ping', methods=['GET'])
def ping():
    """Register a GET request by printing to console."""
    print("PING to server.")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
