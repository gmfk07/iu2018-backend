# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 19:55:26 2018

@author: gmfk07
"""

from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_cors import CORS
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.utils import secure_filename
import threading
import json as JSON
import os

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

UPLOAD_FOLDER = '/uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app.config['SECRET_KEY'] = '$295jvpq34%#2ds'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)
login_manager = LoginManager(app)

#How many seconds it takes to get a new mission
mission_time = 10

from models import Status, User, Galaxy, System, Planet, CatalogItem, PlanetItem, ChatItem

chatRooms = {}
chatRooms["u"] = []
for galaxy in Galaxy.query.all():
    chatRooms["g" + str(galaxy.id)] = []
for planet in Planet.query.all():
    chatRooms["p" + str(planet.id)] = []

if __name__ == '__main__':
    login_manager.init_app(app)
    socketio.run(app, debug = True)
    

def update_chat_list(inputList, val, maxLength):
    inputList.append(val);
    if len(inputList) > maxLength:
        inputList.remove(inputList[0])
        
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@socketio.on('join', namespace='/test')
def on_join(rm):
    #username = data['username']
    join_room(rm)
    for json in chatRooms[rm]:
        emit('chat history', json)
    #send(username + ' has entered the room.', room=room)

@socketio.on('leave', namespace='/test')
def on_leave(rm):
    #username = data['username']
    room = rm
    leave_room(room)
    #send(username + ' has left the room.', room=room)

@socketio.on('broadcast event', namespace='/test')
def broadcast_chat(json):
    room = JSON.loads(json)['room']
    emit('broadcast response', json, broadcast=True, room=room)
    update_chat_list(chatRooms[room], json, 30)
    
@socketio.on('broadcast event', namespace='/pos')
def broadcast_pos(json):
    room = JSON.loads(json)['room']
    emit('broadcast response', json, broadcast=True, room=room)
    update_chat_list(chatRooms[room], json, 30)
    
@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected'})
    print('Client connected')

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

def new_mission(user_id):
    u = User.query.get(user_id)
    u.mission_type = "visit"
    u.mission_current = 0
    u.mission_total = 10
    db.session.add(u)
    db.session.commit()

def post(data, code=200):
    resp = jsonify(data)
    resp.status_code = 200
    resp.headers['Link'] = 'http://build-it-yourself.com'
    return resp

@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object."""
    return User.query.get(user_id)

@login_required
def logout():
    """Logout the current user."""
    u = current_user
    u.authenticated = False
    db.session.add(u)
    db.session.commit()
    logout_user()

@app.route('/login', methods=["POST", "GET", "DELETE"])
def login():
    #Adding users
    if request.method == "POST" and request.headers['Content-Type'] == 'application/json':
            provided_js = request.json;
            provided_user = provided_js["username"]
            provided_email = provided_js["email"]
            provided_pass = provided_js["password_hash"]
            if User.query.filter_by(username=provided_user).first() == None \
            and User.query.filter_by(email=provided_email).first() == None:
                #Username is unique
                u = User(username = provided_user, email = provided_email,
                         password_hash = provided_pass)
                shop_item = ChatItem.query.filter_by(string='black').first()
                u.chat_items.append(shop_item)
                db.session.add(u)
                try:
                    db.session.commit()
                    data = {'status': 'ok', 'user_id': u.id}
                except:
                    db.session.rollback()
                    data = {'status': 'error', 'note': 'database error'}
                finally:
                    db.session.close()
            else:
                data = {'status': 'error', 'note': 'username/email not unique'}
        
            resp = post(data)
            return resp
    #Test username and password
    if request.method == "GET":
        if "username" in request.args and "password_hash" in request.args:
            u = User.query.filter_by(username=request.args["username"]).first()
            if u is not None and u.password_hash == request.args["password_hash"]:
                u.authenticated = True
                db.session.add(u)
                db.session.commit()
                login_user(u, remember=True)
                data = {'status': 'ok'}
            else:
                data = {'status': 'error', 'note': 'password incorrect'}
        else:
            data = {'status': 'error', 'note': 'wrong args'}
        
        resp = post(data)
        return resp
    #Logout
    if request.method == "DELETE":
        if "username" in request.args:
            try:
                logout()
                data = {'status': 'ok'}
            except:
                db.session.rollback()
                data = {'status': 'error', 'note': 'database error'}
        else:
            data = {'status': 'error', 'note': 'wrong args'}
            
        resp = post(data)
        return resp
    
@app.route('/users', methods=["GET", "PATCH"])
def users():
    #Return user information from id
    if request.method == "GET":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is not None :
                if len(u.planet.all()) == 0:
                    p_id = None
                else:
                    p_id = u.planet[0].id
                data = {'status': 'ok', 'email':  u.email, 'name': u.name,
                        'login_days': u.login_days, 'last_login': u.last_login,
                        'planet_id': p_id, 'username': u.username, 
                        'chat_color': u.chat_color, 'alien': u.alien,
                        'rocket': u.rocket}
            else:
                data = {'status': 'error', 'note': 'user does not exist'}
        else:
            data = {'status': 'error', 'note': 'wrong params'}
            
        resp = post(data)
        return resp
    #Update date
    if request.method == "PATCH":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is None:
                data = {'status': 'error', 'note': 'user does not exist'}
                resp = post(data)
                return resp
            elif "chat_color" in request.args:
                u.chat_color = request.args["chat_color"]
                data = {'status': 'ok'}
            elif "alien" in request.args:
                u.alien = request.args["alien"]
                data = {'status': 'ok'}
            elif "rocket" in request.args:
                u.rocket = request.args["rocket"]
                data = {'status': 'ok'}
            else:
                #No other param passed in
                current_date = datetime.utcnow()
                stored_date = u.last_login
                if (current_date.date() == stored_date.date()):
                    new_day = False
                else:
                    new_day = True
                    u.login_days += 1
                u.last_login = current_date
                data = {'status': 'ok', 'new_day': new_day, 'login_days': u.login_days}
            db.session.add(u)
            db.session.commit()
            db.session.close()
            
        resp = post(data)
        return resp

@app.route('/visitors', methods=["POST", "GET", "DELETE"])
def visitors():
    #Add visitor relationship
    if request.method == "POST":
        if "visitor_id" in request.args and "visited_id" in request.args:
            visitor = User.query.get(request.args["visitor_id"])
            visited = User.query.get(request.args["visited_id"])
            try:
                visitor.visit(visited)
                db.session.commit()
                data = {'status': 'ok'}
            except:
                db.session.rollback()
                data = {'status': 'error', 'note': "couldn't add to database"}
        else:
            data = {'status': 'error', 'note': 'wrong params'}
    
        resp = post(data)
        return resp
    #Returns each visited user_id
    if request.method == "GET":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is not None:
                try:
                    result = []
                    for v in u.visited:
                        result.append({"id": v.id})
                    data = {'status': 'ok', 'results': result}
                except:
                    data = {'status': 'error', 'note': "couldn't add to database"}
            else:
                data = {'status': 'error', 'note': "couldn't find user"}
        else:
            data = {'status': 'error', 'note': 'wrong args'}
            
        resp = post(data)
        return resp
    #Removes all relationships where the provided user was visited
    if request.method == "DELETE":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is not None:
                try:
                    visitors_list = u.visitors.all()
                    for v in visitors_list:
                        v.unvisit(u)
                        db.session.add(v)
                    db.session.add(u)
                    db.session.commit()
                    data = {'status': 'ok'}
                except:
                    db.session.rollback()
                    data = {'status': 'error', 'note': "couldn't add to database"}
                finally:
                    db.session.close()
            else:
                data = {'status': 'error', 'note': "couldn't find user"}
        else:
            data = {'status': 'error', 'note': 'wrong args'}
            
        resp = post(data)
        return resp

@app.route('/galaxies', methods=["GET", "POST"])
def galaxies():
    #Return all galaxies and their variables
    if request.method == "GET":
        result = []
        try:
            g_list = Galaxy.query.all()
            for g in g_list:
                result.append({"id": g.id, "name": g.name, "description": g.description,
                               "x": g.x, "y": g.y, "image": g.image})
            data = {'status': 'ok', 'results': result}
        except:
            data = {'status': 'error', 'note': 'database error'}
        
        resp = post(data)
        return resp
    #Create a new galaxy!
    if request.method == "POST" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_name = provided_js["name"]
        provided_description = provided_js["description"]
        provided_x = provided_js["x"]
        provided_y = provided_js["y"]
        provided_image = provided_js["image"]
        try:
            g = Galaxy(name=provided_name, x=provided_x, y=provided_y,
                       image=provided_image, description = provided_description)
            db.session.add(g)
            db.session.commit()
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'note': 'database error'}
        finally:
            db.session.close()
        
        resp = post(data)
        return resp
    
@app.route('/systems', methods=["GET", "POST"])
def systems():
    #Return all systems in the galaxy_id and their variables
    if request.method == "GET":
        if "galaxy_id" in request.args:
            result = []
            try:
                g = Galaxy.query.get(request.args["galaxy_id"])
                for s in g.systems:
                    result.append({"id": s.id, "name": s.name, "quadrant": s.quadrant,
                                   "x": s.x, "y": s.y, "image": s.image})
                data = {'status': 'ok', 'results': result}
            except:
                data = {'status': 'error', 'note': 'database error'}
        elif "system_id" in request.args:
            try:
                s = System.query.get(request.args["system_id"])
                data ={'status': 'ok', "id": s.id, "name": s.name, 
                       "quadrant": s.quadrant, "x": s.x, "y": s.y, "image": s.image}
            except:
                data = {'status': 'error', 'note': 'database error'}
        else:
            data = {'status': 'error', 'note': 'wrong params'}
                
        resp = post(data)
        return resp
    #Create a new System!
    if request.method == "POST" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_galaxy_id = provided_js["galaxy_id"]
        provided_name = provided_js["name"]
        provided_quadrant = provided_js["quadrant"]
        provided_x = provided_js["x"]
        provided_y = provided_js["y"]
        provided_image = provided_js["image"]
        
        g = Galaxy.query.get(provided_galaxy_id)
        if g != None:
            try:
                s = System(name=provided_name, x=provided_x, y=provided_y,
                           image=provided_image, quadrant = provided_quadrant,
                           galaxy=g)
                db.session.add(s)
                db.session.commit()
                data = {'status': 'ok'}
            except:
                db.session.rollback()
                data = {'status': 'error', 'note': 'database error'}
            finally:
                db.session.close()
        else:
            data = {'status': 'error', 'note': 'galaxy does not exist'}
        
        resp = post(data)
        return resp

@app.route('/planets', methods=["GET", "PATCH", "POST"])
def planets():
    #Return all planets in a system_id or a user_id's owned planet and their variables
    if request.method == "GET":
        if "system_id" in request.args:
            result = []
            try:
                s = System.query.get(request.args["system_id"])
                for p in s.planets:
                    result.append({"id": p.id, "name": p.name, "size": p.size,
                                   "order": p.order, "image": p.image,
                                   "surface": p.surface, "owner_id": p.owner_id,
                                   "system_id": p.system_id})
                data = {'status': 'ok', 'results': result}
            except:
                data = {'status': 'error', 'note': 'database error'}
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if len(u.planet.all()) == 0:
                data = {'status': 'ok', 'results': None}
            else:
                p = u.planet[0]
                data = {'status': 'ok', "id": p.id, "name": p.name, "size": p.size,
                "order": p.order, "image": p.image, "surface": p.surface, 
                "owner_id": p.owner_id, "system_id": p.system_id}
        if "planet_id" in request.args:
            try:
                p = Planet.query.get(request.args["planet_id"])
                data = {'status': 'ok', "id": p.id, "name": p.name, "size": p.size,
                                   "order": p.order, "image": p.image,
                                   "surface": p.surface, "owner_id": p.owner_id,
                                   "system_id": p.system_id}
            except:
                data = {'status': 'error', 'note': 'database error'}
        else:
            data = {'status': 'error', 'results': 'wrong params'}
                
        resp = post(data)
        return resp
    #Update planet variables
    if request.method == "PATCH" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_planet_id = provided_js["planet_id"]
        p = Planet.query.get(provided_planet_id)
        if "user_id" and "name" in provided_js:
            provided_user_id = provided_js["user_id"]
            provided_name = provided_js["name"]
    
            u = User.query.get(provided_user_id)
            
            if len(u.planet.all()) != 0:
                old_planet = u.planet[0]
                old_planet.name = None
                u.planet.remove(old_planet) 
                db.session.add(old_planet)
                
            p.name = provided_name
            u.planet.append(p)
            db.session.add(u)
            db.session.add(p)
            
        elif "surface" in provided_js:
            provided_surface = provided_js["surface"]
            p.surface = provided_surface
            db.session.add(p)
            
        elif "image" in provided_js:
           provided_image = provided_js["image"]
           p.image = provided_image
           db.session.add(p)
            
        try:
            db.session.commit()
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'results': 'database error'}
        finally:
            db.session.close()
        
        resp = post(data)
        return resp
    #Create a new Planet!
    if request.method == "POST" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_system_id = provided_js["system_id"]
        provided_order = provided_js["order"]
        provided_size = provided_js["size"]
        provided_surface = provided_js["surface"]
        provided_image = provided_js["image"]
        
        s = System.query.get(provided_system_id)
        if s != None:
            try:
                p = Planet(order=provided_order, size=provided_size, system=s,
                           image=provided_image, surface = provided_surface)
                db.session.add(p)
                db.session.commit()
                data = {'status': 'ok'}
            except:
                db.session.rollback()
                data = {'status': 'error', 'note': 'database error'}
            finally:
                db.session.close()
        else:
            data = {'status': 'error', 'note': 'system does not exist'}
        
        resp = post(data)
        return resp
    
@app.route('/catalog', methods=["GET", "POST", "PATCH"])
def catalog():
    #Return all the CatalogItems and their variables
    if request.method == "GET":
        if "catalog_id" in request.args:
            c = CatalogItem.query.get(request.args["catalog_id"])
            if c != None:
                data = {"name": c.name, "image":c.image,
                        "event_specific": c.event_specific,
                        "available": c.available, "cost1": c.cost1,
                        "cost2": c.cost2, "cost3": c.cost3}
            else:
                data = {'status': 'error', 'results': 'item DNE'}
        else:
            result = []
            try:
                catalogList = CatalogItem.query.all()
                for i in catalogList:
                    result.append({"id": i.id, "name": i.name, "image":i.image,
                                   "event_specific": i.event_specific,
                                   "available": i.available, "cost1": i.cost1,
                                   "cost2": i.cost2, "cost3": i.cost3})
                data = {'status': 'ok', 'results': result}
            except:
                data = {'status': 'error', 'results': 'database error'}
                
        resp = post(data)
        return resp
    #Adds a CatalogItem to the list
    if request.method == "POST" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_name = provided_js["name"]
        provided_image = provided_js["image"]
        provided_event_specific = provided_js["event_specific"]
        provided_available = provided_js["available"]
        provided_cost1 = provided_js["cost1"]
        provided_cost2 = provided_js["cost2"]
        provided_cost3 = provided_js["cost3"]
        
        try:
            c = CatalogItem(name=provided_name, image=provided_image,
                            event_specific=provided_event_specific,
                            available=provided_available, cost1=provided_cost1,
                            cost2=provided_cost2, cost3=provided_cost3)
            db.session.add(c)
            db.session.commit()
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'results': 'database error'}
        finally:
            db.session.close()
                
        resp = post(data)
        return resp
    #Updates a CatalogItem to flip the available variable's value
    if request.method == "PATCH":
        c = CatalogItem.query.get(request.args["catalog_id"])
        try:
            c.available = not c.available
            db.session.add(c)
            db.session.commit()
            data = {'status': 'ok'}
        except:
            data = {'status': 'error', 'results': 'database error'}
                
        resp = post(data)
        return resp

@app.route('/items', methods=["GET", "POST", "PATCH", "DELETE"])
def items():
    #Return all of a user's PlanetItems and their variables
    if request.method == "GET":
        if "user_id" in request.args:
            result = []
            try:
                u = User.query.get(request.args["user_id"])
                for i in u.planet_items:
                    c = i.catalog_parent_id
                    result.append({"id": i.id, "catalog_parent_id": c,
                                   "x": i.x, "y": i.y,
                                   "image": CatalogItem.query.get(c).image})
                data = {'status': 'ok', 'results': result}
            except:
                data = {'status': 'error', 'results': 'database error'}
        else:
            data = {'status': 'error', 'results': 'wrong params'}
                
        resp = post(data)
        return resp
    #Add a PlanetItem to a player's PlanetItemList
    if request.method == "POST" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_user_id = provided_js["user_id"]
        provided_catalog_id = provided_js["catalog_id"]
        provided_x = provided_js["x"]
        provided_y = provided_js["y"]
        
        try:
            u = User.query.get(provided_user_id)
            c = CatalogItem.query.get(provided_catalog_id)
            p = PlanetItem(owner=u, catalog_parent=c, x=provided_x, y=provided_y)
            db.session.add(p)
            db.session.commit()
            data = {'status': 'ok', 'id': p.id, 'image': c.image}
        except:
            db.session.rollback()
            data = {'status': 'error', 'results': 'database error'}
        finally:
            db.session.close()
                
        resp = post(data)
        return resp
    #Removes an item from the database
    if request.method == "DELETE":
        if "item_id" in request.args:
            try:
                i = PlanetItem.query.get(request.args["item_id"])
                db.session.delete(i)
                db.session.commit()
                data = {'status': 'ok'}
            except:
                data = {'status': 'error', 'results': 'database error'}
        else:
            data = {'status': 'error', 'results': 'wrong params'}
            
        resp = post(data)
        return resp
    #Updates the given item_id with x and y
    if request.method == "PATCH" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_item_id = provided_js["item_id"]
        provided_x = provided_js["x"]
        provided_y = provided_js["y"]
        
        try:
            p = PlanetItem.query.get(provided_item_id)
            p.x = provided_x
            p.y = provided_y
            db.session.add(p)
            db.session.commit()
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'results': 'database error'}
        finally:
            db.session.close()
            
        resp = post(data)
        return resp

@app.route('/chatitems', methods=["GET", "POST", "PATCH"])
def chat_items():
    #Return all of a user's ChatItems and their variables
    if request.method == "GET":
        result = []
        if "user_id" in request.args:
            if "item_type" in request.args:
                try:
                    u = User.query.get(request.args["user_id"])
                    for i in u.chat_items:
                        if str(i.itemType) == request.args["item_type"]:
                            result.append({"id": i.id, "string": i.string,
                                           "cost1": i.cost1, "cost2": i.cost2,
                                           "cost3": i.cost3})
                    data = {'status': 'ok', 'results': result}
                except:
                    data = {'status': 'error', 'results': 'database error'}
            else:
                try:
                    u = User.query.get(request.args["user_id"])
                    for i in ChatItem.query.all():
                        result.append({"id": i.id, "string": i.string,
                                    "cost1": i.cost1, "cost2": i.cost2,
                                    "cost3": i.cost3, "item_type": i.itemType,
                                    "owned": i in u.chat_items})
                    data = {'status': 'ok', 'results': result}
                except:
                    data = {'status': 'error', 'results': 'database error'}
        else:
            for i in ChatItem.query.all():
                result.append({"id": i.id, "string": i.string, "item_type": i.itemType,
                               "cost1": i.cost1, "cost2": i.cost2,
                               "cost3": i.cost3})
            data = {'status': 'ok', 'results': result}
                
        resp = post(data)
        return resp
    #Creates a ChatItem
    if request.method == "POST" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_item_type = provided_js["item_type"]
        provided_string = provided_js["string"]
        provided_cost1 = provided_js["cost1"]
        provided_cost2 = provided_js["cost2"]
        provided_cost3 = provided_js["cost3"]
        
        
        try:
            c = ChatItem(itemType = provided_item_type, string = provided_string,
                         cost1 = provided_cost1, cost2 = provided_cost2,
                         cost3 = provided_cost3)
            db.session.add(c)
            db.session.commit()
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'results': 'database error'}
        finally:
            db.session.close()
                
        resp = post(data)
        return resp
    #Add a ChatItem to a player's ChatItemList
    if request.method == "PATCH" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_user_id = provided_js["user_id"]
        provided_chat_item_id = provided_js["chat_item_id"]
        
        try:
            u = User.query.get(provided_user_id)
            c = ChatItem.query.get(provided_chat_item_id)
            u.chat_items.append(c);
            db.session.add(u)
            db.session.add(c)
            db.session.commit()
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'results': 'database error'}
        finally:
            db.session.close()
                
        resp = post(data)
        return resp

@app.route('/currency', methods=["GET", "PATCH"])
def currency():
    #Return currency information from id
    if request.method == "GET":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is not None:
                try:
                    data = {'status': 'ok', 'cur1': u.cur1, 'cur2': u.cur2,
                            'cur3': u.cur3, 'vou2': u.vou2, 'vou3': u.vou3,
                            'lifetime_cur1': u.lifetime_cur1,
                            'lifetime_cur2': u.lifetime_cur2,
                            'lifetime_cur3': u.lifetime_cur3}
                except:
                    data = {'status': 'error', 'results': 'database error'}
            else:
                data = {'status': 'error', 'note': 'user does not exist'}
        else:
            data = {'status': 'error', 'note': 'wrong params'}
            
        resp = post(data)
        return resp
    #Updating currency
    if request.method == "PATCH":
        if request.headers['Content-Type'] == 'application/json':
            provided_js = request.json;
            provided_user_id = provided_js["user_id"]
            provided_cur1 = provided_js["cur1"]
            provided_cur2 = provided_js["cur2"]
            provided_cur3 = provided_js["cur3"]
            provided_vou2 = provided_js["vou2"]
            provided_vou3 = provided_js["vou3"]
            
            if "update_lifetime" in provided_js:
                provided_update = provided_js["update_lifetime"]
            else:
                provided_update = True
            
            u = User.query.get(provided_user_id)
            print(u)
            if u != None:
                u.cur1 += provided_cur1
                u.cur2 += provided_cur2
                u.cur3 += provided_cur3
                u.vou2 += provided_vou2
                u.vou3 += provided_vou3
                if (provided_cur1 > 0 and provided_update):
                    u.lifetime_cur1 += provided_cur1
                if (provided_cur2 > 0 and provided_update):
                    u.lifetime_cur2 += provided_cur2
                if (provided_cur3 > 0 and provided_update):
                    u.lifetime_cur3 += provided_cur3
                    
                db.session.add(u)
                try:
                    db.session.commit()
                    data = {'status': 'ok'}
                except:
                    db.session.rollback()
                    data = {'status': 'error', 'note': 'database error'}
                finally:
                    db.session.close()
        else:
            data = {'status': 'error', 'note': "user doesn't exist"}
        
        resp = post(data)
        return resp

@app.route('/missions', methods=["GET", "POST", "PATCH"])
def missions():
    #Return currency information from id
    if request.method == "GET":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is not None:
                try:
                    data = {'status': 'ok', 'mission_type': u.mission_type,
                            'mission_current': u.mission_current,
                            'mission_total': u.mission_total}
                except:
                    data = {'status': 'error', 'results': 'database error'}
            else:
                data = {'status': 'error', 'note': 'user does not exist'}
        else:
            data = {'status': 'error', 'note': 'wrong params'}
            
        resp = post(data)
        return resp
    #Add one to mission_current
    if request.method == "POST":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is not None:
                try:
                    u.mission_current += 1
                    db.session.add(u)
                    db.session.commit()
                    data = {'status': 'ok'}
                except:
                    data = {'status': 'error', 'results': 'database error'}
            else:
                data = {'status': 'error', 'note': 'user does not exist'}
        else:
            data = {'status': 'error', 'note': 'wrong params'}
            
        resp = post(data)
        return resp
    #Updating currency
    if request.method == "PATCH":
        if "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if u is not None:
                u.mission_current = -1
                u.mission_total = -1
                db.session.add(u)
                try:
                    db.session.commit()
                    timer = threading.Timer(mission_time, new_mission, (u.id,))
                    timer.start()
                    data = {'status': 'ok'}
                except:
                    db.session.rollback()
                    data = {'status': 'error', 'note': 'database error'}
                finally:
                    db.session.close()
            else:
                data = {'status': 'error', 'note': "user doesn't exist"}
        else:
            data = {'status': 'error', 'note': "wrong params"}
        
        resp = post(data)
        return resp

@app.route('/files', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        file = request.files['file']
        # check user selected a file
        if file.filename == '':
            data = {'status': 'error', 'note': "no selected file"}
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            #Make the path and create a file!
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
                
            open("/uploads/" + filename, "w+")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            data = {'status': 'ok', \
                    'url': url_for('uploaded_file', filename=filename)}
        else:
            data = {'status': 'error', 'note': 'file not allowed'}
            
        resp = post(data)
        return resp

@app.route('/status', methods=["GET", "PATCH"])
def status_table():
    #Return the status table's variables
    status = Status.query.get(1)
    if request.method == "GET":
        try:
            data = {'status': 'ok', 'event': status.event, 'news': status.news}
        except:
            data = {'status': 'error', 'note': 'database error'}
        
        resp = post(data)
        return resp
    #Updates the status table with passed-in values
    if request.method == "PATCH" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json
        
        try:
            provided_event = provided_js["event"]
        except:
            provided_event = None
        try:
            provided_news = provided_js["news"]
        except:
            provided_news = None
            
        status = Status.query.get(1)
        try:
            if provided_event is not None:
                status.event = provided_event
            if provided_news is not None:
                status.news = provided_news
            db.session.add(status)
            db.session.commit()
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'note': 'database error'}
        finally:
            db.session.close()
        
        resp = post(data)
        return resp

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Galaxy': Galaxy, 'System': System,
            'Planet': Planet, 'CatalogItem': CatalogItem, 'PlanetItem': PlanetItem,
            'ChatItem': ChatItem, 'Status': Status}