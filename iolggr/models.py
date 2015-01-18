
from google.appengine.ext import ndb


class iot_event(ndb.Model):

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    mac = ndb.StringProperty()
    bssid = ndb.StringProperty()
    params = ndb.JsonProperty(indexed=False)
