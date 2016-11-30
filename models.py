import os
import re
import codecs
import hashlib
import hmac
import random
import string
import webapp2
import jinja2

from google.appengine.ext import ndb

#Return Key for Blog
def blog_key(name='default'):
    return ndb.Key('blogs', name)

#User Info
class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    pwd_hash = ndb.StringProperty(required=True)


#Blog Info
class Post(ndb.Model):
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.StructuredProperty(User)
    likes = ndb.IntegerProperty(default=0)

#Comment Info
class Comment(ndb.Model):
    post_id = ndb.IntegerProperty(required=True)
    author = ndb.StructuredProperty(User)
    content = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

#Like Info
class Like(ndb.Model):
    post_id = ndb.IntegerProperty(required=True)
    author = ndb.StructuredProperty(User)

