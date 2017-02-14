from google.appengine.ext import ndb
from google.appengine.ext import deferred
from datetime import timedelta,datetime
import collections
import logging
import json


format_timestamp = lambda x:x.replace(microsecond=0).isoformat()
to_dt = lambda x:datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')
PERIOD_LENGTH = timedelta(days=7)

class iot_week(ndb.Model):

    #todo account for daylight savings

    stored_params = 'temp,pressure,rssi,up'
    start = ndb.DateTimeProperty(required=True)
    end = ndb.ComputedProperty(lambda x: x.start + PERIOD_LENGTH)
    updated = ndb.DateTimeProperty(auto_now=True)
    data = ndb.BlobProperty(compressed=False, indexed=False)
    mac = ndb.StringProperty(required=True)

    @classmethod
    def get(cls, mac, ts):
        """
        Retrieve the event roll for mac and ts
            sort by oldest first, and then filter by end being after ts.
            the result should have ts before end and there shouldn't be another result with ts after start
        """

        return ndb.Query(kind=cls).order(cls.start).filter(cls.mac == mac, ts < cls.end).get()

    @classmethod
    def get_or_create(cls, mac, ts):

        o = cls.get(mac, ts)

        if o is None:
            o = cls(mac=mac, start=ts)
            o.data = "[]".encode('zlib_codec')

        return o

    def append(self, events):
        data = json.loads(self.data.decode('zlib_codec'))
        data.extend(events)
        self.data=json.dumps(data).encode('zlib_codec')


class iot_event(ndb.Model):

    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    mac = ndb.StringProperty()
    name = ndb.StringProperty()
    params = ndb.JsonProperty(indexed=False)

def rollup_events(batch_size=1000):
    """Roll-up individual events into a single iot_week object"""

    #get a batch of events, oldest first
    _events = iot_event.query().order(iot_event.mac, iot_event.timestamp).fetch(batch_size)

    if len(_events) ==0:
        return

    macs = collections.defaultdict(list)

    for e in _events:
        macs[e.mac].append(e)


    #todo sorted

    for mac, periods in mac_periods.iteritems():

        for period, events in periods.iteritems():

            rollup = iot_week.get_or_create(mac=mac, start=period)

            rollup.append(events)

            rollup.put()
            logging.info('{} events for {} added into {} with {} total events'.format(len(events), rollup.key, period,
                                                                                      len(rollup.data)))
            logging.info('Event extent is {} -> {}'.format(events[0].timestamp, events[-1].timestamp))
            logging.info('Data extent is {} -> {}'.format(rollup.d_start, rollup.d_end))
            ndb.delete_multi([e.key for e in events])

    if len(_events) == 1000:
        deferred.defer(rollup_events, _queue='rollup')


