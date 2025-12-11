frappe.ui.form.on("Attendance Request", {
    onload: function(frm) {
        add_reason_option_based_on_role(frm);

        if (!frm.doc.employee) {
            frappe.call({
                method: "jkmpcl_hr.overrides.attendance_request.get_employee_for_session_user",
                callback: function(r) {
                    if (r.message && r.message.employee) {
                        frm.set_value("employee", r.message.employee);
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
        if (frm.doc.reason === "Field Visit") {
            frm.set_df_property("custom_punch_type", "options", [
                "",
                "In",
                "Out"
            ]);
        } else {
            frm.set_df_property("custom_punch_type", "options", [
                "",
                "In",
                "Out",
                "Both"
            ]);
        }
        update_manual_punch_note(frm);
    },
    custom_punch_type: function(frm) {
        update_manual_punch_note(frm);
    },
});


async function add_reason_option_based_on_role(frm) {
    let res = await frappe.call({
        method: "jkmpcl_hr.overrides.attendance_request.get_system_error_window"
    });

    let from_time = res.message.from_time
        ? frappe.datetime.str_to_obj(res.message.from_time)
        : null;

    let to_time = res.message.to_time
        ? frappe.datetime.str_to_obj(res.message.to_time)
        : null;

    let now = new Date();

    let options = ["", "Manual Punch", "Field Visit"];
    let show_system_error = false;

    // Condition 1 → Everyone during window
    if (from_time && to_time && now >= from_time && now <= to_time) {
        show_system_error = true;
    }
    // Condition 2 → HR Manager always
    else if (frappe.user.has_role("HR Manager")) {
        show_system_error = true;
    }

    if (show_system_error) {
        options.push("System Error");
    }

    frm.set_df_property("reason", "options", options);
}


function update_manual_punch_note(frm) {
    if (!frm.doc.employee || !frm.doc.from_date || frm.doc.reason !== "Manual Punch" ||  !frm.doc.custom_punch_type ) {
        frm.set_value("custom_note", "");
        frm.refresh_field("custom_note");
        return;
    }

    const current_name = (frm.doc.name && frm.doc.name !== "New Attendance Request") ? frm.doc.name : null;
    const current_punch_type = frm.doc.custom_punch_type || null;

    frappe.call({
        method: "jkmpcl_hr.overrides.attendance_request.get_manual_punch_note_html",
        args: {
            employee: frm.doc.employee,
            from_date: frm.doc.from_date,
            current_punch_type: current_punch_type,
            current_name: current_name
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