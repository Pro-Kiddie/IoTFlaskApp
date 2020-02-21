import argparse, os, json
from flask_iot_app import app, bcrypt#, db
from flask_iot_app.models import User

parser = argparse.ArgumentParser(description="Flask Web Server of this IoT Application")
parser.add_argument("-d", "--debug", action="store_true", default=False, dest="debug", help="Run application in debug mode.")
parser.add_argument("-l", "--local", action="store_true", default=False, dest="local", help="Make application run on 127.0.0.1. Externally invisible.")
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