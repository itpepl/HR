import frappe
from frappe.utils import getdate


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


# def sync_child_table(dept_doc, old_doc, dept_table, emp_table):

#     old_rows = getattr(old_doc, dept_table) if old_doc else []
#     new_rows = getattr(dept_doc, dept_table)

#     # Detect new rows
#     old_keys = {(row.effective_from, row.user) for row in old_rows}
#     added_rows = []

#     for row in new_rows:
#         key = (row.effective_from, row.user)
#         if key not in old_keys:
#             added_rows.append(row)

#     if not added_rows:
#         return

#     # Get employees of this department
#     employees = frappe.get_all(
#         "Employee",
#         filters={"department": dept_doc.name},
#         fields=["name"]
#     )

#     for emp in employees:
#         emp_doc = frappe.get_doc("Employee", emp.name)

#         for row in added_rows:

#             # Prevent duplicate rows in Employee
#             exists = any(
#                 (r.effective_from == row.effective_from and r.user == row.user)
#                 for r in getattr(emp_doc, emp_table)
#             )

#             if not exists:
#                 emp_doc.append(emp_table, {
#                     "effective_from": row.effective_from,
#                     "role": row.role,
#                     "user": row.user,
#                     "employee": row.employee
#                 })

#         emp_doc.save(ignore_permissions=True)

def sync_child_table(dept_doc, old_doc,dept_table, emp_table):
    """
    For each Employee in this department where EMPLOYEE_SYNC_SKIP_FIELD is NOT checked:
    - Clear the Employee child table
    - Copy ALL current rows from the Department child table
    """

    new_rows = list(getattr(dept_doc, dept_table) or [])
    old_rows = list(getattr(old_doc, dept_table) or []) if old_doc else []

    def row_key(row):
        return (
            getdate(row.effective_from) if row.effective_from else None,
            getattr(row, "role", None),
            getattr(row, "user", None),
            getattr(row, "employee", None),
        )

    table_changed = False

    if not old_doc:
        table_changed = True
    else:
        if len(old_rows) != len(new_rows):
            table_changed = True
        else:
            for old_row, new_row in zip(old_rows, new_rows):
                if row_key(old_row) != row_key(new_row):
                    print(f"\n\n {row_key(old_row)} {row_key(new_row)}\n\n")
                    table_changed = True
                    break

    if not table_changed:
        print(f"\n\n {dept_table} not changed CHANGEd\n\n")
        return
    else:
        print(f"\n\n {dept_table} CHANGEd\n\n")
        


    employees = frappe.get_all(
        "Employee",
        filters={
            "department": dept_doc.name,
            # only sync if checkbox is unchecked (0 or null)
            "custom_stop_auto_update": ["in", [0, None]],
        },
        pluck="name",
    )

    for emp_name in employees:
        emp_doc = frappe.get_doc("Employee", emp_name)

        emp_doc.set(emp_table, [])

        for row in new_rows:
            emp_doc.append(emp_table, {
                "effective_from": row.effective_from,
                "role": row.role,
                "user": row.user,
                "employee": row.employee,
            })

        emp_doc.save(ignore_permissions=True)
