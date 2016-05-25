import os
import jinja2
import webapp2
import re
import hashlib
import random
import string
import datetime

from google.appengine.ext import db # required for use of entities

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True)
# this makes security holes much less likely

user_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
pass_re = re.compile(r"^.{3,20}$")
mail_re = re.compile(r"^[\S]+@[\S]+.[\S]+$")

global curr_user
curr_user = None

#validity checking functions
def valid_user(user):
    return user_re.match(user)

def valid_pw(pw):
    return pass_re.match(pw)

def valid_mail(mail):
    return mail_re.match(mail)

#pw salt hashing
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
    

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class SignupPage(Handler):
    def write_form(self, username="", user_error="", exist_error="", password="", pass_error="", verify="", veri_error="", email="", mail_error=""):
        self.render("signup.html", curr_user=curr_user, title="User Signup", username=username,
                    password=password,
                    verify=verify,
                    email=email,
                    user_error=user_error,
                    pass_error=pass_error,
                    veri_error=veri_error,
                    mail_error=mail_error,
                    exist_error=exist_error
                    )
    def get(self):
        self.write_form()
    
    def post(self):
        
        usr_err = "That's not a valid username"
        pwd_err = "That's not a valid password"
        veri_err = "The passwords don't match"
        mail_err = "That's an invalid email address"
        
        exist_err = "That user already exists"
        
        usr = self.request.get('username')
        pw = self.request.get('password')
        vrfy = self.request.get('verify')
        mail = self.request.get('email')
        
        v_user = valid_user(usr)
        v_pw = valid_pw(pw)
        v_veri = ''
        if(v_pw):
            v_veri = (pw == vrfy)
        v_mail = valid_mail(mail)
        
        #check for errors in user form input
        errors = self.decide_errors(v_user,v_pw,v_veri,v_mail,mail)
        
        if(errors == 0):
            #check if the user already exists
            h = self.request.cookies.get('userhash')
            if h:
                salt = h.split('|')[1]
            else:
                salt = None
            users = db.GqlQuery("SELECT * FROM User ORDER BY username")
            for user in users:
                if usr == user.username:
                    self.write_form(usr,'',exist_err,'','','','',mail,'')
                    return
            
            h = make_pw_hash(usr, pw, salt) # hash the user token
            #create cookie with hashed user token here
            self.response.set_cookie('userhash', h)
            u = User(username=usr,password=pw,hash=h,email=mail)
            u.put()
            global curr_user
            curr_user = user
            key = u.key()
            record = User.get(key)
            self.redirect('/welcome')
        
        else:
            if(errors >= 8): #username error
                errors -= 8
                if(errors >= 4): #password error
                    errors -= 4
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,usr_err,'','',pwd_err,'','',mail,mail_err)
                        else: #username, password and verify errors
                            self.write_form(usr,usr_err,'','',pwd_err,'','',mail,'')
                    else: #passwords match
                        if(errors == 1): #username, password, email errors
                            self.write_form(usr,usr_err,'','',pwd_err,'','',mail,mail_err)
                        else: #username, password errors
                            self.write_form(usr,usr_err,'','',pwd_err,'','',mail,'')
                else: #password is valid
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,usr_err,'','','','',veri_err,mail,mail_err)
                        else: #username, password and verify errors
                            self.write_form(usr,usr_err,'','','','',veri_err,mail,'')
                    else: #passwords match
                        if(errors == 1): #username, password, email errors
                            self.write_form(usr,usr_err,'','','','','',mail,mail_err)
                        else: #username, password errors
                            self.write_form(usr,usr_err,'','','','','',mail,'')
            else: #username is valid
                if(errors >= 4): #password error
                    errors -= 4
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,'','','',pwd_err,'','',mail,mail_err)
                        else: #password and verify errors
                            self.write_form(usr,'','','',pwd_err,'','',mail,'')
                    else: #passwords match
                        if(errors == 1): #username, password, email errors
                            self.write_form(usr,'','','',pwd_err,'','',mail,mail_err)
                        else: #password errors
                            self.write_form(usr,'','','',pwd_err,'','',mail,'')
                else: #password is valid
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,'','','','','',veri_err,mail,mail_err)
                        else: #verify errors
                            self.write_form(usr,'','','','','',veri_err,mail,'')
                    else: #passwords match
                        if(errors == 1): #email errors
                            self.write_form(usr,'','','','','','',mail,mail_err)
                        else: #no errors (should have already redirected
                            self.write_form(usr,'','','','','','',mail,'')




    def decide_errors(self,v_user,v_pw,v_veri,v_mail,mail):
        returnval = 0;
        if(v_user): #valid username
            if(v_pw): #valid pw
                if(v_veri): #passwords match
                    if(v_mail or (mail == '')): #valid email or no email
                        pass #all good
                    else: #email error
                        returnval += 1
                else: #passwords don't match
                    returnval += 2
                    if(v_mail or (mail == '')): #valid email or no email
                        pass
                    else: #email error
                        returnval += 1
            else: #password error
                returnval += 4
                if(v_veri): #passwords match
                    if(v_mail or (mail == '')): #valid email or no email
                        pass
                    else: #email error
                        returnval += 1
                else: #passwords don't match
                    returnval += 2
                    if(v_mail or (mail == '')): #valid email or no email
                        pass
                    else: #email error
                        returnval += 1
        else: #username error
            returnval +=8
            if(v_pw): #valid pw
                if(v_veri): #passwords match
                    if(v_mail or (mail == '')): #valid email or no email
                        pass
                    else: #email error
                        returnval += 1
                else: #passwords don't match
                    returnval += 2
                    if(v_mail or (mail == '')): #valid email or no email
                        pass
                    else: #email error
                        returnval += 1
            else: #password error
                returnval += 4
                if(v_veri): #passwords match
                    if(v_mail or (mail == '')): #valid email or no email
                        pass
                    else: #email error
                        returnval += 1
                else: #passwords don't match
                    returnval += 2
                    if(v_mail or (mail == '')): #valid email or no email
                        pass
                    else: #email error
                        returnval += 1
        return returnval

class LandingPage(Handler):
    def write_form(self, username=""):
        self.render("welcome.html", curr_user=curr_user, title="Welcome, %s!" % username)
    
    def get(self):
        h = self.request.cookies.get('userhash')
        users = db.GqlQuery("SELECT * FROM User WHERE hash = :1", h)
        user = users.get()
        if not valid_hash(user.username,user.password,h):
            self.redirect('/signup')
        else:
            self.write_form(user.username)

class LoginPage(Handler):
    def write_form(self, username="", user_error="", exist_error="", password="", pass_error=""):
        self.render("login.html", curr_user=curr_user, title="User Login", username=username,
                    password=password,
                    user_error=user_error,
                    pass_error=pass_error,
                    exist_error=exist_error
                    )

    def get(self):
        self.write_form()

    def post(self):

        usr_err = "That's not a valid username"
        pwd_err = "That's not a valid password"
        exist_err = "That user does not exist"

        usr = self.request.get('username')
        pw = self.request.get('password')

        v_user = valid_user(usr)
        v_pw = valid_pw(pw)

        if not v_user:
            self.write_form(usr,'',usr_err,'','')
        else:
            if not v_pw:
                self.write_form(usr,'','','',pwd_err)
            else:
                users = db.GqlQuery("SELECT * FROM User ORDER BY username")
                for user in users:
                    if (user.username == usr) and (user.password == pw):
                        #we have a match, log user in
                        global curr_user
                        curr_user = user
                        self.response.set_cookie('userhash', user.hash)
                        self.redirect('/welcome')
                        
                self.write_form(usr,'','','',exist_err)

class LogoutPage(Handler):
    def get(self):
        global curr_user
        curr_user = None
        self.response.delete_cookie("userhash")
        self.redirect('/signup')

class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True) # SHOULD NOT STORE PW IN DATABASE
    hash = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

class Post(db.Model):
    title = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)

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
            self.redirect("/%s" % p.key().id()) #redirect to the id permalink
        else:
            error = "We need both a subject and some content!"
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
    ('/signup', SignupPage),
    ('/welcome', LandingPage),
    ('/login', LoginPage),
    ('/logout', LogoutPage),
    (r'/(\d+)', PermaPage)
], debug=True)
