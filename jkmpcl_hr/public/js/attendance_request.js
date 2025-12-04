frappe.ui.form.on("Attendance Request", {
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