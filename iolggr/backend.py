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

    def get_data(self, mac, _ts):

        device = iot_device.get_by_id(mac)

        ts = datetime.strptime(_ts, "%Y-%m-%dT%H:%M:%S.%f")

        do_a_rollup(device_key=device.key)

        return iot_rollup_week.get(parent=device.key, _ts=ts)

    def get(self, mac, _ts):

        events = self.get_data(mac, _ts)

        if events is None:
            return self.get_response(500, "")
        return self.get_response(200, events.data)

class device_csv(device_ts):

    def get(self, mac):

        events = self.get_data(mac, datetime.utcnow().isoformat())

        if events is None:
            return self.get_response(500, "")

        #[["ts", "temp", "baro", "rssi", "up"], ["2017-05-28T06:31:42.835011", 1480, 936354, -60, 3041],

        response = webapp2.Response()
        # response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Encoding'] = 'deflate'
        response.status = 200

        data = events.get_data()
        response.out.write(','.join(map(str, data[0]))+'\n')

        limit = 0

        for line in reversed(data):
            response.out.write(','.join(map(str, line))+'\n')
            limit += 1
            if limit > (60*60*24*2)/150:
                break

        return response

api = webapp2.WSGIApplication([
    ('/api/devices/([^/]+)/([^/]+)', device_ts),
    ('/api/devices/([^-]+).csv', device_csv),
    ], debug=True)




















