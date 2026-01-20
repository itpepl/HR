frappe.ui.form.on("Leave Application", {
    onload(frm) {        
        toggle_comp_off_fields(frm, false);
        set_leave_type_query_extended(frm);
    },
    employee(frm) {
        toggle_comp_off_fields(frm, true);
        fetch_reporting_manager(frm);
        set_leave_type_query_extended(frm);
    },
    leave_type(frm) {
        toggle_comp_off_fields(frm, true);

        frm.set_df_property("custom_proof_document", "reqd", 0);
        frm.set_df_property("description", "reqd", 0);

        if (!frm.doc.leave_type) return;
        frappe.call({
            method: "jkmpcl_hr.py.leave_application.get_leave_type",
            args: {
                leave_type: frm.doc.leave_type
            },
            callback(r) {
                if (!r.message) return;

                const leave_type = r.message.custom_leave_type;
                if (leave_type === "Medical Emergency Leave") {
                    frm.set_df_property("custom_proof_document", "reqd", 1);
                    frm.set_df_property("description", "reqd", 1);
                }
            }
        });
    },
    from_date(frm) {
        toggle_comp_off_fields(frm, true);
        set_leave_type_query_extended(frm);
    },
    to_date(frm) {
        toggle_comp_off_fields(frm, true);
        set_leave_type_query_extended(frm);
    }
});

function fetch_reporting_manager(frm) {
    
    frappe.call({
        method: "jkmpcl_hr.py.utils.get_emp_reporting_manager",
        args: {
            emp_id: frm.doc.employee
        },
        callback(r) {
            if (!r.message) return;

            frm.set_value("leave_approver", r.message);
        }
    });
}

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

                if (frm.doc.custom_off_day_work_request) {
                    frm.set_value("custom_off_day_work_request", null);
                }

                if (frm.doc.custom_off_day_date) {
                    frm.set_value("custom_off_day_date", null);
                }
                
                frm.refresh_fields();
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

                // frappe.throw({
                //     title: __("No Valid Comp-Off"),
                //     message: __("No valid Compensatory Off found for the selected date."),
                //     indicator: "red"
                // });
                return;
            }
            const comp_off_record_name = r.message.name;
            const comp_off_date = r.message.date;

            frm.set_value("custom_off_day_work_request", comp_off_record_name);
            frm.set_value("custom_off_day_date", comp_off_date);
        }
    });
}


async function set_leave_type_query_extended(frm) {
    let leave_details = {};
    let lwps = [];

    if (!frm.doc.employee) return;
    
    // Call default ERPNext method
    const r = await frappe.call({
        method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
        args: {
            employee: frm.doc.employee,
            date: frm.doc.from_date || frm.doc.posting_date
        }
    });

    if (r.exc || !r.message) return;

    leave_details = r.message.leave_allocation || {};
    lwps = r.message.lwps || [];

    // Default allowed leave types (Allocated + LWP)
    let allowed_leave_types = Object.keys(leave_details).concat(lwps);

    // Fetch OPEN leave types from Python (permission-safe)
    const open_leave_res = await frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_open_leave_types"
    });

    const open_leave_types = open_leave_res.message || [];

    // Append + remove duplicates
    allowed_leave_types = [...new Set(
        allowed_leave_types.concat(open_leave_types)
    )];

    // Apply final query
    frm.set_query("leave_type", function () {
        return {
            filters: [["leave_type_name", "in", allowed_leave_types]]
        };
    });
}