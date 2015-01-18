#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import json
import logging

from models import iot_event

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')


class LogHandler(webapp2.RequestHandler):

    def post(self):
        log = self.request.headers['X-Log']
        mac = self.request.headers['X-Mac']
        params = {}
        params['name'] = self.request.headers['X-Name']
        try:
            params['AP-mode'] = self.request.headers['X-Mode']
            stats = self.request.headers['X-Stats'].split(',')

            for k,v in enumerate(['authmode','rssi','bssid','channel']):
                params['AP-{}'.format(v)] = stats[k]
        except:
            pass

        try:
            for param in log.strip().split('&'):
                k,v = param.split('=')
                params[k]= v
        except:
            pass

        bssid = None
        if 'AP-bssid' in params:
            bssid = params['AP-bssid']

        i=iot_event(mac = mac,bssid=bssid,params=params)
        i.put()
        log = "MAC = {}\n".format(mac)
        for k,v in params.iteritems():
            log += "{} = {}\n".format(k,v)

        logging.info(log)
        return


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/log',LogHandler),
], debug=True)
