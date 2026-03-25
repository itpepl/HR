import frappe


def on_submit(doc, method):
    """
    On Employee Transfer submit, sync the department-wise approver
    hierarchy (Reporting Manager, Review Manager, HR Manager) to the
    employee master from the newly transferred department.
    """
    new_department = None

    for row in doc.transfer_details:
        if row.property == "Department":
            new_department = row.new
            break

    if not new_department:
        return

    dept = frappe.get_doc("Department", new_department)

    employee = frappe.get_doc("Employee", doc.employee)

    # ── Clear existing approver tables ───────────────────────────────
    employee.set("custom_reporting_manager", [])
    employee.set("custom_review_manager", [])
    employee.set("custom_hr_manager", [])

    # ── Copy Reporting Manager rows ──────────────────────────────────
    for row in dept.get("custom_reporting_manager", []):
        employee.append("custom_reporting_manager", {
            "effective_from": row.effective_from,
            "role":           row.role,
            "user":           row.user,
            "employee":       row.employee,
        })

    # ── Copy Review Manager rows ─────────────────────────────────────
    for row in dept.get("custom_review_manager", []):
        employee.append("custom_review_manager", {
            "effective_from": row.effective_from,
            "role":           row.role,
            "user":           row.user,
            "employee":       row.employee,
        })

    # ── Copy HR Manager rows ─────────────────────────────────────────
    for row in dept.get("custom_hr_manager", []):
        employee.append("custom_hr_manager", {
            "effective_from": row.effective_from,
            "role":           row.role,
            "user":           row.user,
            "employee":       row.employee,
        })

    employee.flags.ignore_permissions = True
    employee.flags.ignore_validate = True
    employee.save()

    frappe.msgprint(
        f"Approver hierarchy updated for department <b>{new_department}</b>",
        alert=True,
        indicator="green"
    )