import frappe

def on_update(doc, method):
    update_employee_child_tables(doc)


def update_employee_child_tables(dept_doc):

    old_doc = dept_doc.get_doc_before_save()

    # Mapping: Dept Child Table   → Employee Child Table
    table_mapping = {
        "custom_reporting_manager": "custom_reporting_manager",
        "custom_review_manager": "custom_review_manager",
        "custom_hr_manager": "custom_hr_manager"
    }

    for dept_table, emp_table in table_mapping.items():
        sync_child_table(dept_doc, old_doc, dept_table, emp_table)


def sync_child_table(dept_doc, old_doc, dept_table, emp_table):

    old_rows = getattr(old_doc, dept_table) if old_doc else []
    new_rows = getattr(dept_doc, dept_table)

    # Detect new rows
    old_keys = {(row.effective_from, row.user) for row in old_rows}
    added_rows = []

    for row in new_rows:
        key = (row.effective_from, row.user)
        if key not in old_keys:
            added_rows.append(row)

    if not added_rows:
        return

    # Get employees of this department
    employees = frappe.get_all(
        "Employee",
        filters={"department": dept_doc.name},
        fields=["name"]
    )

    for emp in employees:
        emp_doc = frappe.get_doc("Employee", emp.name)

        for row in added_rows:

            # Prevent duplicate rows in Employee
            exists = any(
                (r.effective_from == row.effective_from and r.user == row.user)
                for r in getattr(emp_doc, emp_table)
            )

            if not exists:
                emp_doc.append(emp_table, {
                    "effective_from": row.effective_from,
                    "role": row.role,
                    "user": row.user,
                    "employee": row.employee
                })

        emp_doc.save(ignore_permissions=True)
