from mongoengine import FileField, DateTimeField, ListField, IntField, \
    StringField, SequenceField, ReferenceField, EmailField
from plus.mongoengine_plus import Document


class DocMinix(object):
    pass

class User(Document, DocMinix):
    
    user_name = StringField()
    email = EmailField(primary_key=True, required=True, unique=True)
    passwd = StringField()
    
    
    