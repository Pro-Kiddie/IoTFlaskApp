import telepot, re, os, picamera, sys, json
from time import sleep
from datetime import datetime
from telepot.loop import MessageLoop
from gpiozero import MotionSensor
from time import sleep
from io import BytesIO
from PIL import Image
from flask import current_app
from flask_iot_app import buzzer, app, db
from flask_iot_app.iot.models import AirQuality, ImageCapture
from flask_iot_app.iot.camera_pi import Camera

# Export all configurations as env variables
with open("config.json", "r") as config_file:
    config = json.load(config_file)

telegram_bot_token = config.get("telegram_bot_token") # Should read from a file for best practice
# To get telegram_chat_id, send a message to your bot in Telegram
# In python interactive shell:
# import telepot
# bot = telepot.Bot("TOKEN")
# bot.getUpdates()
telegram_chat_id = config.get("telegram_chat_id") 
bot = telepot.Bot(telegram_bot_token)

# Air Quality Section:
# Handler for incoming commands
def respondCommands(msg):
    telegram_chat_id = msg["chat"]["id"]
    command = msg["text"]

    print("{}: Received command: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), command))

    if re.compile(r"(on ?sound)|(on ?buzzer)|(on ?warning)", re.IGNORECASE).search(command) != None:
        buzzer.on()
        bot.sendMessage(telegram_chat_id, "Unhealthy Air Quality Warning Sound Has Been Turned On!")
        print("{}: Turned on Buzzer.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    elif re.compile(r"(off ?sound)|(off ?buzzer)|(off ?warning)", re.IGNORECASE).search(command) != None:
        buzzer.off()
        bot.sendMessage(telegram_chat_id, "Unhealthy Air Quality Warning Sound Has Been Turned Off!")
        print("{}: Turned off Buzzer.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    elif re.compile(r"(get ?aq)|(aq)|(air quality)", re.IGNORECASE).search(command) != None:
        last_rec = AirQuality.query.order_by(AirQuality.id.desc()).first()
        reply = "Current Air Quality:\nPM 2.5: {:.1f}\nPM 10: {:.1f}".format(last_rec.pm_25, last_rec.pm_10)
        bot.sendMessage(telegram_chat_id, reply)
        print("{}: Retrieved Air Quality.".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    else:
        reply = '''Sorry! Invalid Command.
Type "get AQ" to get the latest PM2.5 and PM10 reading.
Type "on buzzer" to play a warning sound for family to wear a mask. 
Type "off buzzer" to stop the warning sound.'''
        bot.sendMessage(telegram_chat_id, reply)

MessageLoop(bot, respondCommands).run_as_thread()
print("***********************************************************")
print("Starting Image Capture at Door Mechanism and Telegram Bot ...")
print("Bot Listening for Commands...")

# Motion Sensor & Image Capture Section
motion = MotionSensor(13, sample_rate=6, queue_len=1)

while True:
    try:
        motion.wait_for_motion()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{}: Motion Detected at Door Step.".format(now))
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
        print("{}: Photo Taken and Saved at {}".format(now, os.path.join(path, fn)))
        # Add Image Capture event to database
        img = ImageCapture(image=fn)
        db.session.add(img)
        db.session.commit()
        # Send image to user via Telegram
        bot.sendPhoto(telegram_chat_id, BytesIO(pic), caption="{}: Motion detected at door.".format(now))
        print("{}: Photo Captured Sent to user".format(now))
        sleep(30)
        motion.wait_for_no_motion()
    except KeyboardInterrupt:
        print("***********************************************************")
        print("Ending Image Capture at Door Mechanism and Telegram Bot")
        sys.exit()
    except:
        print("Something went wrong. Recovering program.")
        sleep(30)
    

