odoo.define('learning_projects.custom_many2many_tags', function (require) {
"use strict";

var relational_fields = require('web.relational_fields');
var FieldMany2ManyTags = relational_fields.FieldMany2ManyTags;
var fieldRegistry = require('web.field_registry');

var CustomFieldMany2ManyTags = FieldMany2ManyTags.extend({
    _renderTags: function () {
        if (this.value.data.length > 10) {
            // Создаём копию данных, содержащую только первые 10 записей
            var limitedData = _.first(this.value.data, 10);
            // Вызываем оригинальный метод _renderTags с ограниченным набором данных
            this._super({data: limitedData});
        } else {
            // Если записей 10 или меньше, просто вызываем оригинальный метод
            this._super.apply(this, arguments);
        }
    },
});

fieldRegistry.add('custom_many2many_tags', CustomFieldMany2ManyTags);

});

