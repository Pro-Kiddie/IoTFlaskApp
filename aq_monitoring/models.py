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


if __name__ == "__main__":
    rcu = 1
    wcu = 1
    # Create all the tables 
    if not AirQuality.exists():
        AirQuality.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("AirQuality table created.")
    
    if not Status.exists():
        Status.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("Status table created.")

    if not Device.exists():
        Device.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("Device table created.")

    if not AQImage.exists():
        AQImage.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("AQImage table created.")
    
    # items = AirQuality.query("woodlands", scan_index_forward=False, limit=1)
    # last_rec = items.next()
    # earliest_time = last_rec.timestamp - timedelta(hours=2)
    # print(earliest_time)
    # items = AirQuality.query("woodlands", AirQuality.timestamp < earliest_time, scan_index_forward=False)
    # for item in items:
    #     print(item)
