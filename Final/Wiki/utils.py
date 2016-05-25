import os
import re
import random
import hashlib
import hmac
import logging
import string

from google.appengine.ext import db

import webapp2 # WSGI app library
import jinja2 # jinja2 template library

import wiki

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = "secretive"

#pw secret hashing
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(10))

def make_pw_hash(name, pw, salt = None):
    if salt is None:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)

def valid_hash(name, pw, h):
    if not h:
        return False
    salt = h.split('|')[1]
    return h == make_pw_hash(name, pw, salt)

def make_secure_val(val):
    return '%s|%s' % (hmac.new(secret, val).hexdigest(), val)

def check_secure_val(secure_val):
    val = secure_val.split('|')[1]
    if secure_val == make_secure_val(val):
        return val

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

def pages_key(group = 'default'):
    return db.Key.from_path('pages',group)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['logged_in'] = self.user # get the user
        params['page'] = self.request.query_string
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
             'Set-Cookie',
             '%s=%s; Path=/' % (name, cookie_val))
    
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)
    
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))
    
    def logout(self):
        self.response.delete_cookie('user_id')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid)) # define the user

    """Clones an entity, adding or overriding constructor attributes.
    
    The cloned entity will have exactly the same property values as the original
    entity, except where overridden. By default it will have no parent entity or
    key name, unless supplied.
    
    Args:
    e: The entity to clone
    extra_args: Keyword arguments to override from the cloned entity and pass
    to the constructor.
    Returns:
    A cloned, possibly modified, copy of entity e.
    """
    def clone_entity(e, **extra_args):
        klass = e.__class__
        props = dict((v._code_name, v.__get__(e, klass)) for v in klass._properties.itervalues() if type(v) is not ndb.ComputedProperty)
        props.update(extra_args)
        return klass(**props)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)
    
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())
    
    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u
    
    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)
    
    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_hash(name, pw, u.pw_hash):
            return u

class Page(db.Model):
    url = db.StringProperty(required = True)
    html = db.TextProperty(required = False)
    created = db.DateTimeProperty(auto_now_add = True)

    @classmethod
    def by_url(cls, url): # altered this to always order by oldest to newest
        p = Page.all().filter('url =', url).order('-created')
        return p

    @classmethod
    def add(cls, url, html):
        return Page(parent=pages_key(),
                    url=url,
                    html=html)

    @classmethod
    def edit(cls, url, html):
        p = cls.by_url(url)

