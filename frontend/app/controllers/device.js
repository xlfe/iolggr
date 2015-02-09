import Em from 'ember';

export default Em.ObjectController.extend({
    actions: {

    },
    last_obs: function() {
        var obs = this.get('_obs');

        console.log(obs);
        if (Em.isEmpty(obs)){
            return null;
        }

        return obs.get('lastObject');
    }.property('_obs.[]')
});