# sudo python3 -m pip install pynamodb
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, UTCDateTimeAttribute, UnicodeSetAttribute, NumberSetAttribute, MapAttribute, ListAttribute
from datetime import datetime#, timedelta
from flask import current_app
from flask_login import UserMixin
from flask_iot_app import loginManager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer # Generates a secret URL with expiration time for resetting password. Can attach a payload (e.g. user id) with the URL and get it back when the URL is received 

# IoT Models
class AirQuality(Model):
    class Meta:
        table_name = "AirQuality"
    
    device_id = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True, default=datetime.utcnow)
    pm_25 = NumberAttribute()
    pm_10 = NumberAttribute()

class Status(Model):
    class Meta:
        table_name = "Status"

    device_comp = UnicodeAttribute(hash_key=True)
    status = UnicodeAttribute()

class Device(Model):
    class Meta:
        table_name = "Device"
    
    device_id = UnicodeAttribute(hash_key=True)
    geo_coord = ListAttribute()

class AQImage(Model):
    class Meta:
        table_name = "AQImage"

    device_id = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True, default=datetime.utcnow)
    fn = UnicodeAttribute()
    labels = MapAttribute()

# Web App Models
class User(Model, UserMixin):
    class Meta:
        table_name = "User"

    email = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    image_file = UnicodeAttribute(default="default.jpg")
    password = UnicodeAttribute()

    def get_id(self): # override the get_id() inherited from UserMixin. login_user calls get_id() on the user instance. UserMixin provides a get_id method that returns the id attribute or raises an exception.
           return (self.email)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec) # Needs an secret key to generate the secret URL which expires within seconds specified
        return s.dumps({"email" : self.email}).decode("utf-8") # {"email" : self.email} is the payload that will be returned when the secret URL is received
        # The secret URL serialized as bytes must dump as string. 
    
    @staticmethod 
    def verify_reset_token(token):
        s = Serializer(current_app.config["SECRET_KEY"]) # Loads the same secret key to decrypt the token
        try:
            email = s.loads(token)["email"] # "user_id" is the payload
        except: # token could be invalid or expired which will throw exception when trying to loads()
            return None 
        return User.get(email) # Return the user object for resetting its password if valid token

@loginManager.user_loader
def load_user(user_email):
    try:
        user = User.get(user_email) # raise exception if record does not exist
    except User.DoesNotExist:
        user = None # Should return None if user does not exists according to documentation -> https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
    finally:
        return user

# items = AirQuality.query("woodlands", scan_index_forward=False, limit=1) # always return an Iterator! Use .get() to retrieve a single item which will raise exception if does not exists
# last_rec = items.next()
# earliest_time = last_rec.timestamp - timedelta(hours=2)
# print(earliest_time)
# items = AirQuality.query("woodlands", AirQuality.timestamp < earliest_time, scan_index_forward=False)
# for item in items:
#     print(item)

