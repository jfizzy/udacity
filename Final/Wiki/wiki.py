import os
import re # regular expression library
import random
import hashlib
import hmac
import logging
import string
import urllib
import urllib2

import webapp2 # WSGI app library
import jinja2 # jinja2 template library

from utils import Handler # adds access to the utils from this file
from utils import User # adds access to the User model from this file
from utils import Page # adds access to the Page model from this file
import utils

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development')

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)' # RE for the arbitrary pages
user_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$") # RE for usernames
pass_re = re.compile(r"^.{3,20}$") # RE for passwords
mail_re = re.compile(r"^[\S]+@[\S]+.[\S]+$") # RE for emails

#Class: WikiFrontPage - front page of the wiki
class WikiFrontPage(Handler):
    def get(self):
        url = self.request.url
        par = None
        if '?v=' in url:
            par = url.rsplit('?',1)[1]
        if not par == None:
            page = Page.by_url('/').fetch(40)[int(par.rsplit('=',1)[1])-1] # gets the selected version
        else:
            page = Page.by_url('/').get()
         
        if page == None: # we have some edited data
            self.render('wikifront.html', html = "<h1><b>Welcome to the Wiki!</b></h1>", page_query='/')
        else:
            self.render('wikifront.html', html=page.html, page_query='/')

#Class: WikiSignupPage - user signup page of the wiki
class WikiSignupPage(Handler):
    def get(self):
        self.render("wikisignup.html", title='Wiki Signup', page_query='/signup')
    
    def post(self):
        have_error = False
        usr = self.request.get('username')
        pwd = self.request.get('password')
        vfy = self.request.get('verify')
        eml = self.request.get('email')
        
        v_user = valid_user(usr)
        v_pass = valid_pw(pwd)
        v_mail = valid_mail(eml)
        
        params = dict(username = usr,
                      email = eml)
                      
        params['title'] = 'Wiki Signup'
            
        if not v_user:
            params['user_error'] = "That's not a valid username"
            have_error = True
                      
        if not v_pass:
            params['pass_error'] = "That wasn't a valid password"
            have_error = True
        elif pwd != vfy:
            params['veri_error'] = "Your passwords didn't match"
            have_error = True
                                                  
        if eml and not v_mail:
            params['mail_error'] = "That's not a valid email"
            have_error = True
    
        if have_error:
            self.render('wikisignup.html', page_query='/signup', **params)
        else:
            #make sure the user doesn't already exist
            u = User.by_name(usr)
            if u:
                msg = 'That user already exists'
                self.render('wikisignup.html', exist_error = msg, title='Wiki Signup', page_query='/signup')
            else:
                u = User.register(usr, pwd, eml)
                u.put()
                self.login(u)
                self.redirect('/')

#validity checking functions
def valid_user(user):
    return user_re.match(user)

def valid_pw(pw):
    return pass_re.match(pw)
    
def valid_mail(mail):
    return mail_re.match(mail)

#Class: WikiLoginPage - user login page of the wiki
class WikiLoginPage(Handler):
    def get(self):
        self.render('wikilogin.html', title="Wiki Login", page_query='/login')
    
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        
        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/')
        else:
            msg = 'Invalid Login'
            self.render('wikilogin.html', exist_error = msg, title="Wiki Login", page_query='/login')

#Class: WikiLogoutPage - user logout page of the wiki
class WikiLogoutPage(Handler):
    def get(self):
        self.logout() # clears the cookie
        self.redirect('/')

#Class: WikiEditPage - arbitrary editing page of the wiki
class WikiEditPage(Handler):
    def get(self, event):
        url = self.request.url
        par = None
        query = url.rsplit('/',1)[1]
        if '?v=' in url:
            par = url.rsplit('?',1)[1]
            query = query.split('?',1)[0]
        query = '/'+query #append the / to the front
        html = ""
        if par:
            page = Page.by_url(query).fetch(40)[int(par.rsplit('=',1)[1])-1] # gets the selected version
        else:
            page = Page.by_url(query).get()
         
        if page:
            html = page.html
            key = page.key() # this is some db based ops to force it to properly update
            Page.get(key)
        elif query == '/':
            html = "<h1><b>Welcome to the Wiki!</b></h1>"
        self.render('wikipage.html', editing=True, page_query = query, html = html)

    def post(self, event):
        url = self.request.url
        par = None
        query = url.rsplit('/',1)[1]
        if '?v=' in url:
            par = url.rsplit('?',1)[1]
            query = query.split('?',1)[0]
        query = '/'+query #append the / to the front
        print query
        html = self.request.get('html')
        
        p = Page.add(query, html)
        p.put()
        key = p.key() # this is some db based ops to force it to properly update
        Page.get(key)
        self.redirect(query)
#Class: WikiHistoryPage - page containing previous versions of this page
class WikiHistoryPage(Handler):
    def get(self, event):
        url = self.request.url
        query = url.rsplit('/',1)[1]
        query = query.split('?',1)[0]
        query = '/'+query #append the / to the front

        pages = Page.by_url(query).fetch(40)
        if pages:
            self.render('wikihistory.html', title="Wiki History", page_query=query, pages = pages)
        else:
            self.render('wikihistory.html', title="Wiki History", page_query=query, pages=None)

#Class: WikiPage - arbitrary page of the wiki
class WikiPage(Handler):
    def get(self, event):
        url = self.request.url
        par = None
        query = url.rsplit('/',1)[1]
        if '?v=' in url:
            par = url.rsplit('?',1)[1]
            query = query.split('?',1)[0]
        query = '/'+query #append the / to the front
        #check if the page already exists
        if par:
            page = Page.by_url(query).fetch(40)[int(par.rsplit('=',1)[1])-1] # gets the selected version
        else:
            page = Page.by_url(query).get()
         
        if page: #page exists
            html = page.html
            self.render('wikipage.html', editing=False, html=html, page_query=query)
        else: #new page
            if self.user:
                self.redirect('/_edit' + query)
            else:
                self.redirect('/login')

#Class: WikiInvalid - Handler to redirect from invalid pages
class WikiInvalid(Handler):
    def get(self):
        logging.error("Invalid Edit Page")
        self.redirect('/')

app = webapp2.WSGIApplication([
                               ('/', WikiFrontPage),
                               ('/signup', WikiSignupPage),
                               ('/login', WikiLoginPage),
                               ('/logout', WikiLogoutPage),
                               ('/_edit', WikiInvalid),
                               ('/_edit/signup', WikiInvalid),
                               ('/_edit/login', WikiInvalid),
                               ('/_edit/logout', WikiInvalid),
                               ('/_edit' + PAGE_RE, WikiEditPage),
                               ('/_history', WikiInvalid),
                               ('/_history/signup', WikiInvalid),
                               ('/_history/login', WikiInvalid),
                               ('/_history/logout', WikiInvalid),
                               ('/_history' + PAGE_RE, WikiHistoryPage),
                               (PAGE_RE, WikiPage)
], debug=True)
