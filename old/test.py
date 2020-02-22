from picamera import PiCamera
from time import sleep
from io import BytesIO, StringIO
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from PIL import Image
import boto3, secrets, json, base64, shutil, sys, os
from models import User, AirQuality
from datetime import timedelta

config = None

with open("config.json", "r") as cf:
    config = json.load(cf)

# try:
#     user = User.get("anlin.17@ichat.sp.edu.s") # raise exception if record does not exist
# except User.DoesNotExist:
#     user = None # Should return None if user does not exists according to documentation -> https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
# finally:
#     print(user)

last_rec = AirQuality.query("woodlands", scan_index_forward=False, limit=1).next()
earlier_rec = last_rec.timestamp - timedelta(minutes=120)
data = AirQuality.query("woodlands", AirQuality.timestamp > earlier_rec, scan_index_forward=False)
for row in data:
    print(row.timestamp.strftime("%Y-%m-%d %H:%M:%S"))



#mqtt_client = AWSIoTMQTTClient("PubSub-1726992")
#mqtt_client.configureEndpoint(config["aws_host"], 8883)
#mqtt_client.configureCredentials(config["aws_root_ca"], config["aws_private_key"], config["aws_certificate"])
#mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
#mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
#mqtt_client.configureConnectDisconnectTimeout(10)  # 10 sec
#mqtt_client.configureMQTTOperationTimeout(5)  # 5 sec
#if not mqtt_client.connect():
    #raise Exception("Unable to connect to AWS MQTT broke.")

# camera = PiCamera(resolution=(1280,720))
# sleep(2) # Let camera warm up
# with BytesIO() as pic_stream: # Save captured image to RAM instead of disk, faster
#     camera.capture(pic_stream, "jpeg")
#     pic_stream.seek(0) # Seek to start of buffer as cursor currently at end. If not, upload_fileobj() later will read 0 bytes. https://stackoverflow.com/questions/53485708/how-the-write-read-and-getvalue-methods-of-python-io-bytesio-work
#     im = Image.open(pic_stream)
#     im.resize((480,270), Image.ANTIALIAS)
#     buffer = BytesIO()
#     im.save(buffer, "JPEG", optimize=True, quality=80)
#     print(sys.getsizeof(buffer))
#     buffer.seek(0)
    #with open("test.jpg", "wb") as f:
        #shutil.copyfileobj(buffer, f, length=131072)
    # payload = {"image" : base64.b64encode(buffer.read()).decode("utf-8")}
    # buffer.seek(0)
    # buffer.truncate()
    # buffer.write(json.dumps(payload).encode())
    # print(sys.getsizeof(buffer))
    # with open("payload.json", "w") as p:
    #     json.dump(payload, p)
    # print(os.path.getsize("payload.json"))
    # pic_stream = BytesIO(base64.decodebytes(payload["image"].encode("utf-8")))
    # pic_stream.seek(0)
    # with open("test1.jpg", "wb") as f:
    #     shutil.copyfileobj(pic_stream, f, length=131072)

    #payload = bytearray(buffer.read())
    #mqtt_client.publish("aq/image/woodlands", json.dumps(payload), 1)
    # buffer.close()                              

