from google.appengine.ext import ndb
from google.appengine.ext import deferred
from datetime import timedelta,datetime
import collections
import logging
import json

BATCH_SIZE = 1000

format_timestamp = lambda x:x.replace(microsecond=0).isoformat()
to_dt = lambda x:datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')

class iot_rollup_base(ndb.Model):

    start = ndb.DateTimeProperty(required=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    data = ndb.BlobProperty(compressed=False, indexed=False)

    @classmethod
    def get(cls, parent, _ts):
        """
        Retrieve the event roll for mac and ts
            sort by oldest first, and then filter by end being after ts.
            the result should have ts before end and there shouldn't be another result with ts after start
        """

        ts = _ts - cls.period_length

        return cls.query(ancestor=parent).order(cls.start).filter(cls.start >= ts).get()

    @classmethod
    def get_or_create(cls, parent, ts):

        o = cls.get(parent, ts)

        if o is None:
            o = cls(parent=parent, start=ts)
            o.set_data([cls.stored_params])

        return o


    def append(self, events):
        data = self.get_data()
        data.extend(events)
        self.set_data(data)

    def get_data(self):
        return json.loads(self.data)

    def set_data(self, data):
        self.data = json.dumps(data)

class iot_rollup_week(iot_rollup_base):
    period_length = timedelta(days=7)
    end = ndb.ComputedProperty(lambda x: x.start + iot_rollup_week.period_length)
    stored_params = ['ts', 'temp', 'baro', 'rssi', 'up']



class iot_event(ndb.Model):
    ts = ndb.DateTimeProperty(required=True)
    params = ndb.JsonProperty(indexed=False)

    def mk_data(self, params):
        return [
            self.params[k] for k in params
        ]


class iot_device(ndb.Model):
    pass

@ndb.transactional
def do_a_rollup(device_key):
    #get a batch of events, oldest first

    events = iot_event.query(ancestor=device_key).order(iot_event.ts).fetch(250)

    if len(events) == 1000:
        deferred.defer(do_a_rollup, device_key, _queue='rollup')

    while events:

        rollup = iot_rollup_week.get_or_create(parent=device_key, ts=events[0].ts)

        #The start of the rollup should always be earlier than the requested ts
        assert rollup.start <= events[0].ts

        #get those events that would go into this rollup
        rollup_candidates = filter(lambda _: _.ts < rollup.end, events)

        #we should have at least one event here...
        assert rollup_candidates

        rollup.append(_.mk_data(rollup.stored_params) for _ in rollup_candidates)
        rollup.put()
        ndb.delete_multi([e.key for e in rollup_candidates])
        logging.info('{} events for {} added into {}'.format(len(rollup_candidates), device_key, rollup.start))

        for _ in rollup_candidates:
            events.remove(_)


