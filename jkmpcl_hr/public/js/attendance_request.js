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
        set_custom_shift_type(frm);
    },
    from_date: function(frm) {
        update_manual_punch_note(frm);
        set_custom_shift_type(frm);
    },
    reason: function(frm) {
        // if (frm.doc.reason === "Field Visit") {
        //     frm.set_df_property("custom_punch_type", "options", [
        //         "",
        //         "In",
        //         "Out"
        //     ]);
        // } else {
        //     frm.set_df_property("custom_punch_type", "options", [
        //         "",
        //         "In",
        //         "Out",
        //         "Both"
        //     ]);
        // }
        update_manual_punch_note(frm);
    },
    custom_punch_type: function(frm) {
        update_manual_punch_note(frm);
    },
    before_workflow_action: function (frm) {
        // Only intercept Approve action from Pending or Approved by HR
        if ((frm.doc.workflow_state === "Pending" || frm.doc.workflow_state === "Approved by HR") && frm.selected_workflow_action === "Approve") {
            return new Promise((resolve, reject) => {
                frappe.workflow.get_transitions(frm.doc).then(transitions => {
                    const selected_transition = transitions.find(t => t.action === frm.selected_workflow_action);
                    const target_state = selected_transition ? selected_transition.next_state : null;

                    // If target is not Final Approved, continue as normal
                    if (target_state !== "Final Approved") {
                        return resolve();
                    }

                    // Target is Final Approved -> call server method
                    frappe.call({
                        method: "jkmpcl_hr.overrides.attendance_request.create_auto_checkin_and_attendance",
                        args: { docname: frm.doc.name },
                        freeze: true
                    }).then(r => {
                        // ensure UI is unfrozen
                        try { frappe.unfreeze && frappe.unfreeze(); } catch (e) {}
                        const msg = (r && r.message && r.message.message) ? r.message.message : "Checkins / attendance created successfully.";
                        frappe.msgprint({ title: "Success", message: msg, indicator: "green" });
                        resolve();
                    }).catch(err => {
                        // ensure UI is unfrozen
                        try { frappe.unfreeze && frappe.unfreeze(); } catch (e) {}

                        // extract only the first server message
                        let server = err._server_messages || (err.responseJSON && err.responseJSON._server_messages) || null;
                        let errMsg = "";
                        if (server) {
                            try {
                                const arr = JSON.parse(server);
                                if (arr && arr.length) {
                                    try {
                                        const first = JSON.parse(arr[0]);
                                        errMsg = first.message || JSON.stringify(first);
                                    } catch (e) {
                                        errMsg = arr[0];
                                    }
                                } else {
                                    errMsg = err.exc || err.message || JSON.stringify(err);
                                }
                            } catch (e) {
                                errMsg = err.exc || err.message || String(err);
                            }
                        } else {
                            errMsg = err.exc || (err.responseJSON && err.responseJSON.exception) || err.message || JSON.stringify(err);
                        }

                        // show single error message and reject to stop workflow transition
                        // frappe.msgprint({ title: "Error", message: errMsg, indicator: "red" });
                        reject(err);
                    });
                }).catch(err => {
                    // If transitions can't be fetched, allow workflow to continue
                    console.error("Failed to fetch transitions:", err);
                    resolve();
                });
            });
        }
        // For all other actions / states, do nothing (workflow continues)
    }
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

    let allowed_role = res.message.allowed_role || null;

    let now = new Date();

    let options = ["", "Manual Punch", "Field Visit"];
    let show_system_error = false;

    // Condition 1 → Everyone during window
    if (from_time && to_time && now >= from_time && now <= to_time) {
        show_system_error = true;
    }
    // Condition 2 → HR Manager always
    else if (frappe.user.has_role(allowed_role)) {
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



function set_custom_shift_type(frm) {
    if (!frm.doc.employee || !frm.doc.from_date) {
        return;
    }
 
    frappe.call({
        method: "jkmpcl_hr.overrides.attendance_request.get_employee_custom_shift_type",
        args: {
            employee: frm.doc.employee,
            date: frm.doc.from_date
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value("custom_shift_type", r.message.custom_shift_type);
                frm.set_value("shift", r.message.shift_name); // optional
            } else {
                frm.set_value("custom_shift_type", null);
            }
        }
    });
}