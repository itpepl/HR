import frappe
from frappe.utils import flt, getdate, today
import calendar


def execute(filters=None):

    filters = frappe._dict(filters or {})

    from_date, to_date = get_date_range(filters)

    employees = get_employees(filters)

    ledger_entries = get_leave_ledger_entries(to_date)

    data = []

    leave_types = get_leave_types(filters)

    for emp in employees:

        row = {
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "branch": emp.branch,
            "designation": emp.designation,
        }

        for lt in leave_types:

            prefix = get_prefix(lt)

            opening = 0
            accrued = 0
            availed_till_last_month = 0
            availed = 0
            deduction = 0

            for entry in ledger_entries:

                if entry.employee != emp.name:
                    continue

                if entry.leave_type != lt:
                    continue

                leaves = flt(entry.leaves)

                # Opening balance
                if entry.from_date < from_date:
                    opening += leaves
                    availed_till_last_month += abs(leaves) if entry.transaction_type == "Leave Application" else 0

                # Inside period
                if from_date <= entry.from_date <= to_date:

                    if entry.transaction_type == "Leave Allocation" and not entry.custom_is_penalty:
                        accrued += leaves

                    elif entry.transaction_type == "Leave Application":
                        availed += abs(leaves)

                    elif entry.custom_is_penalty:
                        deduction += abs(leaves)

            row[f"{prefix}_opening"] = opening
            row[f"{prefix}_accrued"] = accrued
            row[f"{prefix}_availed_last_month"] = availed_till_last_month
            row[f"{prefix}_availed_current_month"] = availed
            row[f"{prefix}_deduction"] = deduction
            row[f"{prefix}_total_availed"] = (
                row.get(f"{prefix}_availed_last_month", 0) + row.get(f"{prefix}_availed_current_month", 0) + row.get(f"{prefix}_deduction", 0)
            )
            row[f"{prefix}_closing"] = (
                row.get(f"{prefix}_opening", 0) + row.get(f"{prefix}_accrued", 0) - row.get(f"{prefix}_availed_current_month", 0) - row.get(f"{prefix}_deduction", 0)
            )

        data.append(row)

    columns = get_columns(leave_types)

    return columns, data


# -------------------------------------------------------


def get_columns(leave_types):

    columns = [

        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120,
        },

        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150,
        },

        {
            "label": "Branch",
            "fieldname": "branch",
            "fieldtype": "Data",
            "width": 120,
        },

        {
            "label": "Designation",
            "fieldname": "designation",
            "fieldtype": "Data",
            "width": 140,
        },
    ]

    for lt in leave_types:

        prefix = get_prefix(lt)

        columns.extend(
            [
                {
                    "label": f"{prefix.upper()} Opening",
                    "fieldname": f"{prefix}_opening",
                    "fieldtype": "Float",
                    "width": 120,
                },
                {
                    "label": f"{prefix.upper()} Accrued",
                    "fieldname": f"{prefix}_accrued",
                    "fieldtype": "Float",
                    "width": 120,
                },
                {
                    "label": f"{prefix.upper()} Availed Till Last Month",
                    "fieldname": f"{prefix}_availed_last_month",
                    "fieldtype": "Float",
                    "width": 120,
                },
                {
                    "label": f"{prefix.upper()} Availed Current Month",
                    "fieldname": f"{prefix}_availed_current_month",
                    "fieldtype": "Float",
                    "width": 120,
                },
                {
                    "label": f"{prefix.upper()} Deduction",
                    "fieldname": f"{prefix}_deduction",
                    "fieldtype": "Float",
                    "width": 120,
                },
                {
                    "label": f"{prefix.upper()} Total Availed",
                    "fieldname": f"{prefix}_total_availed",
                    "fieldtype": "Float",
                    "width": 120,
                },
                {
                    "label": f"{prefix.upper()} Closing",
                    "fieldname": f"{prefix}_closing",
                    "fieldtype": "Float",
                    "width": 120,
                },
            ]
        )

    return columns


# -------------------------------------------------------


def get_date_range(filters):

    # Validate filters
    if not filters.get("month"):
        frappe.throw("Please select Month")

    if not filters.get("year"):
        frappe.throw("Please select Year")

    if not filters.get("as_on_date"):
        frappe.throw("As On Date is missing")

    # Month mapping
    month_map = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }

    month = month_map.get(filters.month)
    year = int(filters.year)

    # First date of selected month
    from_date = f"{year}-{month:02d}-01"

    # As On Date comes from JS logic
    to_date = filters.as_on_date

    return getdate(from_date), getdate(to_date)


# -------------------------------------------------------


def get_employees(filters):

    conditions = " WHERE status = 'Active' "

    if filters.branch:
        conditions += " AND branch = %(branch)s"

    if filters.employee:
        conditions += " AND name = %(employee)s"

    if filters.employment_type:
        conditions += " AND employment_type = %(employment_type)s"

    employees = frappe.db.sql(
        f"""
        SELECT
            name,
            employee_name,
            branch,
            designation
        FROM `tabEmployee`
        {conditions}
    """,
        filters,
        as_dict=1,
    )

    return employees


# -------------------------------------------------------


def get_leave_ledger_entries(to_date):

    return frappe.db.sql(
        """
        SELECT
            employee,
            leave_type,
            transaction_type,
            leaves,
            from_date,
            custom_is_penalty
        FROM `tabLeave Ledger Entry`
        WHERE from_date <= %s
        """,
        to_date,
        as_dict=1,
    )


# -------------------------------------------------------


def get_leave_types(filters):

    if filters.leave_type:
        return [filters.leave_type]

    return ["Casual Leave", "Privilege Leave", "Sick Leave"]


# -------------------------------------------------------


def get_prefix(leave_type):

    mapping = {
        "Casual Leave": "cl",
        "Privilege Leave": "pl",
        "Sick Leave": "sl",
    }

    return mapping.get(leave_type, leave_type.lower())