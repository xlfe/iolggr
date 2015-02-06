import Ember from 'ember';

export default Ember.ObjectController.extend({
    model: {},
    queryParams: ['devices'],

    //model: function (params) {
    //
    //    return this.store.find('charts',params.id);
    //}
});
