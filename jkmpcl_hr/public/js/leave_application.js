frappe.ui.form.on("Leave Application", {
    employee(frm) {
        toggle_comp_off_fields(frm);
    },
    leave_type(frm) {
        toggle_comp_off_fields(frm);
    },
    from_date(frm) {
        toggle_comp_off_fields(frm);
    },
    to_date(frm) {
        toggle_comp_off_fields(frm);
    }
});

function toggle_comp_off_fields(frm) {
    if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date || !frm.doc.leave_type) return;

    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (r && r.message) {

                const leave_type_name = r.message.name;
                const is_comp_off = r.message.is_compensatory;

                if (is_comp_off === 1){
                    if (frm.doc.from_date !== frm.doc.to_date) {
                        frappe.throw("For Compensatory Off, From Date and To Date must be the same.");
                    }

                    fetch_valid_comp_off(frm, leave_type_name);
                }
                
            }
        }
    })
}

function fetch_valid_comp_off(frm, leave_type_name) {

    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_valid_comp_off",
        args: {
            employee: frm.doc.employee,
            leave_date: frm.doc.from_date,
            leave_type_name: leave_type_name
        },
        callback(r) {
            if (!r.message) {
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
