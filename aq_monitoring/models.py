# sudo python3 -m pip install pynamodb
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, UTCDateTimeAttribute, UnicodeSetAttribute, NumberSetAttribute, MapAttribute
from datetime import datetime#, timedelta

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
