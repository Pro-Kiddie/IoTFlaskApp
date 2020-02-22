import secrets # Generate random filename for uploaded picture to prevent collision
import os, botocore
from io import BytesIO
from PIL import Image # Scale down the image uploaded

from flask_iot_app import mail
from flask import url_for, current_app
from flask_mail import Message # Class to craft an email message

# def Save_Picture(form_picture, current_image):
#     # Generate random name for the new profile picture 
#     random_hex_fn = secrets.token_hex(8) # random 8 bytes in hex as new file name to prevent collision
#     _, f_ext = os.path.splitext(form_picture.filename)
#     picture_new_fn = random_hex_fn + f_ext
#     # Resize the profile picture
#     im = Image.open(form_picture)
#     output_size = (250, 250)
#     im.thumbnail(output_size)
#     buffer = BytesIO()
#     im.save(buffer, "JPEG")
#     buffer.seek(0)

#     bucket = s3.Bucket(current_app.config["aws_s3_bucket"])
#     if current_image == "default.jpg": # User never upload profile pic before
#         bucket.upload_fileobj(buffer, picture_new_fn)
#     else: # User does upload before
#         curr_img_on_s3 = s3.Object(current_app.config["aws_s3_bucket"], current_image)
#         try:
#             curr_img_on_s3.load() # check if current pic exists
#         except botocore.exceptions.ClientError as e:
#             if e.response['Error']['Code'] == "404":
#                 # The object does not exist.
#                 bucket.upload_fileobj(buffer, picture_new_fn)
#             else:
#                 # Something else has gone wrong.
#                 print("Something wrong happened when checking if profile pic already exists on AWS S3.")
#         else:
#             # The object does exist. Delete the current profile pic
#             curr_img_on_s3.delete()
#             # Upload the new profile pic
#             bucket.upload_fileobj(buffer, picture_new_fn)
#     return picture_new_fn

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