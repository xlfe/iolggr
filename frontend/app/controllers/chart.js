import Em from 'ember';
/* global moment */


var TimePeriod = Em.Object.extend({});

export default Em.ObjectController.extend({
    actions: {
        remove: function (dev) {
            var d = this.get('_devices');

            if (d.length <= 1) {
                alert("You must have at least one device on the chart");
                return;
            }
            d.removeObject(dev);

            var devices = this.get('devices').split(',');
            devices.removeObject(dev.get('id'));
            this.set('devices', devices.join(','));
        },
        refresh: function () {
            this.dev_observer();
        },
        set_tp: function (tp) {
            var _this = this;
            this.set('loading', true);
            setTimeout(function () {
                _this.get('timeperiods').forEach(function (_) {
                    _.set('active', false);
                });
                tp.set('active', true);
                _this.set('loading', false);
            }, 100);
        }
    },
    model: {},
    colours: {},
    c_i: 1,
    queryParams: ['devices'],
    timeperiods: [
        TimePeriod.create({
            name: '1 day',
            active: true,
            start: function (n) {
                return n.subtract(1, 'days');
            }
        }),
        TimePeriod.create({

            name: '1 week',
            active: false,
            start: function (n) {
                return n.subtract(7, 'days')
            }
        }),
        TimePeriod.create({

            name: '1 month',
            active: false,
            start: function (n) {
                return n.subtract(1, 'month')
            }
        })
    ],
    tp_active: function() {
        var tp = this.get('timeperiods').filter(function(_){
            return _.get('active') === true;
        })[0],
            now = moment().toDate(),
            start = tp.get('start')(moment()).toDate();

        return [start,now];
    }.property('timeperiods.@each.active'),
    dev_observer: function () {

        var store = this.get('store'),
            _this = this,
            devices = this.get('devices');

        if (Em.isNone(devices)) {
            return;
        }

        this.set('loading',true);

        new Em.RSVP.all(devices.split(',').map(function (device) {
                return store.find('device', {id: device, rel: 0});
            })
        ).then(function (devices) {
                _this.set('_devices',
                    devices.map(function (d) {
                        var dev = d.get('firstObject'),
                            i = _this.get('c_i'),
                            colours = _this.get('colours');

                        if (dev.get('id') in colours) {
                            dev.set('colour', colours[dev.get('id')]);
                        }else {
                            dev.set('colour', i);
                            colours[dev.get('id')] = i;
                            _this.incrementProperty('c_i');
                            _this.set('colours',colours);
                        }

                        return dev;
                    })
                );
                _this.set('loading',false);
            }
        );
    }.observes('devices')
});
