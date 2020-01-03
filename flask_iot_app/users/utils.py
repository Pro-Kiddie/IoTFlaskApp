import secrets # Generate random filename for uploaded picture to prevent collision
import os
from PIL import Image # Scale down the  image uploaded

from flask_iot_app import mail
from flask import url_for, current_app
from flask_mail import Message # Class to craft an email message

def Save_Picture(form_picture, current_image):
    # delete the original image of user unless it is default.jpg
    if current_image != "default.jpg" and os.path.exists(os.path.join(current_app.root_path, "static/profile_pics", current_image)): # remove original image_file if it is not default.jpg
        os.remove(os.path.join(current_app.root_path, "static/profile_pics", current_image))

    random_hex_fn = secrets.token_hex(8) # random 8 bytes in hex as new file name to prevent collision
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_new_fn = random_hex_fn + f_ext
    # app.root_path the root directory which the app is running
    picture_path = os.path.join(current_app.root_path, "static/profile_pics", picture_new_fn)

    # resize the image uploaded to smaller image for space efficiency
    output_size = (250, 250)
    im = Image.open(form_picture)
    im.thumbnail(output_size)
    # save the pic uploaded at the desired location with new random name
    im.save(picture_path)
    return picture_new_fn


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message("SmartHome - Password Reset Request", sender="noreply.demo.com", recipients=[user.email]) # subject, sender, recipients
    msg.body = """
    To reset your password, visit the following link:
    
    {}

    If you did not make this request then simply ignore this email.
    """.format(url_for("users.Reset_Password", token=token, _external=True)) #_external so full URL is generated but not relative URLs
    mail.send(msg)