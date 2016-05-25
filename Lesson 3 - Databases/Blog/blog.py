import os
import jinja2
import webapp2

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

class Post(db.Model): #GQL Entity class
    title = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True) # add this when created

class PermaPage(Handler):
    def get(self, product_id):
        post = Post.get_by_id(int(product_id))
        self.render("post.html", title="Post %s" % product_id,
                    post=post)

class NewPostPage(Handler):
    def render_new(self, ptitle="", pbody="", error=""):
        self.render("newpost.html", title="New Blog Post",
                    ptitle=ptitle, pbody=pbody, error=error)

    def get(self):
        self.render_new()

    def post(self):
        title = self.request.get('subject')
        body = self.request.get('content') #pull the user entered variables

        if title and body:
            p = Post(title = title, body = body) # create 'Post' object
            p.put() #add object to the DB
            self.redirect("/%s" % p.key().id()) #***change this to redirect to permalinks
        else:
            error = "We need both a title and some body!"
            self.render_new(title, body, error) # re-render page with error

class MainPage(Handler):
    def render_front(self, ptitle="", pbody="", created="", posts=""):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
        self.render("front.html", title="Blog", subject=ptitle, content=pbody, created=created, posts=posts)

    def get(self):
        self.render_front()

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newpost', NewPostPage),
    (r'/(\d+)', PermaPage)
], debug=True)
