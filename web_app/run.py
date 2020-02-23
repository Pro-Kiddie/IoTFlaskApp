import argparse
from flask_iot_app import app
from flask_iot_app.telegram_bot import TelegramBot

parser = argparse.ArgumentParser(description="Flask Web Server of this Air Quality IoT Application")
parser.add_argument("-d", "--debug", action="store_true", default=False, dest="debug", help="Run application in debug mode.")
parser.add_argument("-l", "--local", action="store_true", default=False, dest="local", help="Make application run on 127.0.0.1. Externally invisible.")
parser.add_argument("-t", "--telegram", action="store_true", default=False, dest="telegram", help="Run Telegram bot component.")
args = parser.parse_args()

# The only purpose of this run is to run our Flask Application in our IoT_CA1 Package
#from flask_iot_app import create_app

# Create database tables if not exists
# db.create_all()

# Create initial admin account as only login page is accessible without login
# Only existing user can create account for other family members
# with open("config.json", "r") as config_file:
#     config = json.load(config_file)
#     email = config.get("admin_email")
#     if not User.query.filter_by(email=email).first(): # Create admin user if does not exists
#         password_hash = bcrypt.generate_password_hash(config.get("admin_password")).decode("utf-8")
#         db.session.add(User(name=config.get("admin_name"), email=email, password=password_hash))
#         db.session.commit()

#app = create_app()
if __name__ == "__main__":
    if args.telegram and args.debug:
        print("\nWarning. Debug mode and telegram bot cannot launch together. Stop launching telegram bot.\n\n")
    if args.telegram and not args.debug: # Cannot launch together with debug mode because debugging will cause this script to run multiple times and telepot MessageLoop only allows one instance.
        bot = TelegramBot()
        bot.run()
    app.run(debug=args.debug, host=None if args.local else "0.0.0.0")

# Dependencies installed while developing this web application
# python3 -m pip install flask
# python3 -m pip install flask-wtf
# python3 -m pip install wtforms
# python3 -m pip install flask-sqlalchemy
# python3 -m pip install flask-bcrypt
# python3 -m pip install flask-login
# python3 -m pip install Pillow
# python3 -m pip install isdangerous #Should be installed together with flask
# python3 -m pip install flask-mail
# python3 -m pip install pymysql
# python3 -m pip install telepot
# python3 -m pip install rpi_lcd
# python3 -m pip install picamera

# # Dependencies for IoT source files
# python3 -m pip install pyserial
# python3 -m pip install twilio
# python3 -m pip install rpi.GPIO
# python3 -m pip install gpiozero

# AWS EC2 Setup Process https://aws.amazon.com/ec2/getting-started/
# Create an EC2 instance (Ubuntu 18 used). Make sure public IP will be assigned. Tick the option when configuring the instance
# Create an role for the EC2 instance. Make sure it has full access to AWS IOT, DynamoDB, S3
# Add a rule to the security group attacked to your instance to allow inbound traffic on port 5000. https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/authorizing-access-to-an-instance.html
# Transfer the web_app to the EC2 instance
# Install the following packages
    # sudo apt-get update
    # sudo apt-get install build-essential libssl-dev libffi-dev
    # sudo apt-get install gcc libpq-dev -y
    # sudo apt-get install python-dev  python-pip -y
    # sudo apt-get install python3-dev python3-pip python3-venv python3-wheel -y
    # pip3 install wheel
# In the web_app directory, create an python3 virtual environment
# Install the the packages in requirements.txt with pip install -r requirements.txt
# Make sure the config.json is filled up properly. E.g. mqtt_client_name and the certs and private keys required by MQTT client is inside the web_app directory.
# Run the web app with python3 run.py -t
# If the Gmail fails to send password reset email due to Google security:
    # Enable allow less secure app http://stackoverflow.com/questions/26852128/smtpauthenticationerror-when-sending-mail-using-gmail-and-python
    # Unlock Captcha to allow your Gmail account from sending location at the AWS instance https://stackoverflow.com/questions/35659172/django-send-mail-from-ec2-via-gmail-gives-smtpauthenticationerror-but-works
