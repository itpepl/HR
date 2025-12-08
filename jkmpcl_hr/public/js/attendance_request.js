frappe.ui.form.on("Attendance Request", {
    onload: function(frm) {
        add_reason_option_based_on_role(frm);

        if (!frm.doc.employee) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Employee",
                    filters: { "user_id": frappe.session.user },
                    fieldname: "name"
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("employee", r.message.name);
                    }
                }
            });
        }

        if (!frm.doc.from_date) {
            frm.set_value("from_date", frappe.datetime.get_today());
        }
    },
    refresh: function(frm) {
        add_reason_option_based_on_role(frm);
    },
    employee: function(frm) {
        update_manual_punch_note(frm);
    },
    from_date: function(frm) {
        update_manual_punch_note(frm);
    },
    reason: function(frm) {
        update_manual_punch_note(frm);
    },
    custom_punch_type: function(frm) {
        update_manual_punch_note(frm);
    },
});


// Function to add extra option SYSTEM ERROR if user has HR role
function add_reason_option_based_on_role(frm) {
    if (!frm.doc) return;

    // Check if user has HR role
    const has_hr_role = frappe.user_roles.includes("HR Manager");

    if (has_hr_role) {
        // Add option if not already added
        if (!frm.fields_dict.reason.df.options.includes("System Error")) {
            frm.fields_dict.reason.df.options += "\nSystem Error";
            frm.refresh_field("reason");
        }
    }
}

function update_manual_punch_note(frm) {
    if (!frm.doc.employee || !frm.doc.from_date || frm.doc.reason !== "Manual Punch" ||  (frm.doc.custom_punch_type !== "In" && frm.doc.custom_punch_type !== "Out")) {
        frm.set_value("custom_note", "");
        frm.refresh_field("custom_note");
        return;
    }

    frappe.call({
        method: "jkmpcl_hr.overrides.attendance_request.get_manual_punch_note_html",
        args: {
            employee: frm.doc.employee,
            from_date: frm.doc.from_date,
        },
        callback: function(r) {
            if (r.message) {
                const html = r.message.html || "";

                frm.set_value("custom_note", html);
                frm.refresh_field("custom_note");
            }
        }
    });
}