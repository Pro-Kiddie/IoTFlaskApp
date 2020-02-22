from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed # FileAllowed is the validator to check the file type allowed by checking the extension
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError #https://wtforms.readthedocs.io/en/stable/validators.html#wtforms.validators.Regexp
from flask_iot_app.models import User
from flask_login import current_user

class LoginForm(FlaskForm): # Inherits FlaskForm
    # Different fields in the form as class variables
    email = StringField('Email', validators=[DataRequired(), Email()]) # Represents an <input type="txt">
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=50)]) # Can create custom regular expression for validator
    remember = BooleanField("Remember Me")
    submit = SubmitField("SIGN IN")

class CreateAccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()]) # 'Email' is the label for the form that will appear in HTML
    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=30)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=50)]) # Can create custom regular expression for validator
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Create Account")

    # Customize validator to check if user with same email already existed
    # No need to add these funcs to validators=[]. This are known as in-line validators
    # They will be automatically evaluated with the field passed in
    # Check documentation
    def validate_email(self, email):
        user = None
        try:
            user = User.get(email.data)
        except User.DoesNotExist:
            pass
        # user will be none if no user with same email exists
        if user:
            raise ValidationError("That email has already been registered. Please choose a different one.")

    # def validate_name(self, name):
    #     user = User.query.filter_by(name=name.data).first()
    #     if user:
    #         raise ValidationError("That name has already been registered. Please choose a different one.")

class UpdateAccountForm(FlaskForm):
    #email = StringField('Email', validators=[DataRequired(), Email()]) # 'Email' is the label for the form that will appear in HTML
    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=30)])
    picture = FileField("Update Profile Picutre", validators=[FileAllowed(["jpg", "png", "jpeg"])])
    submit = SubmitField("Update")

    # def validate_email(self, email):
    #     if current_user.email != email.data: # Only validates email when user updates email. User can only update name or profile picture 
    #         user = None
    #         try:
    #             user = User.get(email.data)
    #         except User.DoesNotExist:
    #             pass
    #         if user:
    #             raise ValidationError("That email has already been registered. Please choose a different one.")

    # def validate_name(self, name):
    #     if current_user.name != name.data:
    #         user = User.query.filter_by(name=name.data).first()
    #         if user:
    #             raise ValidationError("That name has already been registered. Please choose a different one.")


class RequestResetForm(FlaskForm): 
    email = StringField('Email', validators=[DataRequired(), Email()]) 
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user = None
        try:
            user = User.get(email.data)
        except User.DoesNotExist:
            pass
        if user is None:
            raise ValidationError("That account has not been created yet. Please create an account first.")      

class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=50)]) # Can create custom regular expression for validator
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Reset Password")