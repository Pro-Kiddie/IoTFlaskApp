import os, botocore, json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from flask import jsonify, Blueprint, Response, redirect, url_for, current_app
from flask_login import login_required
from flask_iot_app import s3
from flask_iot_app.models import AirQuality, Status, AQImage, Device
from time import sleep
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
    earlier_rec = last_rec.timestamp - timedelta(minutes=m)
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

@iot.route("/allBuzzer/<status>")
def toggleAllBuzzers(status = "state"):
    query = Device.scan()
    for device in query:
        hash_key = device.device_id + "_" + "buzzer"
        new_status = Status(hash_key)
        new_status.update(actions=[Status.status.set(status.lower())])
    return jsonify({"buzzer_status": status.capitalize()})

@iot.route("/allTakePhoto")
def allTakePhoto():
    mqtt_client = AWSIoTMQTTClient(current_app.config['MQTT_CLIENT_NAME'])
    mqtt_client.configureEndpoint(current_app.config['AWS_HOST'], 8883)
    mqtt_client.configureCredentials(current_app.config['AWS_ROOT_CA'], current_app.config['AWS_PRIVATE_KEY'], current_app.config['AWS_CERTIFICATE'])
    mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
    mqtt_client.configureConnectDisconnectTimeout(10)  # 10 sec
    mqtt_client.configureMQTTOperationTimeout(5)  # 5 sec
    if not mqtt_client.connect():
            raise Exception("Unable to connect to AWS MQTT broke.")

    device_list = [device.device_id for device in Device.scan()]

    for device in device_list:
        mqtt_client.publish("status/{}/takephoto".format(device), json.dumps({"comp" : "camera", "status" : "take"}), 1)
        sleep(1)
    print("Taking photos for ALL")

    return 'OK'

@iot.route("/image")
@iot.route("/image/<fn>")
@login_required
def renderImage(fn = "test.jpg"): # E.g. fn = deviceid_asdsadqweqwads.jpg
    # Check if the image exists in static/captured_img
    # If not exists download from S3 and render
    img_path = os.path.join(current_app.root_path, "static/captured_img", fn)
    if not os.path.exists(img_path):
        # print(current_app.config.get("AWS_S3_BUCKET"))
        img_on_s3 = s3.Object(current_app.config["AWS_S3_BUCKET"], fn)
        try:
            img_on_s3.load() # check if current pic exists
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                # The object does not exist.
                print("The AQ image is not available on S3.")
        else:
            # The object does exist. Download it to local image cache folder
            img_on_s3.download_file(img_path)
    return redirect(url_for('static', filename='captured_img/' + fn))

@iot.route("/getAQMap")
@login_required
def getAQMap(): 
    result = []
    # Retrieve all the devices with their coordinates
    # For device, for mulate the result in such format: [{name: "woodlands", value : [cord1, cord2, "PM2.5 PM10"]}, {obj2} ...]
    devices = Device.scan()
    for device in devices:
        record = {'name' : device.device_id.capitalize(), 'value' : device.geo_coord}
        latest_reading = AirQuality.query(device.device_id, scan_index_forward=False, limit=1).next()
        record['value'].append(latest_reading.pm_25)
        result.append(record)
    return jsonify(result)

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


    
