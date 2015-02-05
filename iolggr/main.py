#!/usr/bin/env python

import webapp2
import json
import logging

from google.appengine.ext import deferred
from models import iot_event,iot_exception,rollup_events

class RollupHandler(webapp2.RequestHandler):
    def get(self):
        """Rollup logs into weeks"""

        deferred.defer(rollup_events,_queue='rollup')

class LogHandler(webapp2.RequestHandler):
    def post(self):

        params = {}
        mac = self.request.headers['X-Mac']

        #populate params with all stats received from device
        params['AP-mode'] = self.request.headers['X-Mode']
        params['name'] = self.request.headers['X-Name']

        stats = self.request.headers['X-Stats'].split(',')
        for k,v in enumerate(['authmode','rssi','bssid','channel']):
            params['AP-{}'.format(v)] = stats[k]

        log = self.request.headers['X-Log']
        for param in log.strip().split('&'):
            k,v = param.split('=')
            params[k]= v

        # bssid = None if 'AP-bssid' not in params else params['AP-bssid']

        #check for exceptions, log them if they exist
        c_att = int(params['c_att'])
        w_att = int(params['w_att'])

        assert c_att < 60 and w_att < 60

        if c_att > 1:
            iot_exception(mac=mac, exception='CONNECTION',params=params).put()

        if w_att > 1:
            iot_exception(mac=mac, exception='WIFI',params=params).put()

        #save the event
        i=iot_event(mac=mac,
                    name=params['name'],
                    remote_addr = self.request.remote_addr,
                    params=iot_event.mk_params(params)
        )
        i.put()

        #show the log
        log = "MAC = {}\nNAME = {}\n".format(mac,params['name'])
        for k,v in i.params.iteritems():
            log += "{} = {}\n".format(k,v)

        logging.info(log)
        return


app = webapp2.WSGIApplication([
    ('/admin/rollup', RollupHandler),
    ('/log',LogHandler),
], debug=True)
