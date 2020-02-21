# sudo python3 -m pip install pynamodb
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, UTCDateTimeAttribute, UnicodeSetAttribute, NumberSetAttribute, MapAttribute
from datetime import datetime#, timedelta
from flask_login import UserMixin
# from flask_iot_app import loginManager

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

# @loginManager.user_loader
# def load_user(user_email):
#     pass

# items = AirQuality.query("woodlands", scan_index_forward=True, limit=1)
# last_rec = items.next()
# earliest_time = last_rec.timestamp - timedelta(hours=2)
# print(earliest_time)
# items = AirQuality.query("woodlands", AirQuality.timestamp < earliest_time, scan_index_forward=False)
# for item in items:
#     print(item)

