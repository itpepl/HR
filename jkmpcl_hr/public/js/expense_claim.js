frappe.ui.form.on('Expense Claim', {
    custom_expense_claim_type: function (frm) {
        if (frm.doc.custom_expense_claim_type === "LTA") {
            frm.set_value("naming_series", "HR-LTA-.YYYY.-");
        } else {
            // Optional: Set default naming series
            frm.set_value("naming_series", "HR-EXP-.YYYY.-");
        }
    },
    // =====================================================
    // On Employee Selection
    // Set current fiscal LTA period + previous availed period (if any)
    // =====================================================
    employee: function (frm) {

        if (!frm.doc.employee) {
            frm.set_value('custom_lta_period_from', '');
            frm.set_value('custom_lta_period_to', '');
            frm.set_value('custom_period_of_last_lta_availed_from', '');
            frm.set_value('custom_period_of_last_lta_availed_to', '');
            return;
        }

        frappe.call({
            method: "jkmpcl_hr.py.expense_claim.get_fiscal_periods",
            args: {
                employee: frm.doc.employee,
                expense_claim: frm.doc.name
            },
            callback: function (r) {
                if (!r.message) return;

                frm.set_value('custom_lta_period_from', r.message.lta_period_from);
                frm.set_value('custom_lta_period_to', r.message.lta_period_to);

                // Only populated if a previous fiscal year claim exists, else blank
                frm.set_value('custom_period_of_last_lta_availed_from', r.message.last_availed_from || '');
                frm.set_value('custom_period_of_last_lta_availed_to', r.message.last_availed_to || '');
            }
        });

        // Recalculate leave breakdown if Period Of Leave is already filled
        calculate_lta_days(frm);
    },

    // =====================================================
    // On Period Of Leave From/To Change
    // Auto-calculate CL / PL / PH / WO + sanctioned days
    // =====================================================
    custom_period_of_leave_from: function (frm) {
        calculate_lta_days(frm);
    },

    custom_period_of_leave_to: function (frm) {
        calculate_lta_days(frm);
    },
    onload: function (frm) {
		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);

		if (frm.doc.docstatus == 0) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_mandatory_approval",
				args: {
					doctype: frm.doc.doctype,
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.toggle_reqd("expense_approver", false);
					}
				},
			});
		}

		frm.trigger("update_fields_label");
		frm.trigger("update_child_fields_label");
	},

});


// =====================================================
// Shared function: fetch CL/PL/PH/WO breakdown + sanctioned days
// =====================================================
function calculate_lta_days(frm) {

    if (!frm.doc.employee || !frm.doc.custom_period_of_leave_from || !frm.doc.custom_period_of_leave_to) {
        return;
    }

    frappe.call({
        method: "jkmpcl_hr.py.expense_claim.get_lta_leave_details",
        args: {
            employee: frm.doc.employee,
            period_from: frm.doc.custom_period_of_leave_from,
            period_to: frm.doc.custom_period_of_leave_to
        },
        callback: function (r) {
            if (!r.message) return;

            frm.set_value('custom_cl', r.message.cl_count);
            frm.set_value('custom_pl', r.message.pl_count);
            frm.set_value('custom_ph', r.message.ph_count);
            frm.set_value('custom_wo', r.message.wo_count);
            frm.set_value('custom_total', r.message.total_days);
            frm.set_value('custom_availed_or_sanctioned_no_of_days', r.message.sanctioned_days);
        }
    });
}