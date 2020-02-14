import threading, serial, json, secrets, boto3, re, telepot
from models import AirQuality, Status, Device
from rpi_lcd import LCD
from gpiozero import LED, Buzzer
from twilio.rest import Client
from datetime import datetime, timedelta
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from picamera import PiCamera
from io import BytesIO
from telepot.loop import MessageLoop

class MainApp():

    # Global variables shared between 2 or more threads
    config = None
    iot_threads = []
    instance_created = False
    device_id = None

    # Global variable for MQTT Client
    mqtt_client = None

    # Global variables for PM Sensor
    pm25 = 0
    pm10 = 0
    pm25_threshold = None
    pm10_threshold = None
    #pm_lock = threading.Lock(j) # Not really needed. https://stackoverflow.com/questions/3714613/python-safe-to-read-values-from-an-object-in-a-thread

    # Global variable for Buzzer
    buzzer = None
    buzzer_lock = threading.Lock() # Do not know if gpiozero.Buzzer is thread safe. If _update_buzzer() and telegram thread call MainApp.buzzer.on() tgt
    buzzer_status = None

    # Global variable for telegram bot
    telegram_chat_id = None
    telegram_bot = None

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

        MainApp.mqtt_client = AWSIoTMQTTClient("PubSub-1726992")
        MainApp.mqtt_client.configureEndpoint(MainApp.config["aws_host"], 8883)
        MainApp.mqtt_client.configureCredentials(MainApp.config["aws_root_ca"], MainApp.config["aws_private_key"], MainApp.config["aws_certificate"])
        MainApp.mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        MainApp.mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
        MainApp.mqtt_client.configureConnectDisconnectTimeout(10)  # 10 sec
        MainApp.mqtt_client.configureMQTTOperationTimeout(5)  # 5 sec
        if not MainApp.mqtt_client.connect():
            raise Exception("Unable to connect to AWS MQTT broke.")

        MainApp.pm25_threshold = float(MainApp.config["device_components"]["pm25_threshold"]) # Use [] operator instead of .get() to throw exception if any
        MainApp.pm10_threshold = float(MainApp.config["device_components"]["pm10_threshold"])

        MainApp.buzzer = Buzzer(5)
        MainApp.buzzer_status = MainApp.config["device_components"]["buzzer"]

        MainApp.telegram_chat_id = MainApp.config["telegram_chat_id"]
        MainApp.telegram_bot =  telepot.Bot(MainApp.config["telegram_bot_token"])
    
    def _pm_sensor(self):
        # Local variables for PM sensor
        seri = serial.Serial("/dev/ttyUSB0")
        lcd = LCD()
        led = LED(16)
        twilio_account_sid = MainApp.config.get("twilio_account_sid")
        twilio_auth_token = MainApp.config.get("twilio_auth_token")
        twilio_my_hp = MainApp.config.get("twilio_my_hp") # Can retrieve from database the different numbers to send sms
        twilio_hp = MainApp.config.get("twilio_hp")
        client = Client(twilio_account_sid, twilio_auth_token)

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

                now = datetime.now()
                
                # Publish AQ data to MQTT channel which will be stored into DB by AWS rule
                payload = {"device_id" : MainApp.device_id, 
                           "timestamp" : datetime.utcnow().isoformat(), 
                           "pm_25" : MainApp.pm_25,
                           "pm_10" : MainApp.pm_10 }
                MainApp.mqtt_client.publish("{}/aq".format(MainApp.device_id), json.dumps(payload), 1)
                
                # Display readings onto console
                print("PM Sensor Thread\t\t {}\t PM 2.5: {:.1f}\t PM 10: {:.1f}".format(now.strftime("%Y-%m-%d %H:%M:%S"), MainApp.pm_25, MainApp.pm_10))
                
                # Both PM2.5 and PM10 within healthy range
                if MainApp.pm_25 <= MainApp.pm25_threshold and MainApp.pm_10 <= MainApp.pm10_threshold:
                    # Display readings onto LCD
                    lcd.text("PM 2.5: {:.1f}".format(MainApp.pm_25), 1)
                    lcd.text("PM 10: {:.1f}".format(MainApp.pm_10), 2)
                    # Turn off LED if it is on
                    if led.is_lit:
                        led.off()
                        # Launch another daemon thread to update LED status in db
                        t = threading.Thread(target=self._update_status, name="update_status", args=("led", "off"), daemon=True)
                        t.start()

                # Either or both PM2.5 and PM10 exceeded healthy range
                else:
                    # Display readings onto LCD
                    lcd.text("PM {}: {:.1f}".format("2.5" if MainApp.pm_25 > MainApp.pm25_threshold else "10", MainApp.pm_25 if MainApp.pm_25 > MainApp.pm25_threshold else MainApp.pm_10), 1) # Priority in displaying PM2.5 value if both unhealthy
                    lcd.text("Alerting NEA!", 2)
                    # Turn on LED if it is off
                    if not led.is_lit:
                        led.on()
                        t = threading.Thread(target=self._update_status, name="update_status", args=("led", "on"), daemon=True)
                        t.start()

                    # Send alerts every 1 hour
                    if next_alert_time < now:
                        camera = None
                        try:
                            # Send SMS
                            sms = "Unhealthy air quality observed at {}.\nPlease investigate!\nPM2.5: {:.1f}\nPM10: {:.1f}".format(MainApp.device_id, MainApp.pm_25, MainApp.pm_10)
                            client.api.account.messages.create(to=twilio_my_hp, from_=twilio_hp, body=sms)

                            # Take photo of factory and upload to S3
                            camera = PiCamera(resolution=(1280,720))
                            sleep(2) # Let camera warm up
                            with BytesIO() as pic_stream: # Save captured image to RAM instead of disk, faster
                                camera.capture(pic_stream, "jpeg")
                                pic_stream.seek(0) # Seek to start of buffer as cursor currently at end. If not, upload_fileobj() later will read 0 bytes. https://stackoverflow.com/questions/53485708/how-the-write-read-and-getvalue-methods-of-python-io-bytesio-work
                                s3 = boto3.client("s3")
                                s3_fn = MainApp.device_id + "_" + secrets.token_hex(8) + ".jpg"
                                # Successful S3 image upload will trigger the AWS Lambda function configured.
                                # The Lambda function sends the image to Rekognition
                                # And saves the device_id, S3 image_name and labels detected in DB
                                s3.upload_fileobj(pic_stream, MainApp.config["aws_s3_bucket"], s3_fn)

                                # Send image taken via telegram - <TO DO> if have time
                        except Exception as e:
                            print(e)
                            print("Failed to perform Unhealthy Alerat opeartions. Retry in an hour.")
                        else:
                            pass
                            # Successfully uploaded to S3 -> publish to MQTT to trigger AWS IoT Rule 
                            # NO NEED ANYMORE! Successful S3 upload above will trigger lambda straight away which saves resources from publish MQTT message
                            #payload = {"aws_s3_bucket" : MainApp.config["aws_s3_bucket"], "s3_fn" : s3_fn}
                            #MainApp.mqtt_client.publish("{}/images".format(MainApp.config["device_id"]), json.dumps(payload), 1)
                        finally:
                            # Add 1 hour to next_alert_time, so will only perform Alert opeartions hourly
                            next_alert_time += timedelta(hours=1)
                            if camera != None: 
                                camera.close() # Always close camera 
                
                sleep(10)
                
            except Exception as e:
                print(e)
                print("PM Sensor Thread - Exception. Recovering...")

    def _update_status(self, component, status):
        try:
            hash_key = MainApp.device_id + "_" + component
            new_status = Status(hash_key)
            new_status.update(actions=[Status.status.set(status)])
        except Exception as e:
            print(e)
            print("Update Status Thread - Exception. Failed to update {} status.".format(component))

    def _update_pm_threshold(self):
        while True:
            try:
                pm25 = Status.get(MainApp.device_id + "_" + "pm25_threshold")
                pm10 = Status.get(MainApp.device_id + "_" + "pm10_threshold")
            except Exception as e:
                print(e)
                print("PM Threshold Update Thread - Exception. Recovering...")
            else:
                MainApp.pm25_threshold = float(pm25.status)
                MainApp.pm10_threshold = float(pm10.status)
                # print("PM Threshold Update Thread\t {}\t Updated PM Thresholds".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            finally:
                sleep(17)
    
    def _update_buzzer(self):
        while True:
            try:
                bs = Status.get(MainApp.device_id + "_" + "buzzer").status # Taking the buzzer status stored on db as the true status as web app can only modify the status in db
                if bs == MainApp.buzzer_status:
                    continue
                # local buzzer status different from the buzzer status on db, update local status
                with MainApp.buzzer_lock:
                    if bs == "on":
                        MainApp.buzzer.on()
                        MainApp.buzzer_status = "on"
                    elif bs == "off":
                        MainApp.buzzer.off()
                        MainApp.buzzer_status = "off"
            except Exception as e:
                print(e)
                print("Buzzer Status Update Thread - Exception. Recovering...")
            finally:
                sleep(5)

    def _telegram_respond(self, msg):
        telegram_chat_id = msg["chat"]["id"]
        command = msg["text"]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("Telegram Bot Thread \t\t {}\t Received command: {}".format(now_str, command))
        try:
            if re.compile(r"on ?(all|%s) ?(sound|buzzer|warning)" % MainApp.device_id, re.IGNORECASE).search(command) != None:
                with MainApp.buzzer_lock:
                    MainApp.buzzer.on()
                    t = threading.Thread(target=self._update_status, name="update_status", args=("buzzer", "on"), daemon=True)
                    t.start()
                    MainApp.buzzer_status = "on"
                MainApp.telegram_bot.sendMessage(telegram_chat_id, "Device ID: {}\nUnhealthy Air Quality Warning Sound Has Been Turned On!".format(MainApp.device_id))
                print("Telegram Bot Thread \t\t {}\t Turned on Buzzer.".format(now_str))

            elif re.compile(r"off ?(all|%s) ?(sound|buzzer|warning)" % MainApp.device_id, re.IGNORECASE).search(command) != None:
                with MainApp.buzzer_lock:
                    MainApp.buzzer.off()
                    t = threading.Thread(target=self._update_status, name="update_status", args=("buzzer", "off"), daemon=True)
                    t.start()
                    MainApp.buzzer_status = "off"
                MainApp.telegram_bot.sendMessage(telegram_chat_id, "Device ID: {}\nUnhealthy Air Quality Warning Sound Has Been Turned Off!".format(MainApp.device_id))
                print("Telegram Bot Thread \t\t {}\t Turned off Buzzer.".format(now_str))

            elif re.compile(r"get ?(all|%s) ?((aq)|(air quality))" % MainApp.device_id, re.IGNORECASE).search(command) != None:
                reply = "Device ID: {}\nCurrent Air Quality:\nPM 2.5: {:.1f}\nPM 10: {:.1f}".format(MainApp.device_id, MainApp.pm_25, MainApp.pm_10)
                MainApp.telegram_bot.sendMessage(telegram_chat_id, reply)
                print("Telegram Bot Thread \t\t {}\t Retrieved Air Quality.".format(now_str))

            elif re.compile(r"get (id|device)s", re.IGNORECASE).search(command) != None:
                reply = "All Device IDs:\n"
                for device in Device.scan():
                    reply += (device.device_id + "\n")
                MainApp.telegram_bot.sendMessage(telegram_chat_id, reply)
                print("Telegram Bot Thread \t\t {}\t Retrieved All Device IDs.".format(now_str))

            else:
                reply = '''Sorry! Invalid Command.\n
"get devices" - Get all the device IDs.
"get <all | device_id> AQ" - Get real-time PM2.5 and PM10 reading from all devices or the device with device ID specified.
"on <all | device_id> buzzer" - Play the warning sound for factories monitored. 
"off <all | device_id> buzzer" - Stop the warning sound.'''
                MainApp.telegram_bot.sendMessage(telegram_chat_id, reply)
        except Exception as e:
            print(e)
    
    def run_pm_sensor(self):
        t = threading.Thread(target=self._pm_sensor, name="pm_sensor")
        t.setDaemon(True) # Launch as daemon thread which will end automatically when main thread ends and does not block main thread
        MainApp.iot_threads.append(t)
        t.start()

    def run_update_pm_threshold(self):
        t = threading.Thread(target=self._update_pm_threshold, name="update_pm_threshold")
        t.setDaemon(True) # Launch as daemon thread which will end automatically when main thread ends and does not block main thread
        MainApp.iot_threads.append(t)
        t.start()           

    def run_update_buzzer(self):
        t = threading.Thread(target=self._update_buzzer, name="update_buzzer")
        t.setDaemon(True) # Launch as daemon thread which will end automatically when main thread ends and does not block main thread
        MainApp.iot_threads.append(t)
        t.start()

    def run_telegram_bot(self):
        t = MessageLoop(MainApp.telegram_bot, self._telegram_respond).run_as_thread()
        # print(t == None)
   