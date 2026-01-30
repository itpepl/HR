frappe.ui.form.on("HR Settings", {
    custom_system_error_window_from(frm) {
        validate_window(frm);
    },

    custom_system_error_window_to(frm) {
        validate_window(frm);
    }
});


function validate_window(frm) {
    let start = frm.doc.custom_system_error_window_from;
    let end = frm.doc.custom_system_error_window_to;

    if (start && end) {
        // Convert to JS datetime objects
        let start_dt = frappe.datetime.str_to_obj(start);
        let end_dt = frappe.datetime.str_to_obj(end);

        if (end_dt < start_dt) {
            frappe.msgprint({
                title: "Invalid Date Range",
                message: "'System Error Window To' cannot be earlier than 'From' date.",
                indicator: "red"
            });

            // Reset the field
            frm.set_value("custom_system_error_window_to", "");
        }
    }
}
