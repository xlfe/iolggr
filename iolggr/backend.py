import webapp2
import logging
import json
from google.appengine.ext import ndb
from models import iot_event, iot_rollup_week, iot_device, do_a_rollup

from datetime import datetime, timedelta

# _log = lambda x:logging.info(x)
_log = lambda x:x

class json_response(webapp2.RequestHandler):

    def get_response(self, status, content):
        """Returns an HTTP status message with JSON-encoded content (and appropriate HTTP response headers)"""

        # Create the JSON-encoded response
        try:
            response = webapp2.Response()
            # response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Content-Type'] = 'application/json'
            response.status = status
            json.dump(content, response.out)
        except:
            logging.error(content)
            raise

        return response

class compressed_response(webapp2.RequestHandler):

    def get_response(self, status, content):
        response = webapp2.Response()
        # response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Encoding'] = 'deflate'
        response.status = status
        response.out.write(content)
        return response

class device_ts(compressed_response):

    def get(self, mac, _ts):

        device = iot_device.get_by_id(mac)

        ts = datetime.strptime(_ts, "%Y-%m-%dT%H:%M:%S.%f")

        do_a_rollup(device_key=device.key)

        events = iot_rollup_week.get(parent=device.key, _ts=ts)

        if events is None:
            return self.get_response(500, "")

        return self.get_response(200, events.data)

api = webapp2.WSGIApplication([
    ('/api/devices/([^/]+)/([^/]+)', device_ts),
    ], debug=True)




















