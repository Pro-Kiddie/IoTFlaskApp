from flask.json import JSONEncoder
import decimal, datetime

class CustomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%H:%M\n%Y-%m-%d")
        elif isinstance(obj, decimal.Decimal):
            return round(float(obj), 1)
        else:
            return super(CustomEncoder, self).default(obj)
