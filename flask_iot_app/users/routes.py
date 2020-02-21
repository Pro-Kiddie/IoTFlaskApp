 # Represents a blueprint, a collection of routes and other app-related functions that can be REGISTERED on a real application later.
 # Easier to maintain for big flask applications rather than a single huge routes.py
from flask import Blueprint

from flask import render_template
 # url_for() creates a URL a resource (directory, function, folder ...) to prevent the overhead of having to change URLs throughout an application, if we change a particular route
 # Good to use it as for almost all "href=URL" across the web app
from flask import url_for # Now this function available throughout the Flask Web Server -> Can be assessed from Jinja block {% %} in frontend
from flask import flash # A quick way provided by Flask to send a message to next request! In java, it was request.setAttribute()
from flask import redirect # Redirect a HTTP request to another URL
from flask import request # to get the HTTP request object to retrieve parameters

from flask_iot_app import bcrypt, mail#, db
# from flask_iot_app.models import User, Post # Use from "flask_iot_app1.models" instead of "from models" because clearer it is importing from our own package
from flask_iot_app.models import User

from flask_iot_app.users.forms import CreateAccountForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm # Forms Class created using wt form library in form.py

from flask_login import login_user # method from flask_login library to login a user. Attach the user object to user's session?
from flask_login import current_user # object in flask_login library that stores the currently login user in the session
from flask_login import logout_user
from flask_login import login_required # function decorator to routes meaning those routes can only be visited if user is login

from flask_iot_app.users.utils import send_reset_email, Save_Picture # Customize function written in utils.py

users = Blueprint("users", __name__)

@users.route("/createAccount", methods=['GET', 'POST'])
@login_required
def Create_Account():
    form = CreateAccountForm()
    if form.validate_on_submit():
        # Generate hash for the password validated
        hashed_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # Create the user object with out model
        user = User(form.email.data, name=form.name.data, password=hashed_pass)
        # Store in database
        user.save()
        flash("Account is created. He or she is able to login now.", "success")
        return redirect(url_for("main.Home")) # url_for("Blueprint_name.route_under_that_blueprint")
    else:
        return render_template("createAccount.html", form=form)

        
@users.route("/", methods=["GET", "POST"]) 
@users.route("/login", methods=["GET", "POST"]) # How you make this URL supports POST Request
def Login():
    if current_user.is_authenticated:
        return redirect(url_for("main.Home"))
    form = LoginForm()
    if form.validate_on_submit(): # All fields of the form passed all the validators specified in forms.py
        # Authentication with database 
        user = None
        try:
            user = User.get(form.email.data)
        except:
            pass
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # flask_login library's method to login a user, probably retrieve the user and attach the user to the session
            login_user(user, remember=form.remember.data)
            flash("Welcome {}!".format(user.name), "success") # "success" is the category of the message which can be useful. E.g. bootstrap class value when displaying this flash message
            next_page = request.args.get("next") # request.args. is a dictionary. Use dict.get(key) which returns None if does not exist instead of [] which throws exception
            return redirect(next_page) if next_page else redirect(url_for('main.Home')) # Redirect the user back to homepage after successful login
        else:
            flash("Login unsuccessful. Strangers are not welcomed!", "danger")
    # If the form did not pass the validators, then the same login.html will be rendered but now form.<field>.errors will be set
    return render_template("login_new.html", title="AQ Monitoring", form=form)

@users.route("/logout")
@login_required
def Logout():
    logout_user()
    return redirect(url_for("users.Login"))


@users.route("/account", methods=["GET", "POST"])
@login_required # Can just do this instead of the 1st 3 lines in all routes that require login, but must specify in __init__.py the login view to redirect user to
# After flask_login redirect the user to the login view after trying to access /account without login, it will make a HTTP GET request to /login?next=account with a next parameter.
# Can specify in Login() to redirect the user back to the page that they were trying to after login instead all go back to homepage
def Account():
    # if not current_user.is_authenticated:
    #     flash("Please login first.", "danger")
    #     return redirect(url_for("Login"))
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            #print("Picture uploaded!")
            picture_file = Save_Picture(form.picture.data, current_user.image_file)
            current_user.update(actions=[User.image_file.set(picture_file)])
            # current_user.image_file = picture_file
        # Flask Login's current_user can be used to obtain the user object that represents the client of the request. 
        # The value of this variable can be a user object from the database (which Flask-Login reads through the user_loader callback)
        # or a special anonymous user object if the user did not log in yet.
        current_user.update(actions=[
            #User.email.set(form.email.data),
            User.name.set(form.name.data)])
        current_user.refresh() # Get updates from database so local User object's attributes are in sync #https://pynamodb.readthedocs.io/en/latest/tutorial.html#updating-items
        # current_user.name = form.name.data # Or update locally?
        # current_user.email = form.email.data
        flash("Your account has been updated!", "success")
        redirect(url_for("users.Account"))
    elif request.method == "GET": # Populate the form field with current user info if the request is GET. POST requests will be returned before reaching here
        #form.email.data = current_user.email
        form.name.data = current_user.name
    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template("account.html", image_file=image_file, form=form)


@users.route("/reset_password", methods=["GET", "POST"])
def Reset_Password_Request():
    if current_user.is_authenticated: # if user already login, should not be resetting password. 
        return redirect(url_for("users.Account"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.get(form.email.data) # Form already ensured email exists, can straight away .get()
        send_reset_email(user)
        flash("An email has been sent with instructions to reset your password.", "info")
        return redirect(url_for("users.Login"))
    return render_template("reset_request_new.html", title="Reset Password", form=form)
    

@users.route("/reset_password/<token>", methods=["GET", "POST"])
def Reset_Password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.Home"))
    user = User.verify_reset_token(token) # Returns user object if valid token, else returns None
    if user is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("users.Reset_Password_Request"))
    # Valid token. Display form and let user reset password
    form = ResetPasswordForm()
    if form.validate_on_submit():
        password_hash = bcrypt.generate_password_hash(form.password.data).decode("utf-8") # cannot current_user.password = <new_password> because no user should be login now
        user.update(actions=[User.password.set(password_hash)])
        user.refresh()
        # user.password = password_hash
        flash("Password reset successfully. Please login with your new password.", "success")
        return redirect(url_for("users.Login"))
    return render_template("reset_password.html", title="Reset Password", form=form, username=user.name)
     

