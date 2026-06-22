// Copyright (c) 2026, SanskarTechnolab and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tour Request", {
    refresh: function(frm) {
        // Check if the document is new
        if (frm.is_new()) {
            // Get the current user
            const current_user = frappe.session.user;
            
            // Fetch employee details for the current user
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Employee",
                    filters: {
                        "user_id": current_user
                    },
                    fields: ["name", "employee_name"],
                    limit: 1
                },
                callback: function(response) {
                    if (response.message && response.message.length > 0) {
                        const employee = response.message[0];
                        
                        // Set the employee and employee_name fields
                        frm.set_value("employee", employee.name);
                        frm.set_value("employee_name", employee.employee_name);
                        
                        // Refresh the fields to show updated values
                        frm.refresh_field("employee");
                        frm.refresh_field("employee_name");
                    } else {
                        // Optional: Show a message if no employee found
                        frappe.msgprint({
                            title: __('No Employee Found'),
                            message: __('No employee is linked to your user account. Please contact your administrator.'),
                            indicator: 'orange'
                        });
                    }
                }
            });
        }
    }
});