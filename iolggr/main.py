#!/usr/bin/env python

import webapp2
import json
import logging
import datetime

from google.appengine.ext import deferred
from models import iot_event, iot_device, do_a_rollup

class RollupHandler(webapp2.RequestHandler):
    def get(self):
        """Rollup logs into weeks"""

        devices = iot_device.query().fetch(20)

        for device in devices:
            logging.info('Rolling up {}'.format(device))
            deferred.defer(do_a_rollup, device.key, _queue='rollup')


class LogHandler(webapp2.RequestHandler):

    #define the params that are stored
    _PARAMS = {
        'ts':   lambda p: p['ts'],
        'temp': lambda p: int(p['temp']),
        'baro': lambda p: int(p['baro']),
        'rssi': lambda p: int(p['rssi']),
        'up':   lambda p: int(float(p['up']))
    }

    def post(self, mac):

        device = iot_device.get_or_insert(mac)

        params = json.loads(self.request.body)
        _params = {}

        for k, v in self._PARAMS.iteritems():
            _params[k] = v(params)

        #save the event
        ts = datetime.datetime.strptime(params['ts'], "%Y-%m-%dT%H:%M:%S.%f")
        i=iot_event(parent=device.key,
                    ts=ts,
                    params=_params
        )
        i.put()

        #show the log
        log = "MAC = {}\n".format(mac)
        for k,v in _params.iteritems():
            log += "{} = {}\n".format(k,v)

        logging.info(log)
        return


app = webapp2.WSGIApplication([
    ('/admin/rollup', RollupHandler),
    ('/log/([^/]+)',LogHandler),
], debug=True)
