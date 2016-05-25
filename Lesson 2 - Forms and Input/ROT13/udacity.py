import webapp2

form="""
<form method="post">
    <b>Enter Some Text to ROT13:</b>
    <br>
    <br>
    <textarea name="text" style="height: 100px; width: 400px;">%(text)s</textarea>
    <br>
    <br>
    <input type="submit">
</form>
"""

class MainPage(webapp2.RequestHandler):
    def write_form(self, text=""):
        self.response.out.write(form % {"text": escape_html(text)
                                        })
    def get(self):
        self.write_form()

    def post(self):
        usr_txt = self.request.get('text')
        rot = rot_13(usr_txt)
        self.write_form(rot)

app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)

def escape_html(s):
    for(i, o) in (('&', "&amp;"),
                  ('>', "&gt;"),
                  ('<', "&lt;"),
                  ('"', "&quot;")):
        new_s = s.replace(i, o)
    return new_s

def rot_13(orig):
    l = []
    for i, c in enumerate(orig):
        if c in uppercase: #this is an uppercase letter
            index = uppercase.index(c)
            rot = (index+13)%26
            l.append(uppercase[rot])
        elif c in lowercase: #this is a lowercase letter
            index = lowercase.index(c)
            rot = (index+13)%26
            l.append(lowercase[rot])
        else:
            l.append(c)
    encoded = ''.join(l)
    return encoded

lowercase = ['a','b','c','d','e','f','g','h','i','j','k','l','m',
             'n','o','p','q','r','s','t','u','v','w','x','y','z']

uppercase = ['A','B','C','D','E','F','G','H','I','J','K','L','M',
             'N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
