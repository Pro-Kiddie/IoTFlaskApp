# SDS011's USB device found successfull as shown by dmesg but /dev/ttyUSB0 not loaded -> No driver for its USB device
# It needs ch341 kernel module as driver
# Needs to install the latest linux kernel headers to install ch341 -> sudo apt-get install raspberrypi-kernel-headers
# git clone https://github.com/skyrocknroll/CH341SER_LINUX.git
# Install the driver -> sudo make

import serial, time, sys, signal, json
from datetime import datetime, timedelta
from flask_iot_app import db, led
from flask_iot_app.iot.models import AirQuality
from twilio.rest import Client
from rpi_lcd import LCD


# Export all configurations as env variables
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Twillio API account information (Should store in a JSON file and read from there)
twilio_account_sid = config.get("twilio_account_sid")
twilio_auth_token = config.get("twilio_auth_token")
twilio_my_hp = config.get("twilio_my_hp")
twilio_hp = config.get("twilio_hp")
client = Client(twilio_account_sid, twilio_auth_token)

# Attach handler for Ctrl+C signal to end the program
# signal.signal(signal.SIGINT, lambda n, f: sys.exit())

try:
    seri = serial.Serial("/dev/ttyUSB0")
except serial.SerialException:
    print("SDS011 USB Connection is not detected.")
    sys.exit()
    
lcd = LCD()
next_sms_time = datetime.now()
while True:
    try:
        data = list()
        # Read data from SDS011 which returns in 10 bytes at a time
        for i in range(10):
            byte = seri.read()
            data.append(byte)
        
        # Get the PM2.5 data
        # pm_25 = int.from_bytes(b"".join(data[2:4]), byteorder="little") / 10
        pm_25 = (int.from_bytes(data[3], byteorder="little") * 256 + int.from_bytes(data[2], byteorder="little")) / 10
        # Get the PM10 data
        pm_10 = int.from_bytes(b"".join(data[4:6]), byteorder="little") / 10

        # Display readings onto LCD and console
        # When next_sms_time > datetime.now(), means sms sent and wear mask warning displayed on LCD. Keep the warning for an hour
        if (pm_25 <= 12 and pm_10 <= 50) or next_sms_time < datetime.now():
            lcd.text("PM 2.5: {:.1f}".format(pm_25), 1)
            lcd.text("PM 10: {:.1f}".format(pm_10), 2)
        print("PM 2.5: {:.1f} ug/m^3".format(pm_25))
        print("PM 10: {:.1f} ug/m^3".format(pm_10))

        # Write data to database
        db.session.add(AirQuality(pm_25=pm_25, pm_10=pm_10))
        db.session.commit()

        # If PM 2.5 and PM 10 reached unhealthy range, turn on LED as warning light
        if (pm_25 > 12 or pm_10 > 50):
            if not led.is_lit:
                led.on()
            lcd.text("PM {}: {:.1f}".format("2.5" if pm_25 > 12 else "10", pm_25 if pm_25 > 12 else pm_10), 1)
            lcd.text("Wear A Mask Now!", 2)
            if next_sms_time < datetime.now():
                sms = "\nCurrent air quality has reached unhealthy level. Please wear a mask!\nPM2.5: {:.1f}\nPM10: {:.1f}".format(pm_25, pm_10)
                try:
                    message = client.api.account.messages.create(to=twilio_my_hp, from_=twilio_hp, body=sms)
                except:
                    print("Failed to send sms alert. Please check your Internet connection or Twilio API keys.")
                else:
                    # message sent successful, add 1 hour to next_sms_time, so will only send 1 sms in an hour
                    next_sms_time += timedelta(hours=1)
        else:
            if led.is_lit:
                led.off()

        time.sleep(10)
    except KeyboardInterrupt:
        print("***********************************************************")
        print("Ending reading PM Sensor values.")
        sys.exit()
    except:
        print("Something went wrong. Recovering...")




    