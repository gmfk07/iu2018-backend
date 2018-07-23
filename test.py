# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 13:04:42 2018

@author: gmfk07
"""

from functools import wraps
from flask import Flask, request, jsonify


app = Flask(__name__)

@app.errorhandler(404)
def not_found(e):
    message = {
            'status': 404,
            'message': "Error!"
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    message = {'message': "Authenticate."}
    resp = jsonify(message)

    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'

    return resp

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/', methods=["GET", "POST"])
def api_hello():
    if request.method == "GET":
        if 'name' in request.args:
            return 'Hi, ' + request.args['name']
        else:
            return 'Sorry, I only talk to people with names.'
    elif request.method == "POST":
        if request.headers['Content-Type'] == 'application/json':
            providedJs = request.json;
            
            data = {
                'newID'  : providedJs["userID"] + 1,
                'newMeme' : not providedJs["dankMeme"]
            }
        
            resp = jsonify(data)
            resp.status_code = 200
            resp.headers['Link'] = 'http://build-it-yourself.com'
        
            return resp
        
@app.route('/planets/<planetName>', methods = ['GET'])
def api_users(planetName):
    planets = {'Earth':'142', 'Mars':'143'}
    
    if planetName in planets:
        return jsonify({planetName: planets[planetName]})
    else:
        return not_found()

@app.route('/secrets', methods = ['GET'])
@requires_auth
def api_secret():
    return "Shhh this is top secret spy stuff!"

if __name__ == "__main__":
    app.run(debug = True)