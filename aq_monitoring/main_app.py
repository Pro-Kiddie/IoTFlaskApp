import threading, serial, json, boto3, re, telepot, sys, base64, random
from rpi_lcd import LCD
from gpiozero import LED, Buzzer, MotionSensor
from twilio.rest import Client
from datetime import datetime, timedelta
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from picamera import PiCamera
from io import BytesIO
from telepot.loop import MessageLoop
from PIL import Image

class MainApp():

    # Global variables shared between 2 or more threads
    config = None
    iot_threads = []
    instance_created = False
    device_id = None

    # Global variable for MQTT Client
    mqtt_client = None

    # Global variables for PM Sensor
    pm_25 = 0
    pm_10 = 0
    pm25Threshold = None
    pm10Threshold = None
    #pm_lock = threading.Lock(j) # Not really needed. https://stackoverflow.com/questions/3714613/python-safe-to-read-values-from-an-object-in-a-thread

    # Global variable for Buzzer
    buzzer = None
    buzzer_lock = threading.Lock() # Do not know if gpiozero.Buzzer is thread safe. If _update_buzzer() and telegram thread call MainApp.buzzer.on() tgt
    buzzer_status = None

    # Global variable for telegram bot
    telegram_chat_id = None
    telegram_bot = None

    # Global variable for PiCamera
    camera_lock = threading.Lock()

    def __init__(self, config_file):
        # Only allow one instance of this class
        if MainApp.instance_created:
            raise Exception("Only one instance is allowed for this class.")
        MainApp.instance_created = True

        # Load config file
        with open(config_file, "r") as cf:
            MainApp.config = json.load(cf)

        # Initialization of Global variables
        MainApp.device_id = MainApp.config["device_id"]

        MainApp.mqtt_client = AWSIoTMQTTClient(MainApp.config["mqtt_client_name"])
        MainApp.mqtt_client.configureEndpoint(MainApp.config["aws_host"], 8883)
        MainApp.mqtt_client.configureCredentials(MainApp.config["aws_root_ca"], MainApp.config["aws_private_key"], MainApp.config["aws_certificate"])
        MainApp.mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        MainApp.mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
        MainApp.mqtt_client.configureConnectDisconnectTimeout(10)  # 10 sec
        MainApp.mqtt_client.configureMQTTOperationTimeout(5)  # 5 sec
        if not MainApp.mqtt_client.connect():
            raise Exception("Unable to connect to AWS MQTT broke.")

        MainApp.pm25Threshold = float(MainApp.config["device_components"]["pm25Threshold"]) # Use [] operator instead of .get() to throw exception if any
        MainApp.pm10Threshold = float(MainApp.config["device_components"]["pm10Threshold"])

        MainApp.buzzer = Buzzer(5)
        MainApp.buzzer_status = MainApp.config["device_components"]["buzzer"]

        MainApp.telegram_chat_id = MainApp.config["telegram_chat_id"]
        MainApp.telegram_bot =  telepot.Bot(MainApp.config["telegram_bot_token"])

        # Publish all status -> Sync with database in case of restart
        for c, v in MainApp.config["device_components"].items():
            payload = {"device_comp" : "{}_{}".format(MainApp.device_id, c), "status" : v}
            MainApp.mqtt_client.publish("status/{}".format(MainApp.device_id), json.dumps(payload), 1)
            
        # Subscribe to device's own status and update if there is any change
        MainApp.mqtt_client.subscribe("status/{}/+".format(MainApp.device_id), 1, self._update_status)

    def _pm_sensor(self):
        # Local variables for PM sensor
        seri = serial.Serial("/dev/ttyUSB0")
        lcd = LCD()
        led = LED(16)

        next_alert_time = datetime.now()

        # Main loop
        while True:
            try:
                data = list()
                # Read data from SDS011 which returns in 10 bytes at a time
                for _ in range(10):
                    byte = seri.read()
                    data.append(byte)

                # Parse the PM2.5 and PM10 data
                MainApp.pm_25 = (int.from_bytes(data[3], byteorder="little") * 256 + int.from_bytes(data[2], byteorder="little")) / 10 # pm_25 = int.from_bytes(b"".join(data[2:4]), byteorder="little") / 10
                MainApp.pm_10 = int.from_bytes(b"".join(data[4:6]), byteorder="little") / 10

                # If no SDS101 pm sensor available, use random generated data as pseudo device
                # Comment out line 85, 94-102 & Uncomment out the two lines below
                # MainApp.pm_25 = round(random.uniform(5, 300), 1)
                # MainApp.pm_10 = round(random.uniform(5, 400), 1)

                now = datetime.now()
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                
                # Publish AQ data to MQTT channel which will be stored into DB by AWS rule
                payload = {"device_id" : MainApp.device_id, 
                           "timestamp" : datetime.utcnow().isoformat(), 
                           "pm_25" : MainApp.pm_25,
                           "pm_10" : MainApp.pm_10 }
                MainApp.mqtt_client.publish("aq", json.dumps(payload), 1)
                
                # Display readings onto console
                print("PM Sensor Thread\t\t {}\t PM 2.5: {:.1f}\t PM 10: {:.1f}".format(now_str, MainApp.pm_25, MainApp.pm_10))
                
                # Both PM2.5 and PM10 within healthy range
                if MainApp.pm_25 <= MainApp.pm25Threshold and MainApp.pm_10 <= MainApp.pm10Threshold:
                    # Display readings onto LCD
                    lcd.text("PM 2.5: {:.1f}".format(MainApp.pm_25), 1)
                    lcd.text("PM 10: {:.1f}".format(MainApp.pm_10), 2)
                    # Turn off LED if it is on
                    if led.is_lit:
                        led.off()
                        # Launch another daemon thread to update LED status in db
                        payload = {"device_comp" : "{}_{}".format(MainApp.device_id, "led"),
                                   "status" : "off"}
                        MainApp.mqtt_client.publish("status/{}".format(MainApp.device_id), json.dumps(payload), 1)
                        print("PM Sensor Thread\t\t {}\t Turned Off LED".format(now_str))

                # Either or both PM2.5 and PM10 exceeded healthy range
                else:
                    # Display readings onto LCD
                    lcd.text("PM {}: {:.1f}".format("2.5" if MainApp.pm_25 > MainApp.pm25Threshold else "10", MainApp.pm_25 if MainApp.pm_25 > MainApp.pm25Threshold else MainApp.pm_10), 1) # Priority in displaying PM2.5 value if both unhealthy
                    lcd.text("Alerting NEA!", 2)
                    # Turn on LED if it is off
                    if not led.is_lit:
                        led.on()
                        payload = {"device_comp" : "{}_{}".format(MainApp.device_id, "led"),
                                   "status" : "on"}
                        MainApp.mqtt_client.publish("status/{}".format(MainApp.device_id), json.dumps(payload), 1)
                        print("PM Sensor Thread\t\t {}\t Turned On LED".format(now_str))

                    # Send alerts every 1 hour
                    if next_alert_time < now:
                        camera = None
                        MainApp.camera_lock.acquire()
                        try:
                            # Publish to AQ Alert to trigger Lambda to sent SMS
                            payload = {"device_id" : MainApp.device_id, 
                                       "pm_25" : MainApp.pm_25,
                                       "pm_10" : MainApp.pm_10 }
                            MainApp.mqtt_client.publish("aq/sms", json.dumps(payload), 0)
                            print("PM Sensor Thread\t\t {}\t Alert SMS Sent.".format(now_str))

                            # Take a photo of factory monitered
                            camera = PiCamera(resolution=(1280,720))
                            sleep(2) # Let camera warm up
                            with BytesIO() as pic_stream: # Save captured image to RAM instead of disk, faster
                                camera.capture(pic_stream, "jpeg")
                                pic_stream.seek(0) # Seek to start of buffer as cursor currently at end.

                                # Compress image as the maximum MQTT payload in AWS IoT Core is only 128kB.
                                im = Image.open(pic_stream)
                                im.resize((480,270), Image.ANTIALIAS)
                                buffer = BytesIO()
                                im.save(buffer, "JPEG", optimize=True, quality=80)
                                buffer.seek(0)

                                # Publish to AQ Image and the lambda will upload the image to S3
                                # Successful S3 image upload will trigger the another AWS Lambda function configured.
                                # The Lambda function sends the image to Rekognition
                                # Before saveing the device_id, S3 image_name and labels detected in DB

                                # Cannot publish in bytearray as AWS Lambda can only be invoked by sending JSON data! https://forums.aws.amazon.com/thread.jspa?threadID=225051 
                                # if sys.getsizeof(buffer) < 128000:
                                    # payload = bytearray(buffer.read())
                                    # MainApp.mqtt_client.publish("aq/image/{}".format(MainApp.device_id), payload, 1)

                                payload = {"image" : base64.b64encode(buffer.read()).decode("utf-8")}
                                buffer.seek(0)
                                buffer.truncate()
                                buffer.write(json.dumps(payload).encode())
                                if sys.getsizeof(buffer) < 128000: 
                                    MainApp.mqtt_client.publish("aq/image/{}".format(MainApp.device_id), json.dumps(payload), 1)
                                    print("PM Sensor Thread\t\t {}\t Image Taken and Uploaded.".format(now_str))
                                else:
                                    print("PM Sensor Thread\t\t {}\t Sent Failed. Encoded Image Size Exceeded 128kb.".format(now_str))
                                buffer.close()

                                # Send image taken via telegram - <TO DO> if have time

                        except Exception as e:
                            print(e)
                            print("Failed to perform Unhealthy Alerat opeartions. Retry in an hour.")
                        finally:
                            # Add 1 hour to next_alert_time, so will only perform Alert opeartions hourly
                            next_alert_time += timedelta(hours=1)
                            # Release camera for other threads
                            if camera != None: 
                                camera.close() # Always close camera 
                            MainApp.camera_lock.release()
                
            except Exception as e:
                print(e)
                print("PM Sensor Thread - Exception. Recovering...")
            finally:
                sleep(10)

    def _update_status(self, client, userdata, message):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            payload = json.loads(message.payload)
            comp = payload["comp"] # pm25Threshold, pm10Threshold, buzzer, camera
            status = payload["status"]  # Taking the status stored on db as the true status as web app can only modify the status in db
            if comp == "pm25Threshold":
                MainApp.pm25Threshold = float(status)
                print("Update Status Thread\t\t {}\t PM 2.5 Threshold Updated.".format(now_str))
            elif comp == "pm10Threshold":
                MainApp.pm10Threshold = float(status)
                print("Update Status Thread\t\t {}\t PM 10 Threshold Updated.".format(now_str))
            elif comp == "buzzer" and status != MainApp.buzzer_status:
                # local buzzer status different from the buzzer status on db, update local status
                with MainApp.buzzer_lock:
                    if status == "on":
                        MainApp.buzzer.on()
                        MainApp.buzzer_status = status
                        print("Update Status Thread\t\t {}\t Turned On Buzzer.".format(now_str))
                    elif status == "off":
                        MainApp.buzzer.off()
                        MainApp.buzzer_status = status
                        print("Update Status Thread\t\t {}\t Turned Off Buzzer.".format(now_str))
            elif comp == "camera":
                t = threading.Thread(target=self._take_photo, name="take_photo", daemon=True)
                t.start()
                print("Update Status Thread\t\t {}\t Taking a Photo and Sending via Telegram.".format(now_str))
        except Exception as e:
            print(e)
            print("Update Status Thread - Exception. Failed to update {} status.".format(comp))

    def _take_photo(self):
        try:
            MainApp.camera_lock.acquire()
            camera = PiCamera(resolution=(1280,720))
            sleep(2)
            with BytesIO() as pic_stream:
                camera.capture(pic_stream, "jpeg")
                pic_stream.seek(0)
                MainApp.telegram_bot.sendPhoto(MainApp.telegram_chat_id, pic_stream, caption="Device ID: {}\nFactory Photo Taken.".format(MainApp.device_id))
        except Exception as e:
            print(e)
        finally:
            if camera != None:
                camera.close()
            MainApp.camera_lock.release()
    
    def _motion_sensor(self):
        motionsensor = MotionSensor(13, sample_rate=6, queue_len=1)
        while True:
            try:
                motionsensor.wait_for_motion()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("Motion Sensor Thread \t\t {}\t Suspicious Motion Detected At Device.".format(now_str))
                MainApp.camera_lock.acquire()
                camera = PiCamera(resolution=(1280,720))
                sleep(2)
                with BytesIO() as pic_stream:
                    camera.capture(pic_stream, "jpeg")
                    pic_stream.seek(0)
                    MainApp.telegram_bot.sendPhoto(MainApp.telegram_chat_id, pic_stream, caption="{}\nDevice ID: {}\nSuspicious Motion Detected!\nSomeone Maybe Sabotaging the Air Quality Monitoring Device.".format(now_str, MainApp.device_id))
                    print("Motion Sensor Thread \t\t {}\t Image Taken and Sent to User.".format(now_str))
            except Exception as e:
                print(e)
                print("Motion Sensor Thread - Exception. Recovering ...")
            finally:
                if camera != None:
                    camera.close()
                MainApp.camera_lock.release()
                motionsensor.wait_for_no_motion()
                sleep(10)
    
    def run_pm_sensor(self):
        t = threading.Thread(target=self._pm_sensor, name="pm_sensor", daemon=True)# Launch as daemon thread which will end automatically when main thread ends and does not block main thread
        MainApp.iot_threads.append(t)
        t.start()

    def run_motion_sensor(self):
        t = threading.Thread(target=self._motion_sensor, name="motion_sensor", daemon=True)
        MainApp.iot_threads.append(t)
        t.start()

   