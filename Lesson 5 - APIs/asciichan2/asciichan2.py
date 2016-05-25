import jinja2
import webapp2
import os
import re
import sys
import urllib2
from xml.dom import minidom
from string import letters
from xml.parsers.expat import ExpatError

from google.appengine.ext import db # required for use of entities

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
def gmaps_img(points):
    markers = '&'.join('markers=%s' % (p.lat, p.lon)
                       for p in points)
    return GMAPS_URL + markers

#****** does not work as hostip api is down
IP_URL = "http://api.hostip.info/?ip="

coord_check = re.compile(r"^(-{0,1}[0-9]+\.{1}[0-9]+),(-{0,1}[0-9]+\.{1}[0-9]+)$")

def get_coords(ip):
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except urllib2.URLError:
        return

    if content:
        #parse xml and find coordinates
        try:
            xmldoc = minidom.parseString(xml)
            coords = xmldoc.getElementsByTagName('gml:coordinates')[0].firstChild.nodeValue
            coords.strip()
            if not coord_check.match(coords):
                return
            lon, lat = coords.split(',')
            if lon and lat:
                return db.GeoPt(lat, lon)
        except (IOError, ExpatError) as e:
            return

class Art(db.Model): # this class represents an entity! (table)
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty(required = False)

class MainPage(Handler):
    def render_front(self, title="", art="", error=""):
        arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC LIMIT 10")
        #pay attention to syntax for GqlQuery calls
    
        #prevent the running of multiple queries
        arts = list(arts) # cursor makes this an iterable
    
        #find which arts have coords
        points = filter(None, (a.coords for a in arts))

        #if we have any arts coords, make an image url
        img_url = none
        if points:
            img_url = gmaps_img(points)
        
        #display the image url

        self.render("front.html", title=title, art=art, error=error, arts = arts, img_url = img_url)

    def get(self):
        self.write(repr(get_coords(self.request.remote_addr)))
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Art(title = title, art = art)
            #lookup the user's coordinates from their IP
            coords = get_coords(self.request.remote_addr)
            #if we have coords add them to the art
            if coords:
                p.coords = coords
            
            a.put()

            self.redirect("/")
        else:
            error = "we need both a title and some artwork!"
            self.render_front(title, art, error)



app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
