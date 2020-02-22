from flask_iot_app import db
from datetime import datetime

class AirQuality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pm_25 = db.Column(db.DECIMAL(4,1), nullable=False) # According to SDS011's data specification, reading can only be 0-999
    pm_10 = db.Column(db.DECIMAL(4,1), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # Store datetime to database without timezone info, as UTC. Later when retrivial can add timezone info based on the location of customer

    def __repr__(self):
        return "{}\tPM 2.5: {}\tPM 10: {}".format(self.timestamp, self.pm_25, self.pm_10)

class ImageCapture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(100), nullable=False, unique=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return self.image