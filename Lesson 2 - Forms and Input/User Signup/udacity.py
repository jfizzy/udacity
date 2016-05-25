import webapp2

form="""
<form method="post">
    <b>Signup</b>
    <br>
    <br>
    <table><tbody>
        <tr>
            <td class="label">Username </td>
            <td><input type="text" name="username" value="%(username)s"></label></td>
            <td class="div" style="color: red">%(user_error)s</td>
        </tr>
        <tr>
            <td class="label">Password </td>
            <td><input type="password" name="password" value="%(password)s"></label></td>
            <td class="div" style="color: red">%(pass_error)s</td>
        </tr>
        <tr>
            <td class="label">Verify Password </td>
            <td><input type="password" name="verify" value="%(verify)s"></label></td>
            <td class="div" style="color: red">%(veri_error)s</td>
        </tr>
        <tr>
            <td class="label">Email (optional) </td>
            <td><input type="text" name="email" value="%(email)s"></label></td>
            <td class="div" style="color: red">%(mail_error)s</td>
        </tr>
    </tbody></table>
    <br>
    <br>
    <input type="submit">
</form>
"""

class MainPage(webapp2.RequestHandler):
    def write_form(self, username="", user_error="", password="", pass_error="", verify="", veri_error="", email="", mail_error=""):
        self.response.out.write(form % {"username": escape_html(username),
                                        "password": escape_html(password),
                                        "verify": escape_html(verify),
                                        "email": escape_html(email),
                                        "user_error": escape_html(user_error),
                                        "pass_error": escape_html(pass_error),
                                        "veri_error": escape_html(veri_error),
                                        "mail_error": escape_html(mail_error)
                                        })
    def get(self):
        self.write_form()

    def post(self):
        
        usr_err = "That's not a valid username"
        pwd_err = "That's not a valid password"
        veri_err = "The passwords don't match"
        mail_err = "That's an invalid email address"
        
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
            redirect_with_param = '/LandingPage?username=%s' % usr
            self.redirect(redirect_with_param) # need to find way to pass username
        
        else:
            if(errors >= 8): #username error
                errors -= 8
                if(errors >= 4): #password error
                    errors -= 4
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,usr_err,'',pwd_err,'','',mail,mail_err)
                        else: #username, password and verify errors
                            self.write_form(usr,usr_err,'',pwd_err,'','',mail,'')
                    else: #passwords match
                        if(errors == 1): #username, password, email errors
                            self.write_form(usr,usr_err,'',pwd_err,'','',mail,mail_err)
                        else: #username, password errors
                            self.write_form(usr,usr_err,'',pwd_err,'','',mail,'')
                else: #password is valid
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,usr_err,'','','',veri_err,mail,mail_err)
                        else: #username, password and verify errors
                            self.write_form(usr,usr_err,'','','',veri_err,mail,'')
                    else: #passwords match
                        if(errors == 1): #username, password, email errors
                            self.write_form(usr,usr_err,'','','','',mail,mail_err)
                        else: #username, password errors
                            self.write_form(usr,usr_err,'','','','',mail,'')
            else: #username is valid
                if(errors >= 4): #password error
                    errors -= 4
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,'','',pwd_err,'','',mail,mail_err)
                        else: #password and verify errors
                            self.write_form(usr,'','',pwd_err,'','',mail,'')
                    else: #passwords match
                        if(errors == 1): #username, password, email errors
                            self.write_form(usr,'','',pwd_err,'','',mail,mail_err)
                        else: #password errors
                            self.write_form(usr,'','',pwd_err,'','',mail,'')
                else: #password is valid
                    if(errors >=2): #password mismatch
                        errors -= 2
                        if(errors == 1): #email error
                            self.write_form(usr,'','','','',veri_err,mail,mail_err)
                        else: #verify errors
                            self.write_form(usr,'','','','',veri_err,mail,'')
                    else: #passwords match
                        if(errors == 1): #email errors
                            self.write_form(usr,'','','','','',mail,mail_err)
                        else: #no errors (should have already redirected
                            self.write_form(usr,'','','','','',mail,'')

                


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

class LandingPage(webapp2.RequestHandler):
    
    def get(self, username=""):
        self.response.out.write("""<form method="post">
                                        <br><br>
                                        <b>Welcome, %s!</b>
                                        <br><br>
                                    </form>
                                """ % self.request.get('username'))

import re
user_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
pass_re = re.compile(r"^.{3,20}$")
mail_re = re.compile(r"^[\S]+@[\S]+.[\S]+$")

def valid_user(user):
    return user_re.match(user)

def valid_pw(pw):
    return pass_re.match(pw)

def valid_mail(mail):
    return mail_re.match(mail)

app = webapp2.WSGIApplication([
    ('/', MainPage), ('/LandingPage', LandingPage)
], debug=True)

def escape_html(s):
    for(i, o) in (('&', "&amp;"),
                  ('>', "&gt;"),
                  ('<', "&lt;"),
                  ('"', "&quot;")):
        new_s = s.replace(i, o)
    return new_s

