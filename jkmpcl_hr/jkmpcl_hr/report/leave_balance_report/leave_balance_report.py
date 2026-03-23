import frappe
from frappe.utils import flt, getdate, today
import calendar


def execute(filters=None):

    filters = frappe._dict(filters or {})

    from_date, to_date = get_date_range(filters)

    employees = get_employees(filters)

    data = []

    leave_types = get_leave_types(filters)

    fy_start = getdate(f"{from_date.year}-04-01")

    if from_date.month < 4:
        fy_start = getdate(f"{from_date.year - 1}-04-01")

    ledger_entries = get_leave_ledger_entries(fy_start, to_date)

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
                if fy_start <= entry.from_date < from_date:
                    # Casual Leave lapses every financial year
                    if lt == "Casual Leave" and entry.from_date < fy_start:
                        continue
                    
                    opening += leaves

                    if entry.transaction_type == "Leave Application":
                        availed_till_last_month += abs(leaves)
                    # opening += leaves
                    # availed_till_last_month += abs(leaves) if entry.transaction_type == "Leave Application" else 0

                # Inside period
                if fy_start <= entry.from_date <= to_date and entry.from_date >= from_date:

                    if entry.transaction_type == "Leave Allocation" and not entry.custom_is_penalty:
                        accrued += leaves

                    elif entry.transaction_type == "Leave Application":
                        availed += abs(leaves)

                    elif entry.custom_is_penalty:
                        deduction += abs(leaves)

            # row[f"{prefix}_opening"] = opening
            # row[f"{prefix}_accrued"] = accrued

            # ✅ For April month — override opening and accrued from
            # Leave Allocation document directly via Leave Ledger Entry
            is_april = (from_date.month == 4)
            if is_april and lt in ("Sick Leave", "Privilege Leave"):
                # Contractual and Probation employees accrue on 30-Apr
                # Confirmed and others accrue on 01-Apr
                is_monthly_accrual = emp.get("employment_type") in (
                    "Contractual", "Probation"
                )
                april_first = from_date  # always 01-04-yyyy
                april_last = getdate(f"{from_date.year}-04-30")

                accrual_date = april_last if is_monthly_accrual else april_first

                april_data = get_april_allocation_data(
                    emp.name, lt, april_first, accrual_date
                )
                opening = april_data["opening"]
                accrued = april_data["accrued"]

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
            designation,
            employment_type
        FROM `tabEmployee`
        {conditions}
    """,
        filters,
        as_dict=1,
    )

    return employees


# -------------------------------------------------------


def get_leave_ledger_entries(fy_start, to_date):

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
        WHERE from_date BETWEEN %s AND %s
        """,
        (fy_start, to_date),
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


# -------------------------------------------------------


def get_april_allocation_data(employee: str, leave_type: str, april_date, accrual_date=None) -> dict:
    """
    For April month only — fetch opening balance and new leaves allocated
    directly from the Leave Allocation document linked via Leave Ledger Entry.
    - april_date   → used to fetch opening balance (01-04-yyyy)
    - accrual_date → used to fetch accrued leaves
                     01-04-yyyy for Confirmed (from Leave Allocation doc)
                     30-04-yyyy for Contractual/Probation (from Leave Ledger Entry leaves field directly)
    Returns {"opening": 0, "accrued": 0}
    """
    if accrual_date is None:
        accrual_date = april_date

    # ── Opening balance → always from 01-Apr ledger entry ──────────
    opening_ledger = frappe.db.get_value(
        "Leave Ledger Entry",
        {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": april_date,
            "transaction_type": "Leave Allocation",
            "custom_is_penalty": 0,
            "docstatus": 1,
        },
        ["transaction_name"],
        as_dict=True,
    )

    opening = 0
    if opening_ledger and opening_ledger.transaction_name:
        allocation = frappe.db.get_value(
            "Leave Allocation",
            {
                "name": opening_ledger.transaction_name,
                "docstatus": 1,
            },
            ["custom_opening_balance"],
            as_dict=True,
        )
        if allocation:
            opening = flt(allocation.custom_opening_balance or 0)

    # ── Accrued → read directly from the Leave Ledger Entry leaves field
    # For Contractual/Probation the accrual entry on 30-Apr updates the
    # existing allocation — so new_leaves_allocated on the allocation doc
    # is not reliable. The actual accrued amount is in the ledger entry itself.
    accrual_ledger = frappe.db.get_value(
        "Leave Ledger Entry",
        {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": accrual_date,
            "transaction_type": "Leave Allocation",
            "custom_is_penalty": 0,
            "docstatus": 1,
        },
        ["transaction_name", "leaves"],
        as_dict=True,
    )

    accrued = 0
    if accrual_ledger:
        # ── Confirmed employees (accrual_date == april_date == 01-Apr):
        # fetch new_leaves_allocated from the Leave Allocation document
        if accrual_date == april_date:
            if accrual_ledger.transaction_name:
                allocation = frappe.db.get_value(
                    "Leave Allocation",
                    {
                        "name": accrual_ledger.transaction_name,
                        "docstatus": 1,
                    },
                    ["new_leaves_allocated"],
                    as_dict=True,
                )
                if allocation:
                    accrued = flt(allocation.new_leaves_allocated or 0)

        # ── Contractual/Probation (accrual_date == 30-Apr):
        # new_leaves_allocated on the allocation is unreliable since
        # monthly accrual only updates total_leaves_allocated.
        # Read the actual accrued amount directly from the ledger entry.
        else:
            accrued = flt(accrual_ledger.leaves or 0)

    return {"opening": opening, "accrued": accrued}
