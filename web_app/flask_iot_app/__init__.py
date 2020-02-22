# This is the special file (__init__.py) should be created so Python knows this directory is a Python Package
# Turning our Flask application directory into a Python Package

# This is the file that Python runs first to initialize different component in this Python Package to bring the different .py files tgt
# For this Flask Package, should do all the Flask application initialization/configuration here

import os
from flask import Flask
# Default Flask template_folder="templates" in app root folder -> Customize it by Flask(__name__, template_folder=template_dir)
# Default Flask static_folder="static" to store all other files such as CSS, Javascript, pictures and etc
working_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(working_dir, "html_templates") 
# Default static files (e.g. CSS & Javascript files) should be placed inside a folder call "static"; static_folder=static


# Create Flask Controller Instance
app = Flask(__name__) # __XXX__ special variables in Python, __name__ is the file name of this script

from flask_iot_app.config import Config # Import the config class with app's configuration to initalize app
app.config.from_object(Config) # Load config class with all configurations 

# https://flask-sqlalchemy.palletsprojects.com/en/2.x/
# SQLAlchamy Package - Object Relation Mapper (ORM) 
# Allows programmers to access databases in an object-oriented way
# Can access to different databases without changing the Python code, just need to change the database URI
# from flask_sqlalchemy import SQLAlchemy
# Create SQLAlchemy database instance for this whole application
# db = SQLAlchemy(app) # The class take in an Flask instance and look for the "SQLALCHMEY_DATABASE_URI" parameter value


# falsk_bcrypt is a wrapper library around the original bcrypt library
# https://flask-bcrypt.readthedocs.io/en/0.7.1/
# Used to hash password and store in password
# Automatically uses different salt value each time a password hash is generated
# By default hash password up to maximum 72 bytes
from flask_bcrypt import Bcrypt
# Bcrypt object for this flask app for hashing and checking password logic
bcrypt = Bcrypt(app)


# https://flask-login.readthedocs.io/en/latest/#how-it-works
# Library to manager user logins
# Works by storing the unique ID of a user in the user's session when the user logins
# LoginManager expects certain properties/methods (e.g. is_authenticated, is_alive) implemented in your User Model
# You must tell LoginManager a function which will load your user model by its unique ID using a @.user_load decorator
from flask_login import LoginManager
# flask_login LoginManager Object
loginManager = LoginManager(app)
loginManager.login_view = 'users.Login' # for all routes that require login, if not login, will be redirected to "users.Login" view ("Login is the function name of that displays login page")
loginManager.login_message_category = 'info' # bootstrap info class

# loginManager.refresh_view = 'users.Login'
# loginManager.needs_refresh_message = (u"Session timeout. Please relogin.")
# loginManager.needs_refresh_message_category = 'warning'
# Flask sessions expire once you close the browser unless you have a permanent session set. Do not close browser, do not expire.
# app.permanent_session_lifetime = timedelta(minutes=5)


# https://pythonhosted.org/Flask-Mail/
# Library to send emails with the server, account you set
# Send emails on behalf of your Flask app to achieve functionalities such as reset password emails
from flask_mail import Mail
# flask_mail object for sending emails
# Configurations like email server, port, username and password must be set
mail = Mail(app)


# Configure App's custom JSON encoder which will be used by flask.jsonify()
# https://web.archive.org/web/20190128010149/http://flask.pocoo.org/snippets/119/
from flask_iot_app.iot.utils import CustomEncoder
app.json_encoder = CustomEncoder

# Initialize LED object here as certain routes need to import the LED object to perform tasks such as checking its status
# Other IoT .py files can also import this object
# from gpiozero import LED, Buzzer
# led = LED(16)
# buzzer = Buzzer(5)

# AWS resources
import boto3
s3 = boto3.resource("s3")

# Run Flask app from a function
# Advantages: Create different instances of the same app with different configurations
# Create the different flask plugins (flask-bcrypt, flask-mail, flask-login) instance outside, so that they do not initially get bound to a specific app, and contain its settings
# They can be reused by other instances of the app
#def create_app(config_class=Config):

    # Now ties the different plugins with the application instance
    #db.init_app(app)
    #bcrypt.init_app(app)
    #loginManager.init_app(app)
    #mail.init_app(app)

    # MUST initialize the routes which is the most important part of our Flask application
    # from flask_iot_app import routes 
    # Cannot put this above, especially above "app=Flask()" because routes.py is importing app and if this is above that, results in Circular Import!

# After turning this application into a Blueprint structure, do not import routes like above but register the routes with this app
from flask_iot_app.users.routes import users
from flask_iot_app.main.routes import main
from flask_iot_app.iot.routes import iot
from flask_iot_app.errors.handlers import errors
from flask_iot_app.models import Device

app.register_blueprint(users)
app.register_blueprint(main)
app.register_blueprint(iot)
app.register_blueprint(errors)

#Global Context Processor to retrieve Device IDs
@app.context_processor
def utility_processor():
    def get_device_ids():
        device_ids = []
        query = Device.scan()
        for device in query:
            device_ids.append(device.device_id)
        return device_ids
    return dict(get_device_ids = get_device_ids)

#    return app

# Flask by default uses Jinja2 Template Engine 
'''
{%....%} are for statements
{{....}} are expressions used to print to template output
{#....#} are for comments which are not included in the template output
#....## are used as line statements
'''
