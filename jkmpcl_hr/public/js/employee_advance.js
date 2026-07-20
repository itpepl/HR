frappe.ui.form.on('Employee Advance', {
    onload: function(frm) {
        toggle_claim_advance_fields(frm);
        set_date_restrictions(frm);
    },
    refresh: function(frm) {
        toggle_claim_advance_fields(frm);
        set_date_restrictions(frm);
        // if (frm.doc.docstatus === 0 && !frm.doc.employee) {
		// 	frappe.msgprint(__("Please select employee first"));
		// }
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
    },
    setup: function (frm) {
		frm.set_query("advance_account", function () {
			return {
				filters: {
					root_type: "Asset",
					is_group: 0,
					company: frm.doc.company,
					account_currency: frm.doc.currency,
					account_type: "Receivable",
				},
			};
		});
	},
    custom_claim_amount: function(frm) {
        if (frm.is_new()) {
            frm.set_value('advance_amount', frm.doc.custom_claim_amount);
        }
    },
    custom_from_date: function(frm) {
        validate_date_not_past(frm, 'custom_from_date');
    },
    custom_to_date: function(frm) {
        validate_date_not_past(frm, 'custom_to_date');
    },
    validate: function(frm) {
        // Runs automatically before save; return false / throw to block save
        validate_date_not_past(frm, 'custom_from_date');
        validate_date_not_past(frm, 'custom_to_date');
    }
});

function toggle_claim_advance_fields(frm) {
    if (frm.is_new()) {
        frm.set_df_property('custom_claim_amount', 'read_only', 0);
        frm.set_df_property('advance_amount', 'read_only', 1);
    } else {
        frm.set_df_property('custom_claim_amount', 'read_only', 1);
        frm.set_df_property('advance_amount', 'read_only', 0);
    }
    frm.refresh_field('custom_claim_amount');
    frm.refresh_field('advance_amount');
}

function set_date_restrictions(frm) {
    if (frm.fields_dict.custom_from_date && frm.fields_dict.custom_from_date.datepicker) {
        frm.fields_dict.custom_from_date.datepicker.update({ minDate: new Date() });
    }
    if (frm.fields_dict.custom_to_date && frm.fields_dict.custom_to_date.datepicker) {
        frm.fields_dict.custom_to_date.datepicker.update({ minDate: new Date() });
    }
}

function validate_date_not_past(frm, fieldname) {
    const value = frm.doc[fieldname];
    if (!value) return;

    const today = frappe.datetime.get_today();
    if (value < today) {
        frappe.msgprint(__("{0} cannot be a date in the past.", [frappe.meta.get_label(frm.doctype, fieldname)]));
        frappe.validated = false; // blocks save
        frm.set_value(fieldname, "");
    }
}