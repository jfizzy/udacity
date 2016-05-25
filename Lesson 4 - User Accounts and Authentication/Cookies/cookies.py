import os
import jinja2 #template libraries
import webapp2 #WSGI webapp2 libraries
import hashlib #hash function libraries
import hmac # library for
import random #library for creating (pseudo?) random numbers
import string #library with useful string funcs

SECRET = 'imsosecret'

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    hspl = h.split('|')
    if make_secure_val(hspl[0]) == h:
        return hspl[0]

def make_salt(): # this function creates a random 5 letter string (better encryption)
    return ''.join(random.choice(string.letters) for x in xrange(5))

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = 0
        visit_cookie_str = self.request.cookies.get('visits')
        #convenience of app engine!
        #cookies are stored as text (strings) is text so we must cast them
        if visit_cookie_str:
            cookie_val = check_secure_val(visit_cookie_str)
            if cookie_val:
                visits = int(cookie_val)
    
        visits += 1
        
        new_cookie_val = make_secure_val(str(visits))
    
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % new_cookie_val)

        if visits > 100000:
            self.write("You are the best ever!")
        else:
            self.write("You've been here %s times!" % visits)


app = webapp2.WSGIApplication([
                               ('/', MainPage)
                               ], debug=True)