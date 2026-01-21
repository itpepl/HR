frappe.ui.form.on("Leave Application", {
    onload(frm) {        
        toggle_comp_off_fields(frm, false);
        set_leave_type_query_extended(frm);
        toggle_maternity_fields(frm)
    },

    before_save(frm) {
        validate_for_adoption_leave(frm);
    },
    employee(frm) {
        toggle_comp_off_fields(frm, true);
        fetch_reporting_manager(frm);
        set_leave_type_query_extended(frm);
        if(frm.doc.leave_type) {
            set_ml_leave_dates(frm)            
        }
    },
    leave_type(frm) {

        toggle_comp_off_fields(frm, true);
        toggle_maternity_fields(frm);
        if (frm.doc.employee) {
            set_ml_leave_dates(frm)            
        }

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

    custom_maternity_leave_type(frm) {
        set_ml_leave_dates(frm)
    },
    from_date(frm) {
        toggle_comp_off_fields(frm, true);
        set_leave_type_query_extended(frm);
        set_ml_leave_dates(frm);
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

function toggle_maternity_fields(frm) {


    frm.set_df_property("custom_maternity_leave_type", "hidden", 1)
    frm.set_df_property("custom_no_of_surviving_children", "hidden", 1)
    frm.set_df_property("custom_adopting_child_age", "hidden", 1)

    frm.set_df_property("custom_maternity_leave_type", "reqd", 0);
    frm.set_df_property("custom_no_of_surviving_children", "reqd", 0);
    frm.set_df_property("custom_adopting_child_age", "reqd", 0);
    

    frm.set_df_property("to_date", "read_only", 0);
    
    if (!frm.doc.leave_type) return;
    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;

            const leave_type = r.message.custom_leave_type;
            if (leave_type === "Maternity Leave" || leave_type === "Special Maternity Leave") {
                frm.set_df_property("custom_maternity_leave_type", "hidden", 0);
                frm.set_df_property("custom_maternity_leave_type", "reqd", 1);                    
            }

            if (leave_type === "Child Adoption Leave") {
                frm.set_df_property("custom_no_of_surviving_children", "hidden", 0)
                frm.set_df_property("custom_adopting_child_age", "hidden", 0)

                frm.set_df_property("custom_no_of_surviving_children", "reqd", 1);
                frm.set_df_property("custom_adopting_child_age", "reqd", 1);
                frm.set_df_property("description", "reqd", 1);
                frm.set_df_property("custom_proof_document", "reqd", 1);


                frm.set_df_property("to_date", "read_only", 1);
            }

        }
    });    

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
    console.log("Setting extended leave type query...");
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
            method: "jkmpcl_hr.py.leave_application.get_open_leave_types",
            args: {
                employee: frm.doc.employee || null,
            }
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


function set_ml_leave_dates(frm) {

    if (!frm.doc.leave_type) return;
    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;

            const leave_type = r.message.custom_leave_type;
            if (leave_type !== "Child Adoption Leave" && leave_type !== "Maternity Leave" && leave_type !== "Special Maternity Leave") {
                // frm.set_value("to_date", null);
                // frm.set_value("from_date", null);        
                return;
            }
            
            let from_date = frm.doc.from_date ? frappe.datetime.str_to_obj(frm.doc.from_date) : frappe.datetime.get_today();
            if (!frm.doc.from_date) {
                frm.set_value("from_date", frappe.datetime.obj_to_str(from_date));
            }

            frappe.call({
                method: "jkmpcl_hr.py.leave_application.get_days_for_ml",
                args: {
                    employee: frm.doc.employee,
                    leave_type: leave_type,
                    maturity_leave_type: frm.doc.custom_maternity_leave_type,
                    from_date: frm.doc.from_date
                },
                async callback(r) {
                    if (!r.message) return;
                    let to_date = from_date;
                    const leave_days = r.message - 1;
                    console.log("Days for ML:", leave_days);
                    to_date = frappe.datetime.add_days(from_date, leave_days);
                    frm.set_value("to_date", frappe.datetime.obj_to_str(to_date));

                }
            });

            // let to_date = from_date;
            // if ((frm.doc.custom_maternity_leave_type === "Miscarriage" || frm.doc.custom_maternity_leave_type === "Abortion") && leave_type !== "Child Adoption Leave") {
            //     console.log("This is getting called")
            //     to_date = frappe.datetime.add_days(from_date, 41);
            // }
            // else if (frm.doc.custom_maternity_leave_type === "Normal" || leave_type === "Child Adoption Leave") {
            //     to_date = frappe.datetime.add_days(from_date, 89);
            // }
            
        
            // frm.set_value("to_date", frappe.datetime.obj_to_str(to_date));
        }
    });    
}


function validate_for_adoption_leave(frm) {
    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;
            const leave_type = r.message.custom_leave_type;
            if (leave_type !== "Child Adoption Leave") return;
            if (frm.doc.custom_adopting_child_age > 1) {
                frappe.throw("Adopting Child Age must be less than or equal to 1 year for Child Adoption Leave.");
            }
            if (frm.doc.custom_no_of_surviving_children > 2) {
                frappe.throw("Number of Surviving Children must be less than to 2 for Child Adoption Leave.");
            }
        }
    });
}