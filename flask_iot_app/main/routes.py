from datetime import datetime, timezone
from flask import Blueprint, render_template
from flask_login import login_required
# from flask_iot_app.iot.models import ImageCapture
from flask_iot_app.models import AQImage

# OTHER KNOWNLEDGE
# If the specific row does not exists in database, returns HTTP code 404 with flask's default page for that code 
# Model.query.getor404(post_id)

# Dynamic URL
# How to you specify an dynamic URL which is compulsory -> Depending on the dynamic URL render different content
# This is different from parameters in GET request URL. Those are optional which retrieved by requests.args.get("parameter_name")
# Where as dynamic URL portion /<int:post_id> is a must have
# @app.route("/post/<int:post_id>") # Can specify the type for the dynamic portion of the URL to be int or string
# def post(post_id):
# for dynamic URL, url_for("post", post_id=post.id ) will produce "http://<server>/post/<post_id>"

# GET URL with Parameters
# How do you craft an GET url that requires parameters 
# @app.route("/post") 
# def post():
# url_for("post", post_id=post.id ) will produce "http://<server>post?post_id=<post_id> 

# Use url_for to join different parts of Dynamic URL
# url_for("Reset_Password", token=token) # http://<server>/reset_password/token

# If the request made by a user is illegal, can abort the request can return an built-in flask error page
# from flask import abort 
# abort(403) #Built-in error page with error code 403 - meaning forbidden

main = Blueprint("main", __name__)

# Pages
# Air Quality Page
@main.route("/home") # Function Decorators provided by Flask -> Takes in our function and serve it when the route is accessed
@login_required 
def Home():
    # captures = ImageCapture.query.order_by(ImageCapture.id.desc()).limit(4).all()
    return render_template('index.html')#, captures=captures, timezone=timezone) # Must return the page. Flask will render what your this function returns for the URL specified

# Door Camera Page
@main.route("/door_camera")
@login_required
def door_camera():
    # Retrieve the last 4 image captured at door step
    #captures = ImageCapture.query.order_by(ImageCapture.id.desc()).limit(4).all()
    #return render_template("door_camera.html", captures=captures, timezone=timezone)
    pass