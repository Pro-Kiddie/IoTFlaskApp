import json, threading, serial, re, telepot, os, sys, argparse
from time import sleep
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from flask import current_app
from flask_iot_app import db, led, buzzer, app
from flask_iot_app.iot.models import AirQuality, ImageCapture
from twilio.rest import Client
from telepot.loop import MessageLoop
from rpi_lcd import LCD
from gpiozero import MotionSensor
from flask_iot_app.iot.camera_pi import Camera


class IoT():
    # Shared among different threads
    database = None
    config = None
    iot_threads = []
    instance_created = False

    def __init__(self, config_file, pm_25_threshold, pm_10_threshold):
        # Only allow one instance of this class
        if IoT.instance_created:
            raise Exception("Only one instance is allowed for this class.")
        IoT.instance_created = True

        # Load config file
        with open(config_file, "r") as cf:
            IoT.config = json.load(cf)

        # Initializae database
        IoT.database = db

        # Initialize variables for PM sensor
        # Initialize here instead in _pm_sensor thread method as if exception the thread will die.
        self.seri = serial.Serial("/dev/ttyUSB0")
        self.lcd = LCD()
        self.led = led
        self.pm_25_threshold = pm_25_threshold
        self.pm_10_threshold = pm_10_threshold

        # Initialize variables for door_bot
        self.buzzer = buzzer
        self.telegram_chat_id = IoT.config.get("telegram_chat_id") 
        self.bot = telepot.Bot(IoT.config.get("telegram_bot_token")) # Shared between threads
        self.motion = MotionSensor(13, sample_rate=6, queue_len=1)

    def _pm_sensor(self):
        # Twillio API account information (Should store in a JSON file and read from there)
        twilio_account_sid = IoT.config.get("twilio_account_sid")
        twilio_auth_token = IoT.config.get("twilio_auth_token")
        # Can retrieve from database the different numbers to send sms
        twilio_my_hp = IoT.config.get("twilio_my_hp")
        twilio_hp = IoT.config.get("twilio_hp")
        client = Client(twilio_account_sid, twilio_auth_token)

        next_sms_time = datetime.now()

        while True:
            try:
                data = list()
                # Read data from SDS011 which returns in 10 bytes at a time
                for _ in range(10):
                    byte = self.seri.read()
                    data.append(byte)

                # Get the PM2.5 data
                # pm_25 = int.from_bytes(b"".join(data[2:4]), byteorder="little") / 10
                pm_25 = (int.from_bytes(data[3], byteorder="little") *
                         256 + int.from_bytes(data[2], byteorder="little")) / 10
                # Get the PM10 data
                pm_10 = int.from_bytes(
                    b"".join(data[4:6]), byteorder="little") / 10

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Display readings onto LCD and console
                # When next_sms_time > datetime.now(), means sms sent and wear mask warning displayed on LCD. Keep the warning for an hour
                if (pm_25 <= self.pm_25_threshold and pm_10 <= self.pm_10_threshold) or next_sms_time < datetime.now():
                    self.lcd.text("PM 2.5: {:.1f}".format(pm_25), 1)
                    self.lcd.text("PM 10: {:.1f}".format(pm_10), 2)
                print("PM Sensor Thread \t {}: PM 2.5: {:.1f}".format(now, pm_25))
                print("PM Sensor Thread \t {}: PM 10: {:.1f}".format(now, pm_10))

                # Write data to database
                IoT.database.session.add(AirQuality(pm_25=pm_25, pm_10=pm_10))
                IoT.database.session.commit()

                # If PM 2.5 and PM 10 reached unhealthy range, turn on LED as warning light
                if (pm_25 > self.pm_25_threshold or pm_10 > self.pm_10_threshold):
                    if not self.led.is_lit:
                        self.led.on()
                    self.lcd.text("PM {}: {:.1f}".format("2.5" if pm_25 >
                                                         self.pm_25_threshold else "10", pm_25 if pm_25 > self.pm_25_threshold else pm_10), 1)
                    self.lcd.text("Wear A Mask Now!", 2)
                    if next_sms_time < datetime.now():
                        sms = "\nCurrent air quality has reached unhealthy level. Please wear a mask!\nPM2.5: {:.1f}\nPM10: {:.1f}".format(
                            pm_25, pm_10)
                        try:
                            client.api.account.messages.create(to=twilio_my_hp, from_=twilio_hp, body=sms)
                        except:
                            print(
                                "Failed to send sms alert. Please check your Internet connection or Twilio API keys.")
                        else:
                            # message sent successful, add 1 hour to next_sms_time, so will only send 1 sms in an hour
                            next_sms_time += timedelta(hours=1)
                else:
                    if self.led.is_lit:
                        self.led.off()
                sleep(10)
            except Exception as e:
                print(e)
                print("PM Sensor Thread - Exception. Recovering...")

    def _door_bot(self):
        MessageLoop(self.bot, self._respondCommands).run_as_thread()

        while True:
            try:
                self.motion.wait_for_motion()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("Door Bot Thread \t {}: Motion Detected at Door Step.".format(now))
                # Get image from camera
                camera = Camera()
                sleep(2)
                pic = camera.get_frame()
                if len(pic) == 0 or pic == None:
                    sleep(5)
                    continue
                # Save image 
                fn = "_".join(now.split(" ")) + ".jpg"
                with app.app_context():
                    path = os.path.join(current_app.root_path, "static/captured_img") 
                im = Image.open(BytesIO(pic))
                im.save(os.path.join(path, fn))
                print("Door Bot Thread \t {}: Photo Taken and Saved at {}".format(now, os.path.join(path, fn)))
                # Add Image Capture event to database
                img = ImageCapture(image=fn)
                IoT.database.session.add(img)
                IoT.database.session.commit()
                # Send image to user via Telegram
                self.bot.sendPhoto(self.telegram_chat_id, BytesIO(pic), caption="{}: Motion detected at door.".format(now))
                print("Door Bot Thread \t {}: Photo Captured Sent to user".format(now))
                sleep(30)
                self.motion.wait_for_no_motion()
            except Exception as e:
                print(e)
                print("Door Bot Thread - Exception. Recovering ...")
                sleep(30)
    

    def _respondCommands(self, msg):
        telegram_chat_id = msg["chat"]["id"]
        command = msg["text"]

        print("AQ Bot Thread \t\t {}: Received command: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), command))

        if re.compile(r"(on ?sound)|(on ?buzzer)|(on ?warning)", re.IGNORECASE).search(command) != None:
            self.buzzer.on()
            self.bot.sendMessage(telegram_chat_id, "Unhealthy Air Quality Warning Sound Has Been Turned On!")
            print("AQ Bot Thread \t\t {}: Turned on Buzzer.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        elif re.compile(r"(off ?sound)|(off ?buzzer)|(off ?warning)", re.IGNORECASE).search(command) != None:
            self.buzzer.off()
            self.bot.sendMessage(telegram_chat_id, "Unhealthy Air Quality Warning Sound Has Been Turned Off!")
            print("AQ Bot Thread \t\t {}: Turned off Buzzer.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        elif re.compile(r"(get ?aq)|(aq)|(air quality)", re.IGNORECASE).search(command) != None:
            last_rec = AirQuality.query.order_by(AirQuality.id.desc()).first()
            reply = "Current Air Quality:\nPM 2.5: {:.1f}\nPM 10: {:.1f}".format(last_rec.pm_25, last_rec.pm_10)
            self.bot.sendMessage(telegram_chat_id, reply)
            print("AQ Bot Thread \t\t {}: Retrieved Air Quality.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        else:
            reply = '''Sorry! Invalid Command.
Type "get AQ" to get the latest PM2.5 and PM10 reading.
Type "on buzzer" to play a warning sound for family to wear a mask. 
Type "off buzzer" to stop the warning sound.'''
            self.bot.sendMessage(telegram_chat_id, reply)

    def run_pm_sensor(self):
        t = threading.Thread(target=self._pm_sensor, name="pm_sensor")
        t.setDaemon(True) # Launch as daemon thread which will end automatically when main thread ends
        IoT.iot_threads.append(t)
        t.start()

    def run_door_bot(self):
        t = threading.Thread(target=self._door_bot, name="door_bot")
        t.setDaemon(True)
        IoT.iot_threads.append(t)
        t.start()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IoT Component of this IoT Application")
    parser.add_argument('-pm25', dest="pm_25_threshold" ,type=int, default=12, metavar="value", help="PM 2.5 Threshold to On LED and Send SMS Alert.")
    parser.add_argument('-pm10', dest="pm_10_threshold" ,type=int, default=50, metavar="value", help="PM 10 Threshold to On LED and Send SMS Alert.")
    args = parser.parse_args()

    iot = IoT(config_file="config.json", pm_25_threshold=args.pm_25_threshold, pm_10_threshold=args.pm_10_threshold)
    iot.run_pm_sensor()
    iot.run_door_bot()
    try:
        while True: # Keep the main thread running
            for t in IoT.iot_threads: # Loop through the different threads
                if not t.isAlive(): # If any is not alive, try to restart the thread
                    if t.getName() == "pm_sensor":
                        iot.run_pm_sensor()
                    elif t.getName() == "door_bot":
                        iot.run_door_bot()
                    IoT.iot_threads.remove(t)
            t.join(5)
    except KeyboardInterrupt:
        print("Ending IoT Component of this IoT Flask Web Application")
