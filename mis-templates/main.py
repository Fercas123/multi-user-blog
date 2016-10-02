import os
import re

import jinja2
import webapp2
from string import letters

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape= True)


class Handler(webapp2.RequestHandler):
    def write (self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))



#Shopping List Project
class MainPage(Handler):
    def get(self):
        items = self.request.get_all("food")
        self.render("shopping_list.html", items = items)

#FizzBuzz Project, get fizz when divisible by 3, buzz by 5, fizzbuzz by both
class FizzBuzzHandler(Handler):
    def get(self):
        n=self.request.get('n', 0)
        n = n and int(n)
        self.render('fizzbuzz.html', n=n)

#Rot13 Project, change the letters for letter+13
class RotHandler(Handler):
    def get(self):
        self.render('rot13.html')

    def post(self):
        rot13 = ''
        text = self.request.get('text')
        if text:
            for c in text:
                if ord(c) >= ord('a') and ord(c) <= ord('z'):
                    rot13 += chr((ord(c) - ord('a') + 13) % 26 + ord('a'))
                elif ord(c) >= ord('A') and ord(c) <= ord('Z'):
                    rot13 += chr((ord(c) - ord('A') + 13) % 26 + ord('A'))
                else:
                    rot13 += c

        self.render('rot13.html', text= rot13)

#Signup project, enter valid name, password and/or email
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class SignUpHandler(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                      email = email)

        if not valid_username(username):
            params['error_username'] = "That name is not valid or too small"
            have_error = True

        if not valid_password(password):
            params['error_password'] = "We cant accept that as a password"
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your password didn't match"
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email"
            have_error = True

        if have_error:
            self.render('signup.html', **params)
        else:
            self.redirect('/welcome?username=' + username)

class Welcome(Handler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/signup')

#Posting in the blog project
def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("blog/post.html", p = self)

class BlogIndex(Handler):
    def render_front(self, title="", content="", error=""):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 5")
        self.render('blog/index.html', title=title, content=content, error=error, posts = posts)

    def get(self):
        self.render_front()

class NewPost(Handler):
    def get(self):
        self.render('blog/newpost.html')

    def post(self):
        title = self.request.get('title')
        content = self.request.get('content')

        if title and content:
            p = Post(parent = blog_key(), title = title, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "we need both title and some text"
            self.render("blog/newpost.html", title=title, content=content, error=error)

class Permalink(NewPost):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("blog/post.html", post = post)




app = webapp2.WSGIApplication([
    ('/', MainPage), ('/fizzbuzz', FizzBuzzHandler),('/rot13', RotHandler),
    ('/signup', SignUpHandler), ('/welcome', Welcome),
    ('/blog/?', BlogIndex), ('/blog/newpost', NewPost),('/blog/([0-9]+)', Permalink)
], debug=True)
