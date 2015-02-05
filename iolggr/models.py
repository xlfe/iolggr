import collections
import logging
from google.appengine.ext import ndb
from google.appengine.ext import deferred
import datetime
import json


class iot_week(ndb.Model):
    WEEK_START_DAY = 1 #Monday
    """1 week worth of data"""

    start = ndb.DateTimeProperty(required=True)
    end = ndb.ComputedProperty(lambda x: x.start + datetime.timedelta(days=7))

    updated = ndb.DateTimeProperty(auto_now=True)
    remote_addrs = ndb.StringProperty(repeated=True)
    mac = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    data = ndb.JsonProperty(compressed=False, indexed=False, default={})

    @classmethod
    def dt_to_week(cls,dt):
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=dt.isoweekday() - 1)
        return start

    @classmethod
    def get_or_create(cls,mac,week):
        o = cls.query().filter(cls.mac== mac, cls.start == week).get()

        if o is None:
            o = cls(mac=mac, start=week)

        return o

class iot_exception(ndb.Model):

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    mac = ndb.StringProperty()
    exception = ndb.StringProperty(choices=['CONNECTION','WIFI'])
    params = ndb.JsonProperty(indexed=False)


class iot_event(ndb.Model):
    """
        Params should include:

        Store these for device identification:
            MAC = 1340c89be4c1
            remote_addr

        Dont store these:
            AP-bssid = fc:75:16:53:ef:dc
            w_att = 1
            c_att = 1
            AP-authmode = 2
            AP-mode = 1
            AP-channel = 6

        Keep this in iot_event:
            name = Office

        Keep these in params:
            pressure = 94799
            temp = 2625
            AP-rssi = -82
            delay = 7079
            w_delay = 6793
        """

    _PARAMS = {
        'temp':     lambda p: int(p['temp']),
        'pressure': lambda p: int(p['pressure']),
        'rssi':     lambda p: int(p['AP-rssi']),
        'w_delay':  lambda p: int(p['w_delay']),
        'delay':    lambda p: int(p['delay']) - int(p['w_delay'])
    }

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    mac = ndb.StringProperty()
    remote_addr = ndb.StringProperty()
    name = ndb.StringProperty()
    params = ndb.JsonProperty(indexed=False)


    @classmethod
    def mk_params(cls,params):

        p = {}

        for k,v in cls._PARAMS.iteritems():
            try:
                p[k] = v(params)
            except TypeError:
                p[k] = params[v]

        return p




def rollup_events():

    events = iot_event.query().order(iot_event.mac, -iot_event.timestamp).fetch(1000)

    if len(events) == 0:
        return
    elif len(events) == 1000:
        # More events waiting then queue them up
        deferred.defer(rollup_events,_queue='rollup')

    mac_weeks = collections.defaultdict(lambda: collections.defaultdict(list))

    for e in events:
        mac_weeks[e.mac][iot_week.dt_to_week(e.timestamp)].append(e)

    for mac,weeks in mac_weeks.iteritems():

        for week,events in weeks.iteritems():

            rollup = iot_week.get_or_create(mac=mac,week=week)
            sz = 0

            for e in events:

                d = {}

                try:
                    for k in iot_event._PARAMS:
                        d[k] = e.params[k]
                except KeyError:
                    d = iot_event.mk_params(e.params)

                dt = e.timestamp.replace(microsecond=0).isoformat()
                rollup.data[dt] = d

                if e.remote_addr not in rollup.remote_addrs:
                    rollup.remote_addrs.append(e.remote_addr)
                rollup.name = e.name

            logging.info('{} events for {} added into rollup({}) with {} total events'.format(len(events),mac,week,len(rollup.data)))
            rollup.put()
            ndb.delete_multi([e.key for e in events])




