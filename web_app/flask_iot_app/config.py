import json
from flask_iot_app import app

with open(app.root_path + "/../config_mine.json", "r") as config_file:
    config = json.load(config_file)

# Store all the flask app configurations in a class
# The class object can be passed into flask app when initializing
# Class object is easier to maintain and can do things like inheritance
# Best practice is to store sensitive configurations in ENVIRONMENT VARIABLES and read using os.environ.get("KEY")

class Config:
    # config attribute (subclass of dict) of the Flask object holds the configuration values for this app (app.config[KEY] = VALUE)
    # This is how to set configurations under the parameter name you specified or Builtin Configuration Values

    # SECRETKEY is a Builtin Configuration Value which will be used for securely signing the session cookie and can be used for any other security related needs by extensions or your application
    # Should be a long random string you generated. For production do not, store in source code
    SECRET_KEY = config.get("SECRET_KEY") # Generated using secret library

    # Specify the database URI this app is going to use. Using SQLite for now
    SQLALCHEMY_DATABASE_URI = config.get("SQLALCHEMY_DATABASE_URI") #  SQLAlchemy is going to load driver for the database according to the URL
    # SQLite is a lightweight database that is going to store the database in a FILE called the "site.db" relative to current directory

    # flask_mail is configured through the standard Flask.config[]
    MAIL_SERVER = "smtp.googlemail.com" # Can be changed to other mail server besides Gmail
    MAIL_PORT = "587"
    MAIL_USE_TLS = True
    MAIL_USERNAME = config.get("MAIL_USERNAME") #os.environ.get("EMAIL_USER") # Should setup the environment variables before running the app
    MAIL_PASSWORD = config.get("MAIL_PASSWORD") #os.environ.get("EMAIL_PASS") # Can be done in run.py? Configure its permissions properly

    # AWS resources
    AWS_HOST = config.get("aws_host")
    AWS_ROOT_CA = config.get("aws_root_ca")
    AWS_CERTIFICATE = config.get("aws_certificate")
    AWS_PRIVATE_KEY = config.get("aws_private_key")
    AWS_S3_BUCKET = config.get("aws_s3_bucket")
    MQTT_CLIENT_NAME = config.get("mqtt_client_name")
