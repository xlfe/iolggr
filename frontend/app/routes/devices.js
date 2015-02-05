import Ember from 'ember';

export default Ember.Route.extend({
    model: function () {

        return this.store.find('iplist','me').then(function(ipl){
            var res = ipl.get('results'),
                _res = [];

            for (var k in res){
                _res.pushObject(Ember.Object.create({
                    name:res[k],
                    id:k
                }));
            }
            return _res;
        });
    }
});
