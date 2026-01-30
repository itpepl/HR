frappe.ui.form.on("Leave Allocation", {
    
    
    new_leaves_allocated(frm) {
        
        frm.set_value(
			"total_leaves_allocated",
			flt(frm.doc.unused_leaves) + flt(frm.doc.new_leaves_allocated) + flt(frm.doc.custom_opening_balance)
		);
    }
})