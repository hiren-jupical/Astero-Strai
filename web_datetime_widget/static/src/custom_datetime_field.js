/** @odoo-module **/

import { Component, onWillRender, useState } from "@odoo/owl";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import {
    areDatesEqual,
    formatDate,
    formatDateTime,
} from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { archParseBoolean } from "@web/views/utils";
import { DateTimeField, dateTimeField } from "@web/views/fields/datetime/datetime_field";

/**
 * @typedef {luxon.DateTime} DateTime
 *
 
 * @typedef {import("../standard_field_props").StandardFieldProps & {
 *  endDateField?: string;
 *  maxDate?: string;
 *  minDate?: string;
 *  placeholder?: string;
 *  required?: boolean;
 *  rounding?: number;
 *  startDateField?: string;
 *  warnFuture?: boolean;
 *  showTime?: boolean;
 * }} DateTimeFieldProps
 *
 * @typedef {import("@web/core/datetime/datetime_picker").DateTimePickerProps} DateTimePickerProps
 */

/** @extends {Component<DateTimeFieldProps>} */
export class CustomDateTimeField extends DateTimeField {
    static props = {
        ...super.props,
        showTime: { type: Boolean, optional: true },
    };

    static template = "web.DateTimeField";

    //-------------------------------------------------------------------------
    // Lifecycle
    //-------------------------------------------------------------------------

    setup() {
        const getPickerProps = () => {
            const value = this.getRecordValue();
            /** @type {DateTimePickerProps} */
            const pickerProps = {
                value,
                type: this.props.showTime ? 'datetime' : 'date',
                range: this.isRange(value),
            };
            if (this.props.maxDate) {
                pickerProps.maxDate = this.parseLimitDate(this.props.maxDate);
            }
            if (this.props.minDate) {
                pickerProps.minDate = this.parseLimitDate(this.props.minDate);
            }
            if (!isNaN(this.props.rounding)) {
                pickerProps.rounding = this.props.rounding;
            }
            return pickerProps;
        };

        const dateTimePicker = useDateTimePicker({
            target: "root",
            get pickerProps() {
                return getPickerProps();
            },
            onChange: () => {
                this.state.range = this.isRange(this.state.value);
            },
            onApply: () => {
                const toUpdate = {};
                if (Array.isArray(this.state.value)) {
                    // Value is already a range
                    [toUpdate[this.startDateField], toUpdate[this.endDateField]] = this.state.value;
                } else {
                    toUpdate[this.props.name] = this.state.value;
                }
                // when startDateField and endDateField are set, and one of them has changed, we keep
                // the unchanged one to make sure ORM protects both fields from being recomputed by the
                // server, ORM team will handle this properly on master, then we can remove unchanged values
                if (!this.startDateField || !this.endDateField) {
                    // If startDateField or endDateField are not set, delete unchanged fields
                    for (const fieldName in toUpdate) {
                        if (areDatesEqual(toUpdate[fieldName], this.props.record.data[fieldName])) {
                            delete toUpdate[fieldName];
                        }
                    }
                } else {
                    // If both startDateField and endDateField are set, check if they haven't changed
                    if (areDatesEqual(toUpdate[this.startDateField], this.props.record.data[this.startDateField]) &&
                        areDatesEqual(toUpdate[this.endDateField], this.props.record.data[this.endDateField])) {
                        delete toUpdate[this.startDateField];
                        delete toUpdate[this.endDateField];
                    }
                }

                if (Object.keys(toUpdate).length) {
                    this.props.record.update(toUpdate);
                }
            },
        });
        // Subscribes to changes made on the picker state
        this.state = useState(dateTimePicker.state);
        this.openPicker = dateTimePicker.open;

        onWillRender(() => this.triggerIsDirty());
    }

    //-------------------------------------------------------------------------
    // Methods
    //-------------------------------------------------------------------------

    /**
     * @param {number} valueIndex
     */
    getFormattedValue(valueIndex) {
        const value = this.values[valueIndex];
        return value
            ? this.props.showTime && this.field.type !== "date"
                ? formatDateTime(value)
                : formatDate(value)
            : "";
    }
}

export const customDateTimeField = {
    ...dateTimeField,
    component: CustomDateTimeField,
    displayName: _t("Custom Date & Time"),
    supportedOptions: [
        ...dateTimeField.supportedOptions,
    ],
    extractProps: ({ attrs, options }, dynamicInfo) => ({
        ...dateTimeField.extractProps({ attrs, options }, dynamicInfo),
        showTime: archParseBoolean(options.showTime ?? false),
    }),
    supportedTypes: ["datetime"],
};

registry
    .category("fields")
    .add("custom_datetime", customDateTimeField);
