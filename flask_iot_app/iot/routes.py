from datetime import datetime, timedelta, timezone
from flask import jsonify, Blueprint, Response
from flask_login import login_required
from flask_iot_app.iot.models import AirQuality
from flask_iot_app.iot.camera_pi import Camera
from flask_iot_app import led, buzzer

iot = Blueprint("iot", __name__)

@iot.route("/getAQ")
@login_required
def GetAQ():
    # Get the past 60 minute data from the last record for now; can be expanded to past 24 hour if I have more data
    last_rec = AirQuality.query.order_by(AirQuality.id.desc()).first()
    sixty_min_ago = last_rec.timestamp - timedelta(minutes=120)
    data = AirQuality.query.filter(AirQuality.timestamp > sixty_min_ago).all()

    # Within a minute, there can be many records, aggregate the records and take average
    # More informative to users to show average PM2.5 data every minute, rather than every 10 seconds
    # Can change to hours later
    result = []
    cur_time = data[0].timestamp
    sum_25 = 0
    sum_10 = 0
    counter = 0
    for row in data:
        if row.timestamp.minute != cur_time.minute:
            avg_25 = sum_25 / counter
            avg_10 = sum_10 / counter
            # Time saved to database is UTC time, convert back to local timezone
            cur_time = cur_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
            d = dict(zip(['timestamp', "pm25", "pm10"], [cur_time, avg_25, avg_10]))
            result.append(d)
            sum_25 = 0
            sum_10 = 0
            counter = 0
            cur_time = row.timestamp
        
        sum_25 += row.pm_25
        sum_10 += row.pm_10
        counter += 1
        
    # Append data for last minute
    cur_time = cur_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
    d = dict(zip(['timestamp', "pm25", "pm10"], [cur_time, sum_25/counter, sum_10/counter]))
    result.append(d)

    # for row in data:
    #     local_time = row.timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)
    #     result.append(dict(zip(["timestamp", "pm25", "pm10"], [local_time, row.pm_25, row.pm_10])))

    # Encode the data into JSON format for transfer
    return jsonify(result)

@iot.route("/getAvgAQ")
@login_required
def getAvgAQ():
    # Get average PM 2.5 & PM 10 for the past hour for now; can be expanded
    last_rec = AirQuality.query.order_by(AirQuality.id.desc()).first()
    sixty_min_ago = last_rec.timestamp - timedelta(minutes=60)
    data = AirQuality.query.filter(AirQuality.timestamp > sixty_min_ago).all()
    sum_25 = 0
    sum_10 = 0
    for row in data:
        sum_25 += row.pm_25
        sum_10 += row.pm_10
    avg_25 = sum_25 / len(data)
    avg_10 = sum_10 / len(data)
    return jsonify({"avg_25": avg_25, "avg_10" : avg_10})

@iot.route("/getLEDStatus")
@login_required
def getLEDStatus():
    result = dict()
    if led.is_lit:
        result['LED_status'] = "On"
    else:
        result['LED_status'] = "Off"
    return jsonify(result)


@iot.route("/buzzerState/<status>")
@login_required
def buzzerState(status=None):
    if status == "On":
        buzzer.on()
    elif status == "Off":
        buzzer.off()
    return jsonify({"buzzer_status": "On" if buzzer.is_active else "Off"})

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@iot.route('/video_feed')
@login_required
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


    
