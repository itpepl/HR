frappe.ui.form.on("Leave Application", {
    onload(frm) {        
        toggle_comp_off_fields(frm, false);
    },
    employee(frm) {
        toggle_comp_off_fields(frm, true);
    },
    leave_type(frm) {
        toggle_comp_off_fields(frm, true);
    },
    from_date(frm) {
        toggle_comp_off_fields(frm, true);
    },
    to_date(frm) {
        toggle_comp_off_fields(frm, true);
    }
});

function toggle_comp_off_fields(frm, validate = false) {
    frm.set_df_property("custom_off_day_work_request", "hidden", 1);
    frm.set_df_property("custom_off_day_date", "hidden", 1);

    if (!frm.doc.leave_type) return;

    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;

            const is_comp_off = r.message.is_compensatory;

            if (!is_comp_off) {
                frm.set_df_property("custom_off_day_work_request", "hidden", 1);
                frm.set_df_property("custom_off_day_date", "hidden", 1);

                frm.set_value("custom_off_day_work_request", null);
                frm.set_value("custom_off_day_date", null); 
                return;
            }

            frm.set_df_property("custom_off_day_work_request", "hidden", 0);
            frm.set_df_property("custom_off_day_date", "hidden", 0);

            if (!validate) return;

            fetch_valid_comp_off(frm, r.message.name);
        }
    })
}

function fetch_valid_comp_off(frm, leave_type_name) {

    if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date || !frm.doc.leave_type) return;

    if (frm.doc.from_date !== frm.doc.to_date) {
        frappe.throw("For Compensatory Off, From Date and To Date must be the same.");
    }

    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_valid_comp_off",
        args: {
            employee: frm.doc.employee,
            leave_date: frm.doc.from_date,
            leave_type_name: leave_type_name
        },
        callback(r) {
            if (!r.message) {
                frm.set_value("custom_off_day_work_request", null);
                frm.set_value("custom_off_day_date", null);

                frappe.throw({
                    title: __("No Valid Comp-Off"),
                    message: __("No valid Compensatory Off found for the selected date."),
                    indicator: "red"
                });
                return;
            }
            const comp_off_record_name = r.message.name;
            const comp_off_date = r.message.date;

            frm.set_value("custom_off_day_work_request", comp_off_record_name);
            frm.set_value("custom_off_day_date", comp_off_date);
        }
    });
}
