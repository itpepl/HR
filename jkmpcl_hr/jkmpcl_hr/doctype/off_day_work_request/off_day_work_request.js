// Copyright (c) 2025, SanskarTechnolab and contributors
// For license information, please see license.txt


frappe.ui.form.on("Off-Day Work Request", {
    date(frm) {
        if (!frm.doc.employee || !frm.doc.date) return;

        frappe.call({
            method: "jkmpcl_hr.jkmpcl_hr.doctype.off_day_work_request.off_day_work_request.check_working_day_valid",
            args: {
                employee: frm.doc.employee,
                date: frm.doc.date
            },
            callback(r) {
                if (!r.message) {
                    frappe.msgprint({
                        title: "Invalid Date",
                        message: "Selected date is not a Week-Off or Holiday for this employee.",
                        indicator: "red"
                    });
                    // frm.set_value("date", null);
                }
            }
        });
    }
});
