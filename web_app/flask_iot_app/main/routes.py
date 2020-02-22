from datetime import datetime, timezone
from flask import Blueprint, render_template, jsonify, flash, Markup
from flask_login import login_required
# from flask_iot_app.iot.models import ImageCapture
from flask_iot_app.models import AQImage, Status
from flask_iot_app.iot.forms import UpdateThresholdForm

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
    hi = Markup('''{
                        name:"Admiralty",
                        value:[103.7948,1.4954,90]
                    },
                    {
                        name:"Sembawang",
                        value:[103.7948,1.4554,10]
                    },
                    {
                        name:"Woodlands",
                        value:[103.7948,1.4154,10]
                    }''')
    return render_template('index.html',hi=hi)#, captures=captures, timezone=timezone) # Must return the page. Flask will render what your this function returns for the URL specified

@main.route("/device/<device_id>", methods=['GET', 'POST']) # Function Decorators provided by Flask -> Takes in our function and serve it when the route is accessed
@login_required 
def device(device_id):
    # captures = ImageCapture.query.order_by(ImageCapture.id.desc()).limit(4).all()
    # Retrieve records about the last 5 image taken when AQ thresholds are exceeded for that device
    last_5_images = AQImage.query(device_id, scan_index_forward=False, limit=5)
    image_dict = {}
    timestamp_dict = {}
    for image in last_5_images:
        label_dict = {}
        for label in image.labels:
            label_dict[label] = round(image.labels[label], 2)
        if(not label_dict):
            label_dict["None"] = 0
        image_dict[image.fn] = label_dict
        timestamp_dict[image.fn] = image.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Retrieve current PM threshold values for the device
    pm25Threshold = Status.get(device_id + "_pm25Threshold").status
    pm10Threshold = Status.get(device_id + "_pm10Threshold").status

    # Create the form for updating PM thresholds for the device which will be rendered in the model
    form = UpdateThresholdForm(device_id=device_id)
    if form.validate_on_submit():
        new_pm25 = Status(form.device_id.data + "_pm25Threshold")
        new_pm10 = Status(form.device_id.data + "_pm10Threshold")
        new_pm25.update(actions=[Status.status.set(str(round(float(form.pm_25.data), 1)))])
        new_pm10.update(actions=[Status.status.set(str(round(float(form.pm_10.data), 1)))])
        flash("PM 2.5 and PM 10 thresholds updated.", "success")
    return render_template('dashboard.html', device_id=device_id, image_dict=image_dict, timestamp_dict=timestamp_dict, pm25Threshold=pm25Threshold, pm10Threshold=pm10Threshold, form=form)#, captures=captures, timezone=timezone) # Must return the page. Flask will render what your this function returns for the URL specified

# Door Camera Page
# @main.route("/door_camera")
# @login_required
# def door_camera():
    # Retrieve the last 4 image captured at door step
    #captures = ImageCapture.query.order_by(ImageCapture.id.desc()).limit(4).all()
    #return render_template("door_camera.html", captures=captures, timezone=timezone)
    # pass