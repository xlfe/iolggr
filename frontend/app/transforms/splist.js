import DS from 'ember-data';
import Em from 'ember';

export default DS.Transform.extend({
    deserialize: function(serialized) {
        return Em.isNone(serialized) ? Em.A() : serialized.split(',');
    },
    serialize: function(deserialized) {
        return Em.isNone(deserialized) ? [] : deserialized.join(',');
    }
});
