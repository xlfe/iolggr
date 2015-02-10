import Em from 'ember';

export default Em.ObjectController.extend({
    actions: {

    },
    latest_obs: function() {
        var obs = this.get('_obs');

        if (Em.isEmpty(obs)){
            return null;
        }

        return obs.get('lastObject');
    }.property('_obs.[]')
});