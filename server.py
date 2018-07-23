# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 19:55:26 2018

@author: gmfk07
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import Status, User, Galaxy, System, Planet, CatalogItem, PlanetItem

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

@app.route('/login', methods=["POST", "GET"])
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
                data = {'status': 'ok', 'note': u.id}
            else:
                data = {'status': 'error', 'note': 'password incorrect'}
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
                        'planet_id': p_id}
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
            if u is not None :
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
            else:
                data = {'status': 'error', 'note': 'user does not exist'}
        else:
            data = {'status': 'error', 'note': 'wrong params'}
            
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
        elif "user_id" in request.args:
            u = User.query.get(request.args["user_id"])
            if len(u.planet.all()) == 0:
                data = {'status': 'ok', 'results': None}
            else:
                p = u.planet[0]
                data = {'status': 'ok', "id": p.id, "name": p.name, "size": p.size,
                "order": p.order, "image": p.image, "surface": p.surface, 
                "owner_id": p.owner_id, "system_id": p.system_id}
        elif "planet_id" in request.args:
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
    #Sets a user's planet to a given planet_id
    if request.method == "PATCH" and request.headers['Content-Type'] == 'application/json':
        provided_js = request.json;
        provided_user_id = provided_js["user_id"]
        provided_planet_id = provided_js["planet_id"]
        provided_name = provided_js["name"]

        u = User.query.get(provided_user_id)
        p = Planet.query.get(provided_planet_id)
        if len(u.planet.all()) != 0:
            old_planet = u.planet[0]
            old_planet.name = None
            u.planet.remove(old_planet) 
            db.session.add(old_planet)
            
        p.name = provided_name
        u.planet.append(p)
        db.session.add(u)
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
    
@app.route('/catalog', methods=["GET"])
def catalog():
    #Return all the CatalogItems and their variables
    if request.method == "GET":
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

@app.route('/items', methods=["GET", "POST", "PATCH"])
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
            data = {'status': 'ok'}
        except:
            db.session.rollback()
            data = {'status': 'error', 'results': 'database error'}
        finally:
            db.session.close()
                
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
            
            u = User.query.get(provided_user_id)
            if u != None:
                u.cur1 += provided_cur1
                u.cur2 += provided_cur2
                u.cur3 += provided_cur3
                u.vou2 += provided_vou2
                u.vou3 += provided_vou3
                if (u.cur1 > 0):
                    u.lifetime_cur1 += provided_cur1
                if (u.cur2 > 0):
                    u.lifetime_cur2 += provided_cur2
                if (u.cur3 > 0):
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

@app.route('/missions', methods=["GET", "PATCH"])
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
                    timer = threading.Timer(10.0, new_mission, (u.id,))
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
            'Status': Status}