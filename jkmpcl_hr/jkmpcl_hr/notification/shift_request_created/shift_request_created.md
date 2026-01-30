<p>Hello {{frappe.db.get_value("Employee", {"user_id": doc.approver}, "employee_name")}}</p>

<p>A new Shift Request has been submitted and is awaiting your approval.</p>
