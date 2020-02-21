from datetime import datetime, timedelta, timezone
from decimal import Decimal
from flask import jsonify, Blueprint, Response
from flask_login import login_required
from flask_iot_app.models import AirQuality, Status
# from flask_iot_app.iot.camera_pi import Camera
# from flask_iot_app import led, buzzer

iot = Blueprint("iot", __name__)

@iot.route("/getAQ")
@iot.route("/getAQ/<device_id>")
@iot.route("/getAQ/<device_id>/<timeframe>")
@login_required
def GetAQ(device_id = "woodlands", timeframe = 0):
    m = 0
    timeframe = int(timeframe)
    if(timeframe == 0):
        m = 120
    elif(timeframe == 1):
        m = 720
    elif (timeframe == 2):
        m = 1440
    elif (timeframe == 3):
        m = 10080
    # Get the past 60 minute data from the last record for now; can be expanded to past 24 hour if I have more data
    # last_rec = AirQuality.query.order_by(AirQuality.id.desc()).first()
    # sixty_min_ago = last_rec.timestamp - timedelta(minutes=120)
    # data = AirQuality.query.filter(AirQuality.timestamp > sixty_min_ago).all()
    last_rec = AirQuality.query(device_id, scan_index_forward=False, limit=1).next()
    earlier_rec = last_rec.timestamp - timedelta(minutes=120)
    data = AirQuality.query(device_id, AirQuality.timestamp > earlier_rec, scan_index_forward=True)

    # Within a minute, there can be many records, aggregate the records and take average
    # More informative to users to show average PM2.5 data every minute, rather than every 10 seconds
    # Can change to hours later
    result = []
    first_row = data.next()
    cur_time = first_row.timestamp
    sum_25 = first_row.pm_25
    sum_10 = first_row.pm_10
    counter = 1
    if (timeframe == 0):
        for row in data:
            if row.timestamp.minute != cur_time.minute:
                avg_25 = sum_25 / counter
                avg_10 = sum_10 / counter
                # Time saved to database is UTC time, convert back to local timezone
                cur_time = cur_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
                d = dict(zip(['timestamp', "pm25", "pm10"], [cur_time, Decimal(avg_25), Decimal(avg_10)]))
                result.append(d)
                sum_25 = 0
                sum_10 = 0
                counter = 0
                cur_time = row.timestamp
            
            sum_25 += row.pm_25
            sum_10 += row.pm_10
            counter += 1
    elif (timeframe == 1 or timeframe == 2):
        for row in data:
            if row.timestamp.hour != cur_time.hour:
                avg_25 = sum_25 / counter
                avg_10 = sum_10 / counter
                # Time saved to database is UTC time, convert back to local timezone
                cur_time = cur_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
                d = dict(zip(['timestamp', "pm25", "pm10"], [cur_time, Decimal(avg_25), Decimal(avg_10)]))
                result.append(d)
                sum_25 = 0
                sum_10 = 0
                counter = 0
                cur_time = row.timestamp
            
            sum_25 += row.pm_25
            sum_10 += row.pm_10
            counter += 1
    else:
        for row in data:
            if row.timestamp.day != cur_time.day:
                avg_25 = sum_25 / counter
                avg_10 = sum_10 / counter
                # Time saved to database is UTC time, convert back to local timezone
                cur_time = cur_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
                d = dict(zip(['timestamp', "pm25", "pm10"], [cur_time, Decimal(avg_25), Decimal(avg_10)]))
                result.append(d)
                sum_25 = 0
                sum_10 = 0
                counter = 0
                cur_time = row.timestamp
            
            sum_25 += row.pm_25
            sum_10 += row.pm_10
            counter += 1
    # Append data for last minute/hour/day
    cur_time = cur_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
    # print(isinstance(sum_25/counter, float))
    d = dict(zip(['timestamp', "pm25", "pm10"], [cur_time, Decimal(sum_25/counter), Decimal(sum_10/counter)]))
    result.append(d)

    # for row in data:
    #     local_time = row.timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)
    #     result.append(dict(zip(["timestamp", "pm25", "pm10"], [local_time, row.pm_25, row.pm_10])))

    # Encode the data into JSON format for transfer
    return jsonify(result)

@iot.route("/getAvgAQ")
@iot.route("/getAvgAQ/<device_id>")
@login_required
def getAvgAQ(device_id = "woodlands"):
    # Get average PM 2.5 & PM 10 for the past hour for now; can be expanded
    # last_rec = AirQuality.query.order_by(AirQuality.id.desc()).first()
    # sixty_min_ago = last_rec.timestamp - timedelta(minutes=60)
    # data = AirQuality.query.filter(AirQuality.timestamp > sixty_min_ago).all()
    last_rec = AirQuality.query(device_id, scan_index_forward=False, limit=1).next()
    earlier_rec = last_rec.timestamp - timedelta(minutes=60)
    data = AirQuality.query(device_id, AirQuality.timestamp > earlier_rec, scan_index_forward=False)
    sum_25 = 0
    sum_10 = 0
    for row in data:
        sum_25 += row.pm_25
        sum_10 += row.pm_10
    avg_25 = sum_25 / data.total_count
    avg_10 = sum_10 / data.total_count
    return jsonify({"avg_25": Decimal(avg_25), "avg_10" : Decimal(avg_10)})

@iot.route("/getLEDStatus")
@iot.route("/getLEDStatus/<device_id>")
@login_required
def getLEDStatus(device_id = "woodlands"):
    result = dict()
    # if led.is_lit:
    #     result['LED_status'] = "On"
    # else:
    #     result['LED_status'] = "Off"
    status = Status.get("{}_{}".format(device_id, "led")).status # device_id entered must be valid, if not will throw exception 
    result["LED_status"] = status.capitalize()
    return jsonify(result)

@iot.route("/buzzerState/<status>")
@iot.route("/buzzerState/<device_id>/<status>")
@login_required
def buzzerState(device_id = "woodlands", status = "state"):
    if status == "State":
        status = Status.get("{}_{}".format(device_id, "buzzer")).status
    elif status == "On" or status == "Off":
        hash_key = device_id + "_" + "buzzer"
        new_status = Status(hash_key)
        new_status.update(actions=[Status.status.set(status.lower())])
    return jsonify({"buzzer_status": status.capitalize()})

# def gen(camera):
#     """Video streaming generator function."""
#     while True:
#         frame = camera.get_frame()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @iot.route('/video_feed')
# @login_required
# def video_feed():
#     """Video streaming route. Put this in the src attribute of an img tag."""
#     return Response(gen(Camera()),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')


    
