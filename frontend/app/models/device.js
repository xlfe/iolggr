import DS from 'ember-data';
import Em from 'ember';

export default DS.Model.extend({
    name: DS.attr('string'),
    obs: DS.attr('list'),
    keys: DS.attr('splist'),
    _obs: function () {
        var keys = this.get('keys'),
            obs = this.get('obs'),
            start = moment(this.get('start'));

        if (Em.isEmpty(obs)) {
            return null;
        }

        return obs.map(function (_) {

            start.add(+_[0], 'seconds');

            var

                _obs = _.slice(1),
                obj = {
                    dt: start.toDate()
                };

            console.log(start.toDate(),_[0]);

            for (var i = 0; i < _obs.length; i++) {
                obj[keys[i]] = _obs[i];
            }

            return obj;

        });
    }.property('keys', 'obs.[]', 'start'),
    start: DS.attr('datetime')
});