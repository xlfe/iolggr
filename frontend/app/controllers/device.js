import Em from 'ember';

export default Em.ObjectController.extend({
    actions: {

    },
    last_seen: function() {

        var m = this.get('model');

        if (Em.isNone(m)){
            return null;
        }

        for (var k in m.get('obs')){
            return k;
        }

    }.property('model.obs'),
    last_obs: function() {
        var m = this.get('model'),
            last_seen = this.get('last_seen');

        if (last_seen == null){
            return null;
        }
        return m.get('obs')[last_seen];
    }.property('last_seen')

});