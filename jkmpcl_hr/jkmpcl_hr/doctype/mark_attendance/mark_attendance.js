// Copyright (c) 2026, SanskarTechnolab and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mark Attendance", {

    mark_attendance(frm) {

        if (!frm.doc.attendance_date) {
            frappe.msgprint("Please select Attendance Date first");
            return;
        }

        frappe.call({
            method: "mark_attendance_now",
            doc: frm.doc,
            freeze: true,
            freeze_message: "Marking attendance...",
            callback(r) {
                if (r.message?.success) {
                    frappe.msgprint(r.message.message);
                }
            }
        });
    }
});
