# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 19:58:03 2018

@author: gmfk07
"""
from datetime import datetime
from server import db

visitors = db.Table('visitors',
    db.Column('visitor_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('visited_id', db.Integer, db.ForeignKey('user.id'))
)

chatStore = db.Table('chat_store',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('chat_item_id', db.Integer, db.ForeignKey('chat_item.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    authenticated = db.Column(db.Boolean)
    name = db.Column(db.String(64))
    login_days = db.Column(db.Integer, default=1)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    chat_color = db.Column(db.String(16), default="black")
    alien = db.Column(db.String(128))
    rocket = db.Column(db.String(128))
    bio = db.Column(db.String(256))
    
    planet_desc = db.Column(db.String(256))
    theme = db.Column(db.String(128))
    
    mission_type = db.Column(db.String(16), default="visit")
    mission_current = db.Column(db.Integer, default=0)
    mission_total = db.Column(db.Integer, default=10)
    
    cur1 = db.Column(db.Integer, default=0)
    cur2 = db.Column(db.Integer, default=0)
    cur3 = db.Column(db.Integer, default=0)
    vou2 = db.Column(db.Integer, default=0)
    vou3 = db.Column(db.Integer, default=0)
    lifetime_cur1 = db.Column(db.Integer, default=0)
    lifetime_cur2 = db.Column(db.Integer, default=0)
    lifetime_cur3 = db.Column(db.Integer, default=0)
    
    planet = db.relationship('Planet', backref='owner', lazy='dynamic')
    planet_items = db.relationship('PlanetItem', backref='owner', lazy='dynamic')
    projects = db.relationship('Project', backref='owner', lazy='dynamic')
    aliens = db.relationship('Alien', backref='owner', lazy='dynamic')
    
    chat_items = db.relationship(
        'ChatItem', secondary=chatStore, backref=db.backref('owners', lazy='joined'), lazy='joined')
    
    visited = db.relationship(
        'User', secondary=visitors,
        primaryjoin=(visitors.c.visitor_id == id),
        secondaryjoin=(visitors.c.visited_id == id),
        backref=db.backref('visitors', lazy='dynamic'), lazy='dynamic')
    
    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the id to satisfy Flask-Login's requirements."""
        return self.id

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False
    
    def visit(self, user):
        if not self.has_visited(user):
            self.visited.append(user)

    def unvisit(self, user):
        if self.has_visited(user):
            self.visited.remove(user)

    def has_visited(self, user):
        return self.visited.filter(
            visitors.c.visitor_id == user.id).count() > 0

    def __repr__(self):
        return '<User {}>'.format(self.username)    

class Galaxy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(128))
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    image = db.Column(db.String(128))

    systems = db.relationship('System', backref='galaxy', lazy='dynamic')

    def __repr__(self):
        return '<Galaxy {}>'.format(self.name)
    
class System(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxy.id'))
    name = db.Column(db.String(64), index=True, unique=True)
    quadrant = db.Column(db.Integer)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    image = db.Column(db.String(128))

    planets = db.relationship('Planet', backref='system', lazy='dynamic')

    def __repr__(self):
        return '<System {}>'.format(self.name)
    
class Planet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    system_id = db.Column(db.Integer, db.ForeignKey('system.id'))
    name = db.Column(db.String(64))
    order = db.Column(db.Integer)
    size = db.Column(db.Integer)
    image = db.Column(db.String(128))
    surface = db.Column(db.String(128))

    def __repr__(self):
        return '<Planet {}>'.format(self.name)
    
class CatalogItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    image = db.Column(db.String(128))
    event_specific = db.Column(db.Boolean)
    available = db.Column(db.Boolean)
    is_rocket = db.Column(db.Boolean)
    
    cost1 = db.Column(db.Integer)
    cost2 = db.Column(db.Integer)
    cost3 = db.Column(db.Integer)
    
    planet_items = db.relationship('PlanetItem', backref='catalog_parent', lazy='dynamic')
    
    def __repr__(self):
        return '<CatalogItem {}>'.format(self.name)
    
class ChatItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itemType = db.Column(db.Integer)
    string = db.Column(db.String(16), index=True, unique=True)
    
    cost1 = db.Column(db.Integer)
    cost2 = db.Column(db.Integer)
    cost3 = db.Column(db.Integer)
    
    def __repr__(self):
        return '<ChatItem {}>'.format(self.id)
    
class PlanetItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    catalog_parent_id = db.Column(db.Integer, db.ForeignKey('catalog_item.id'))
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    
    def __repr__(self):
        return '<PlanetItem {}>'.format(self.id)
    
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(32))
    desc = db.Column(db.String(128))
    file = db.Column(db.String(128))
    
    def __repr__(self):
        return '<Project {}>'.format(self.id)
    
class AlienSpecies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    image = db.Column(db.String(128))
    event_specific = db.Column(db.Boolean)
    available = db.Column(db.Boolean)
    
    cost1 = db.Column(db.Integer)
    cost2 = db.Column(db.Integer)
    cost3 = db.Column(db.Integer)
    
    aliens = db.relationship('Alien', backref='species', lazy='dynamic')
    
    def __repr__(self):
        return '<AlienSpecies {}>'.format(self.name)
    
class Alien(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    species_id = db.Column(db.Integer, db.ForeignKey('alien_species.id'))
    name = db.Column(db.String(64), index=True, unique=True)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    
    def __repr__(self):
        return '<Alien {}>'.format(self.name)
    
class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Boolean)
    news = db.Column(db.String(256))
    
    def __repr__(self):
        return '<Status {}>'.format(self.id)