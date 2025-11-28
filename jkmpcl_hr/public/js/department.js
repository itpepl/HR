frappe.ui.form.on("Department", {
    onload: function(frm) {
        // set up filters for all three child tables on load
        setup_user_filters(frm);
    }
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
