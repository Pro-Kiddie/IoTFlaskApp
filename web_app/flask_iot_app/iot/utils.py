from flask.json import JSONEncoder
import decimal, datetime

class CustomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%H:%M\n%Y-%m-%d")
        # elif isinstance(obj, float): Will not be called when float is to be serialized -> https://stackoverflow.com/a/47276890
        #     return round(float(obj), 1)
        elif isinstance(obj, decimal.Decimal):
            return round(float(obj), 1)
        else:
            return super(CustomEncoder, self).default(obj)
