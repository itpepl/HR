// Copyright (c) 2026, SanskarTechnolab and contributors
// For license information, please see license.txt

frappe.ui.form.on("Generate Comp Off", {

    generate_for_date(frm) {
        frm.save()
    },
	generate(frm) {

        if (!frm.doc.generate_for_date) {
            frappe.msgprint("Please select Date first");
            return;
        }

        frappe.call({
            method: "generate_comp_off",
            doc: frm.doc,
            freeze: true,
            freeze_message: "Generating CompOff...",
            callback(r) {
                if (r.message?.success) {
                    frappe.msgprint(r.message.message);
                }
            }
        });
    }
});
