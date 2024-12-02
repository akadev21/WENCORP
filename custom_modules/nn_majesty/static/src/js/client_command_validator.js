odoo.define('nn_majesty.client_command_validator', function(require) {
    "use strict";

    var FormController = require('web.FormController');
    var core = require('web.core');
    var _t = core._t;

    FormController.include({
        async _onSave() {
            var res = await this._super(...arguments);
            var $wizardForm = this.$el;

            // Get the total value of the `number_input` fields
            var totalNumberInput = 0;
            $wizardForm.find('input[name="number_input"]').each(function() {
                totalNumberInput += parseFloat($(this).val()) || 0;
            });

            // Get the quantity value
            var quantity = parseFloat($wizardForm.find('input[name="quantity"]').val()) || 0;

            // Compare the values
            if (totalNumberInput !== quantity) {
                this._showWarning(_t("The sum of 'number_input' does not match the quantity."));
                return false;
            }
            return res;
        },

        _showWarning: function(message) {
            this.do_notify(_t('Validation Error'), message);
        }
    });
});
