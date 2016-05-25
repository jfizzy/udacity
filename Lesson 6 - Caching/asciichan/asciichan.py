import jinja2
import webapp2
import os
import re
import sys
import urllib2
import random # rng
import logging # logging module
from collections import namedtuple # tuple type
from xml.dom import minidom
from string import letters
from xml.parsers.expat import ExpatError

from google.appengine.api import memcache
from google.appengine.ext import db # required for use of entities

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development')

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True)
# this makes security holes much less likely

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
def gmaps_img():
    markers = '&'.join('markers=%s,%s' % (p.lat, p.lon) for p in points)
    return GMAPS_URL + markers

#****** does not work as hostip api is down
IP_URL = "http://api.hostip.info/?ip="

coord_check = re.compile(r"^(-{0,1}[0-9]+\.{1}[0-9]+),(-{0,1}[0-9]+\.{1}[0-9]+)$")

coords = {"Calgary":("51.044270", "-114.062019"), "Edmonton":("53.5444", "-113.4909"), "Vancouver":("49.2827", "-123.1207")}

Point = namedtuple('Point', ["lat", "lon"])
points = [Point(51.044270,-114.062019),
          Point(53.5444, -113.4909),
          Point(49.2827, -123.1207),
          Point(53.903926, -122.766199)]

def get_coords(): #****** removed IP because of issues with IPv4 vs IPv6 and api down
    p = random.choice(points)
    return str(p.lat)+','+str(p.lon)

class Art(db.Model): # this class represents an entity! (table)
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty(required = False)

def top_arts(update = False):
    key = 'top'
    arts = memcache.get(key) # check the memcache
    if arts is None or update:
        logging.error("DB Query")
        arts = db.GqlQuery("SELECT * "
                           "FROM Art "
                           "ORDER BY created DESC "
                           "LIMIT 10")

        arts = list(arts)
        memcache.set(key, arts)
    return arts

class MainPage(Handler):
    def render_front(self, title="", art="", error=""):
        arts = top_arts(False)

        #if we have any arts coords, make an image url
        img_url = gmaps_img()
        
        #display the image url

        self.render("front.html", title=title, art=art, error=error, arts = arts, img_url = img_url)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Art(title = title, art = art)
            #lookup the user's coordinates from their IP
            coords = get_coords()
            #if we have coords add them to the art
            if coords:
                print coords
                a.coords = coords
            
            a.put()
            top_arts(True)
            self.redirect("/")
        else:
            error = "we need both a title and some artwork!"
            self.render_front(title, art, error)



app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
