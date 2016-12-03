import os
import re
import random
import hashlib
import hmac
import webapp2
import jinja2
import codecs
import string

from models import *

from string import letters
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


secret = 'abcdef'

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PWD_RE = re.compile(r"^.{3,20}$")


def valid_username(username):
    """Validate Username"""
    return USER_RE.match(username)


def valid_password(password):
    """Validate Password"""
    return PWD_RE.match(password)


def hash_str(s):
    """Encrypt Password with HMAC"""
    return hmac.new(secret, s).hexdigest()


def make_secure_val(s):
    """Make secure value"""
    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
    """Validate secure value"""
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val


def make_salt():
    """Generate salt for hashing"""
    return ''.join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(name, pw, salt=None):
    """Encrypt password with HASH"""
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)


def valid_pw(name, pw, h):
    """Decrypt Password"""
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)


def users_key(group='default'):
    """Return User Key"""
    return ndb.Key('users', group)

def blog_key(name='default'):
    '''Return Key for Blog'''
    return ndb.Key('blogs', name)    


class BlogHandler(webapp2.RequestHandler):
    """Define functions for rendering Web Pages"""
    def write(self, *a, **kw):
        """Write to Web Page"""
        self.response.write(*a, **kw)

    def render_str(self, template, **kw):
        """Render Jinja template"""
        kw['user'] = self.user
        t = jinja_env.get_template(template)
        return t.render(kw)

    def render(self, template, **kw):
        """Write template to Web Page"""
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        """Set Cookie"""
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        """Return Cookie Value"""
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def initialize(self, *a, **kw):
        """Initialise Web Page with signed-in user"""
        webapp2.RequestHandler.initialize(self, *a, **kw)
        username = self.read_secure_cookie('user')
        self.user = User.gql("WHERE username = '%s'" % username).get()


class Signup(BlogHandler):
    """Handler for Signup"""
    def get(self):
        self.render("signup.html")

    def post(self):
        user_error = False
        pwd_error = False
        verify_error = False
        exist_error = False
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")

        user = User.gql("WHERE username = '%s'" % username).get()
        if user:
            exist_error = True
            self.render(
                "signup.html",
                exist_error=exist_error, username=username)
        else:
            if not username or not valid_username(username):
                user_error = True
            if not password or not verify or not valid_password(password):
                pwd_error = True
            if password != verify:
                verify_error = True

            if user_error or pwd_error or verify_error:
                self.render("signup.html",
                            user_error=user_error,
                            pwd_error=pwd_error,
                            verify_error=verify_error,
                            username=username)
            else:
                user = User(username=username,
                            pwd_hash=make_pw_hash(username, password))
                user.put()
                user_cookie = make_secure_val(str(username))
                self.response.headers.add_header(
                    "Set-Cookie",
                    "user=%s; Path=/" % user_cookie)
                self.redirect("/blog")


class Login(BlogHandler):
    """Handler for Login"""
    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        user = User.gql("WHERE username = '%s'" % username).get()
        if user and valid_pw(username, password, user.pwd_hash):
            user_cookie = make_secure_val(str(username))
            self.response.headers.add_header("Set-Cookie",
                                             "user=%s; Path=/" % user_cookie)
            self.redirect("/blog")
        else:
            error = "Invalid username"
            self.render("login.html", username=username, error=error)


class Logout(BlogHandler):
    """Handler for Logout"""
    def get(self):
        self.response.headers.add_header("Set-Cookie", "user=; Path=/")
        self.redirect("/blog")


class Blog(BlogHandler):
    def get(self):
        posts = ndb.gql("select * from PostModel order by created desc limit 10")
        self.render("front.html", posts=posts)


class NewPost(BlogHandler):
    """Handler for NewPost"""
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            return self.redirect("/login")
        subject = self.request.get("subject")
        content = self.request.get("content")
        print "subject %s" % subject
        print "content %s" % content
        if subject and content:
            post = PostModel(parent=blog_key(),subject=subject,content=content,author=self.user)
            post.put()
            self.redirect("/blog")
        else:
            error = "Missing subject or content"
            self.render(
                "newpost.html",
                subject=subject, content=content, error=error)


class Post(BlogHandler):
    """Handler for Post and renders comments and likes"""
    def get(self, post_id):
        key = ndb.Key('PostModel', int(post_id), parent=blog_key())
        post = key.get()
        comments = Comment.gql("WHERE post_id = %s ORDER BY created DESC"
                               % int(post_id))
        liked = None
        if self.user:
            liked = Like.gql("WHERE post_id = :1 AND author.username = :2",
                             int(post_id), self.user.username).get()
        if not post:
            self.error(404)
            return
        self.render("permalink.html", post=post, comments=comments, liked=liked)

    def post(self, post_id):
        key = ndb.Key('PostModel', int(post_id), parent=blog_key())
        post = key.get()
        liked = Like.gql("WHERE post_id = :1 AND author.username = :2",
                        int(post_id), self.user.username).get()
        if self.request.get("like"):
            if post and not self.user and not self.user == PostModel.author  and not liked:
                post.likes += 1
                like = Like(post_id=int(post_id), author=self.user)
                like.put()
                post.put()
            self.redirect("/blog/%s" % post_id)
        elif self.request.get("unlike"):
            if post and self.user and liked:
                post.likes -= 1
                key = liked.key
                key.delete()
                post.put()
            self.redirect("/blog/%s" % post_id)
        else:
            if not self.user:
                return self.redirect("/login")
            content = self.request.get("content")
            if content:
                comment = Comment(content=str(content),
                                  author=self.user,
                                  post_id=int(post_id))
                comment.put()
                self.redirect("/blog/%s" % post_id)
            else:
                self.render("permalink.html", post=post)


class EditPost(BlogHandler):
    """Handler for EditPost"""
    def get(self):
        if self.user:
            post_id = self.request.get("post")
            key = ndb.Key('PostModel', int(post_id), parent=blog_key())
            post = key.get()
            if not post:
                self.error(404)
                return
            self.render("editpost.html",
                        subject=post.subject, content=post.content)
        else:
            self.redirect("/login")

    def post(self):
        post_id = self.request.get("post")
        key = ndb.Key('PostModel', int(post_id), parent=blog_key())
        post = key.get()
        if post and post.author.username == self.user.username:
            if not self.user:
                return self.redirect("/login")
            subject = self.request.get("subject")
            content = self.request.get("content")
            if subject and content:
                post.subject = subject
                post.content = content
                post.put()
                self.redirect("/blog")
            else:
                error = "Missing subject or content"
                self.render("editpost.html",
                            subject=subject, content=content, error=error)
        else:
            self.redirect("/blog")


class DeletePost(BlogHandler):
    """Handler for DeletePost"""
    def get(self):
        if self.user:
            post_id = self.request.get("post")
            key = ndb.Key('PostModel', int(post_id), parent=blog_key())
            post = key.get()
            if not post:
                self.error(404)
                return
            self.render("deletepost.html", post=post)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            return self.redirect("/login")
        post_id = self.request.get("post")
        key = ndb.Key('PostModel', int(post_id), parent=blog_key())
        post = key.get()
        if post and post.author.username == self.user.username:
            key.delete()
        self.redirect("/blog")


class EditComment(BlogHandler):
    """Handler for EditComment"""
    def get(self):
        if self.user:
            comment_id = self.request.get("comment")
            key = ndb.Key('Comment', int(comment_id))
            comment = key.get()
            if not comment:
                self.error(404)
                return
            self.render("editcomment.html",
                        content=comment.content, post_id=comment.post_id)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            return self.redirect("/login")
        comment_id = self.request.get("comment")
        key = ndb.Key('Comment', int(comment_id))
        comment = key.get()
        if comment and comment.author.username == self.user.username:
            content = self.request.get("content")
            if content:
                comment.content = content
                comment.put()
                self.redirect("/blog/%s" % comment.post_id)
            else:
                error = "Missing subject or content"
                self.render("editcomment.html",
                            content=content,
                            post_id=comment.post_id,
                            error=error)
        else:
            self.redirect("/blog/%s" % comment.post_id)


class DeleteComment(BlogHandler):
    """Handler for DeleteComment"""
    def get(self):
        if self.user:
            comment_id = self.request.get("comment")
            key = ndb.Key('Comment', int(comment_id))
            comment = key.get()
            if not comment:
                self.error(404)
                return
            self.render("deletecomment.html", comment=comment)
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            return self.redirect("/login")
        comment_id = self.request.get("comment")
        key = ndb.Key('Comment', int(comment_id))
        comment = key.get()
        if comment and comment.author.username == self.user.username:
            post_id = comment.post_id
            key.delete()
        self.redirect("/blog/%s" % post_id)

app = webapp2.WSGIApplication([('/', Blog),
                               ('/signup', Signup),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/blog', Blog),
                               ('/blog/newpost', NewPost),
                               ('/blog/([0-9]+)', Post),
                               ('/blog/edit', EditPost),
                               ('/blog/delete', DeletePost),
                               ('/comment/edit', EditComment),
                               ('/comment/delete', DeleteComment),
                               ], debug=True)
