import decimal
from flask_wtf import FlaskForm
from wtforms import SubmitField, DecimalField, HiddenField
from wtforms.validators import DataRequired, NumberRange
from decimal import ROUND_HALF_UP

class UpdateThresholdForm(FlaskForm):
    device_id = HiddenField(validators=[DataRequired()])
    # default DecimalField implementation does not round off the form data it receives. It only rounds off the initial data (as in defaults, or model/saved data).
    pm_25 = DecimalField("PM 2.5 Threshold", places=1, rounding=ROUND_HALF_UP, validators=[DataRequired(), NumberRange(min=0, max=2000, message='Please enter a reasonable threshold value.')])
    pm_10 = DecimalField("PM 10 Threshold", places=1, rounding=ROUND_HALF_UP, validators=[DataRequired(), NumberRange(min=0, max=2000, message='Please enter a reasonable threshold value.')])
    submit = SubmitField("Update")