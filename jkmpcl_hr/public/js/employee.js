frappe.ui.form.on("Employee", {
    onload: function(frm) {
        // set up filters for all three child tables on load
        setup_user_filters(frm);
    },

    refresh: function(frm){
        if(frm.doc.branch){
            // frm.set_query("default_shift", function(){
            //     return{
            //         filters:{
            //             custom_branch: frm.doc.branch
            //         }
            //     }
            // })
            apply_filter_in_shift_type(frm)
        }
    },
    department: async function (frm) {
        // if (!frm.is_new()) return;
        if (frm.doc.custom_stop_auto_update) return;

        const child_tables = [
            "custom_reporting_manager",
            "custom_review_manager",
            "custom_hr_manager"
        ];

        // clear all child tables
        child_tables.forEach(tbl => frm.clear_table(tbl));
        if (!frm.doc.department) {
            child_tables.forEach(tbl => frm.refresh_field(tbl));
            return;
        }

        // reference date: use date_of_joining if provided else today's date
        const ref_date = frappe.datetime.get_today();
        const refTime = new Date(ref_date).getTime();

        // fetch data for all three tables at once
        const all_data = await frappe.xcall('jkmpcl_hr.py.api.get_reporting_managers', {
            department: frm.doc.department
        }).catch(() => ({}));

        // populate each child table from the result
        for (const parentfield of child_tables) {
            const rows = all_data[parentfield] || [];

            if (!rows.length) {
                frm.refresh_field(parentfield);
                continue;
            }

            // keep entries with effective_from, sort ascending
            const sorted = rows
                .filter(r => r.effective_from)
                .map(r => ({
                    employee: r.employee,
                    role: r.role,
                    user: r.user,
                    effective_from: r.effective_from
                }))
                .sort((a, b) => new Date(a.effective_from) - new Date(b.effective_from));

            // find last index with effective_from <= ref_date
            let currentIndex = -1;
            for (let i = 0; i < sorted.length; i++) {
                if (new Date(sorted[i].effective_from).getTime() <= refTime) {
                    currentIndex = i;
                } else {
                    break;
                }
            }

            const startIndex = currentIndex >= 0 ? currentIndex : 0;

            for (let i = startIndex; i < sorted.length; i++) {
                const r = sorted[i];
                const child = frm.add_child(parentfield);
                child.effective_from = r.effective_from;
                child.role = r.role;
                child.user = r.user;
                child.employee = r.employee;
            }

            frm.refresh_field(parentfield);
        }
    },
    
    branch: function (frm) {
        
        frm.set_value("default_shift", "")
        if(frm.doc.branch){
            apply_filter_in_shift_type(frm)
        }
    },
    custom_attendance_source: function (frm) {
        frm.set_value("default_shift", "")
    }
    // default_shift: function(frm){
    //     if(frm.doc.branch){
    //         frm.set_query("default_shift", function(){
    //              return{
    //                 filters:{
    //                     custom_branch: frm.doc.branch
    //                 }
    //              }
    //         })
    //     }
    // }


});

frappe.ui.form.on("Approver", {
    role: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Clear user field when role changes
        frappe.model.set_value(cdt, cdn, "user", "");

        // Re-apply filters after role change
        setup_user_filters(frm);
    },
    
    user: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // if no user selected, clear employee
        if (!row.user) {
            frappe.model.set_value(cdt, cdn, "employee", "");
            return;
        }

        // fetch employee linked with this user
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Employee",
                filters: { "user_id": row.user },
                fieldname: ["name", "employee_name"]
            },
            callback: function(r) {
                if (r.message && r.message.name) {
                    // set the employee field
                    frappe.model.set_value(cdt, cdn, "employee", r.message.name);
                } else {
                    frappe.model.set_value(cdt, cdn, "employee", "");
                }
            }
        });
    }
});

function setup_user_filters(frm) {
    const child_tables = ["custom_reporting_manager", "custom_review_manager", "custom_hr_manager"];

    child_tables.forEach(function(table_name) {
        if (frm.fields_dict[table_name]) {
            frm.fields_dict[table_name].grid.get_field("user").get_query = function(doc, cdt, cdn) {
                const row = locals[cdt][cdn];

                // if no role selected, show all users
                if (!row || !row.role) {
                    return {};
                }

                // filter users by selected role
                return {
                    query: "jkmpcl_hr.py.api.get_users_with_role",
                    filters: { role: row.role }
                };
            };
        }
    });
}

// * FUNCTION TO APPLY FILTER ON shift_type FIELD
function apply_filter_in_shift_type(frm){
    frm.set_query("default_shift", function () {
        return {
            query: "jkmpcl_hr.py.api.determine_shift_types",
            filters: {
                branch: frm.doc.branch,
                as_on_date: frappe.datetime.get_today(),
                emp_id: frm.doc.name,
                gender: frm.doc.gender,
                attendance_source: frm.doc.custom_attendance_source
            }
        };
    });
}