from flask_mongoengine.wtf import model_form
from wtforms.widgets import TextArea
from mongoengine import (EmbeddedDocument, EmbeddedDocumentField,
                         connect, DecimalField, StringField, IntField, FloatField, ListField, BooleanField, Document, ReferenceField, NULLIFY)

# class User(db.Model):
#     __tablename__ = "users"
#     id = db.Column('user_id',db.Integer , primary_key=True)
#     username = db.Column('username', db.String(20), unique=True , index=True)
#     password = db.Column('password' , db.String(10))
#     email = db.Column('email',db.String(50),unique=True , index=True)
#     registered_on = db.Column('registered_on' , db.DateTime)
 
#     def __init__(self , username ,password , email):
#         self.username = username
#         self.password = password
#         self.email = email
#         self.registered_on = datetime.utcnow()
 
#     def is_authenticated(self):
#         return True
 
#     def is_active(self):
#         return True
 
#     def is_anonymous(self):
#         return False
 
#     def get_id(self):
#         return unicode(self.id)
 
#     def __repr__(self):
#         return '<User %r>' % (self.username)


class Message(Document):
    name = StringField(max_length=200)
    file1 = StringField(max_length=500)
    file2 = StringField(max_length=500)
    file3 = StringField(max_length=500)
    def __unicode__(self):
      return self.name