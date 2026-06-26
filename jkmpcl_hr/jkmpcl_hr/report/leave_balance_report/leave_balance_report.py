# ---------------------------------------- Leave Required Report Updated Code (08-04-2026) ----------------------------------------

# ----------------------------- Latest UPDATED CODE (08-04-2026) -------------------------------

# ----------------------------- Latest UPDATED CODE (26-06-2026) as per bug 354190 -------------------------------
import frappe
from frappe.utils import flt, getdate, today
import calendar
from datetime import timedelta



# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

NEW_SCHEME_START    = getdate("2025-12-01")   # first accrual date of FY 2025
FY2025_OPENING_DATE = getdate("2025-11-30")   # opening snapshot date for FY 2025
FY2026_START        = getdate("2026-04-01")   # first day of FY 2026 and beyond


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTE
# ─────────────────────────────────────────────────────────────────────────────

def execute(filters=None):

    filters = frappe._dict(filters or {})

    # from_date → 1st of the filtered month
    # to_date   → last date of the filtered month (or today if current month)
    from_date, to_date = get_date_range(filters)

    employees   = get_employees(filters)
    leave_types = get_leave_types(filters)

    # ── Determine which Financial Year window we are in ───────────────────────
    fy_accrual_start, opening_date = get_fy_boundaries(from_date)

    is_fy2025 = (opening_date == FY2025_OPENING_DATE)

    # ── Fetch ALL relevant ledger entries in one query ────────────────────────
    ledger_entries = get_leave_ledger_entries(opening_date, to_date)
    leave_applications = get_leave_applications(opening_date, to_date)
    # ── Pre-fetch custom_opening_balance for SL allocations on opening_date ──
    # Only needed for FY 2026+ where SL opening = custom_opening_balance
    # from the linked Leave Allocation document.
    sl_opening_balance_map = {}
    # if not is_fy2025:
    #     sl_opening_balance_map = get_sl_custom_opening_balances(
    #         ledger_entries, opening_date
    #     )

    # ── Previous-month boundaries ─────────────────────────────────────────────
    # availed_prev_end  : last day of previous month  (None for first FY month)
    # prev_month_start  : first day of previous month (None for first FY month)
    #
    # "Availed Till Last Month" accumulates:
    #   • Leave Applications  from fy_accrual_start → availed_prev_end
    #   • Penalty deductions  from prev_month_start → availed_prev_end ONLY
    #     (i.e. deductions of the previous month, not the whole FY)

    is_first_month_of_fy = (
        from_date == fy_accrual_start          # covers FY 2025 December case
        or (
            not is_fy2025                      # FY 2026+ only
            and from_date == opening_date      # April = first month of FY
        )
    )

    if is_first_month_of_fy:
        availed_prev_end = None
        prev_month_start = None
    else:
        # Last day of previous month
        availed_prev_end = add_days(from_date, -1)
        # First day of previous month
        prev_month_start = getdate(
            f"{availed_prev_end.year}-{availed_prev_end.month:02d}-01"
        )

    data = []

    for emp in employees:

        row = {
            "employee":      emp.name,
            "employee_name": emp.employee_name,
            "branch":        emp.branch,
            "designation":   emp.designation,
        }

        is_monthly_accrual_emp = emp.get("employment_type") in (
            "Contractual", "Probation"
        )

        for lt in leave_types:

            prefix = get_prefix(lt)

            opening               = 0.0
            accrued               = 0.0
            availed_till_last_mth = 0.0
            availed_current_mth   = 0.0
            deduction_current_mth = 0.0

            for entry in ledger_entries:

                if entry.employee   != emp.name: continue
                if entry.leave_type != lt:        continue

                leaves     = flt(entry.leaves)
                e_date     = getdate(entry.from_date)
                txn_type   = entry.transaction_type
                is_penalty = entry.custom_is_penalty

                # ── 1. OPENING BALANCE ────────────────────────────────────────
                #
                # FY 2025:
                #   All leave types: entries on 30-Nov-2025, Leave Allocation,
                #   not penalty → Opening.
                #
                # FY 2026+:
                #   CL  : Always 0. The 01-Apr CL allocation → Accrued.
                #   SL  : Entry on 01-Apr-YYYY, Leave Allocation, not penalty.
                #         Fetch custom_opening_balance from the linked Leave
                #         Allocation doc (via transaction_name). That value is
                #         the SL Opening Balance. The remainder (new grant)
                #         goes to Accrued.
                #   PL  : Entry on 01-Apr-YYYY, Leave Allocation, not penalty.
                #         Use leaves directly from the ledger entry as Opening
                #         (this is the carry-forward balance).
                #         Monthly accrual entries after 01-Apr → Accrued.

                if (
                    e_date == opening_date
                    and txn_type == "Leave Allocation"
                    and not is_penalty
                ):
                    if is_fy2025:
                        # FY 2025: all opening allocations on 30-Nov-2025 → Opening
                        opening += leaves

                    else:
                        # FY 2026+
                        if lt == "Casual Leave":
                            # CL lapses at year-end → 01-Apr allocation goes to Accrued
                            accrued += leaves

                        elif lt == "Sick Leave":
                            # SL Opening = custom_opening_balance from the linked
                            # Leave Allocation document. Remainder = new grant → Accrued.
                            key = (emp.name, lt)
                            custom_ob = sl_opening_balance_map.get(key, 0.0)
                            opening += custom_ob
                            new_grant = leaves - custom_ob
                            if new_grant > 0:
                                accrued += new_grant

                        elif lt == "Privilege Leave":
                            # PL: the 01-Apr-YYYY ledger entry is the carry-forward.
                            # Use leaves directly as Opening Balance.
                            opening += leaves

                # ── 2. ACCRUED ────────────────────────────────────────────────
                #
                # FY 2025 : fy_accrual_start (01-Dec-2025) → to_date
                # FY 2026+: fy_accrual_start (02-Apr-YYYY) → to_date
                # Leave Allocation entries that are not penalties.
                # 01-Apr entries are handled in block 1 above and naturally
                # excluded here because fy_accrual_start = 02-Apr for FY 2026+.

                elif (
                    fy_accrual_start <= e_date <= to_date
                    and txn_type == "Leave Allocation"
                    and not is_penalty
                ):
                    accrued += leaves

                # ── 3. AVAILED TILL LAST MONTH — Leave Applications ───────────
                # Leave Applications (not penalty) from fy_accrual_start up to
                # end of the previous month.
                # Zero for the very first month of the FY.

                # elif (
                #     availed_prev_end is not None
                #     and opening_date <= e_date <= availed_prev_end
                #     and txn_type == "Leave Application"
                #     and not is_penalty
                # ):
                #     availed_till_last_mth += abs(leaves)

                # ── 3b. AVAILED TILL LAST MONTH — Previous-month deductions ───
                # Penalty Leave Allocations from FINANCIAL YEAR START up to
                # end of previous month (opening_date → availed_prev_end).

                # elif (
                #     prev_month_start is not None
                #     and availed_prev_end is not None
                #     and opening_date <= e_date <= availed_prev_end
                #     and txn_type == "Leave Allocation"
                #     and is_penalty
                # ):
                #     availed_till_last_mth += abs(leaves)

                # ── 4. AVAILED CURRENT MONTH ─────────────────────────────────
                # Leave Application entries (not penalty) within the filtered
                # month only (from_date → to_date).

                # elif (
                #     from_date <= e_date <= to_date
                #     and txn_type == "Leave Application"
                #     and not is_penalty
                # ):
                #     availed_current_mth += abs(leaves)

                # ── 5. DEDUCTION CURRENT MONTH ────────────────────────────────
                # Penalty Leave Allocations within the current filtered month
                # only (from_date → to_date). NOT cumulative from FY start.

                elif (
                    from_date <= e_date <= to_date
                    and txn_type == "Leave Allocation"
                    and is_penalty
                ):
                    deduction_current_mth += abs(leaves)
            # ------------------------------------------------------------------
            # Calculate Leave Application month-wise
            # ------------------------------------------------------------------

            for leave in leave_applications:

                # Employee check
                if leave.employee != emp.name:
                    continue

                # Leave Type check
                if leave.leave_type != lt:
                    continue

                leave_from = getdate(leave.from_date)
                leave_to = getdate(leave.to_date)

                # --------------------------------------------------------------
                # Availed Till Last Month
                # --------------------------------------------------------------
                if availed_prev_end:

                    availed_till_last_mth += get_leave_days_in_period(
                        leave_from,
                        leave_to,
                        opening_date,
                        availed_prev_end
                    )

                # --------------------------------------------------------------
                # Availed Current Month
                # --------------------------------------------------------------
                availed_current_mth += get_leave_days_in_period(
                    leave_from,
                    leave_to,
                    from_date,
                    to_date
                )
            # ── 6 & 7. DERIVED COLUMNS ────────────────────────────────────────
            total_availed = availed_till_last_mth + availed_current_mth + deduction_current_mth
            closing       = opening + accrued - total_availed

            row[f"{prefix}_opening"]               = opening
            row[f"{prefix}_accrued"]               = accrued
            row[f"{prefix}_availed_last_month"]    = availed_till_last_mth
            row[f"{prefix}_availed_current_month"] = availed_current_mth
            row[f"{prefix}_deduction"]             = deduction_current_mth
            row[f"{prefix}_total_availed"]         = total_availed
            row[f"{prefix}_closing"]               = closing

        data.append(row)

    columns = get_columns(leave_types)
    return columns, data



def get_leave_days_in_period(
    leave_from,
    leave_to,
    report_from,
    report_to
):

    start = max(leave_from, report_from)
    end = min(leave_to, report_to)

    if start > end:
        return 0

    return (end - start).days + 1

def get_leave_applications(fetch_from, fetch_to):

    return frappe.db.sql(
        """
        SELECT

            employee,
            leave_type,
            from_date,
            to_date,
            total_leave_days

        FROM `tabLeave Application`

        WHERE

            docstatus = 1
            AND status = 'Approved'

            AND to_date >= %s
            AND from_date <= %s

        """,
        (fetch_from, fetch_to),
        as_dict=True,
    )
# ─────────────────────────────────────────────────────────────────────────────
# HELPER: SL CUSTOM OPENING BALANCE PRE-FETCH
# ─────────────────────────────────────────────────────────────────────────────

def get_sl_custom_opening_balances(ledger_entries, opening_date):
    """
    For FY 2026+, find all Sick Leave ledger entries posted on opening_date
    (01-Apr-YYYY) with transaction_type = "Leave Allocation" and not penalty.
    For each, fetch the linked Leave Allocation document via transaction_name
    and read the custom_opening_balance field.

    Returns a dict keyed by (employee, leave_type) → custom_opening_balance.
    """
    result = {}

    for entry in ledger_entries:
        if entry.leave_type         != "Sick Leave":       continue
        if getdate(entry.from_date) != opening_date:       continue
        if entry.transaction_type   != "Leave Allocation": continue
        if entry.custom_is_penalty:                        continue

        transaction_name = entry.get("transaction_name")
        if not transaction_name:
            continue

        try:
            custom_ob = frappe.db.get_value(
                "Leave Allocation",
                transaction_name,
                "custom_opening_balance"
            )
            key = (entry.employee, entry.leave_type)
            result[key] = flt(custom_ob)
        except Exception:
            result[(entry.employee, entry.leave_type)] = 0.0
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: FY BOUNDARIES
# ─────────────────────────────────────────────────────────────────────────────

def get_fy_boundaries(from_date):
    """
    Returns (fy_accrual_start, opening_date) for the given report month.

    FY 2025  (Dec-2025 to Mar-2026)
        fy_accrual_start = 2025-12-01
        opening_date     = 2025-11-30

    FY 2026+ (Apr-YYYY to Mar-YYYY+1)
        fy_accrual_start = YYYY-04-02   (day after opening_date, to avoid
                                          double-counting the 01-Apr allocation)
        opening_date     = YYYY-04-01
    """

    fy2025_end = getdate("2026-03-31")
    if NEW_SCHEME_START <= from_date <= fy2025_end:
        return NEW_SCHEME_START, FY2025_OPENING_DATE

    if from_date.month >= 4:
        fy_year = from_date.year
    else:
        fy_year = from_date.year - 1

    fy_start         = getdate(f"{fy_year}-04-01")
    fy_accrual_start = add_days(fy_start, 1)   # 02-Apr-YYYY

    return fy_accrual_start, fy_start


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: DATE ARITHMETIC
# ─────────────────────────────────────────────────────────────────────────────

def add_days(date, n):
    """Return date + n calendar days as a date object."""
    from datetime import timedelta
    return date + timedelta(days=n)


# ─────────────────────────────────────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────────────────────────────────────

def get_columns(leave_types):

    columns = [
        {
            "label":     "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options":   "Employee",
            "width":     120,
        },
        {
            "label":     "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width":     150,
        },
        {
            "label":     "Branch",
            "fieldname": "branch",
            "fieldtype": "Data",
            "width":     120,
        },
        {
            "label":     "Designation",
            "fieldname": "designation",
            "fieldtype": "Data",
            "width":     140,
        },
    ]

    for lt in leave_types:
        prefix = get_prefix(lt)
        label  = prefix.upper()

        columns.extend([
            {
                "label":     f"{label} Opening Balance",
                "fieldname": f"{prefix}_opening",
                "fieldtype": "Float",
                "width":     140,
            },
            {
                "label":     f"{label} Accrued Balance",
                "fieldname": f"{prefix}_accrued",
                "fieldtype": "Float",
                "width":     140,
            },
            {
                "label":     f"{label} Availed Till Last Month",
                "fieldname": f"{prefix}_availed_last_month",
                "fieldtype": "Float",
                "width":     170,
            },
            {
                "label":     f"{label} Availed Current Month",
                "fieldname": f"{prefix}_availed_current_month",
                "fieldtype": "Float",
                "width":     170,
            },
            {
                "label":     f"{label} Deduction Current Month",
                "fieldname": f"{prefix}_deduction",
                "fieldtype": "Float",
                "width":     180,
            },
            {
                "label":     f"{label} Total Availed",
                "fieldname": f"{prefix}_total_availed",
                "fieldtype": "Float",
                "width":     140,
            },
            {
                "label":     f"{label} Closing Balance",
                "fieldname": f"{prefix}_closing",
                "fieldtype": "Float",
                "width":     140,
            },
        ])

    return columns


# ─────────────────────────────────────────────────────────────────────────────
# DATE RANGE FROM FILTERS
# ─────────────────────────────────────────────────────────────────────────────

def get_date_range(filters):

    if not filters.get("month"):
        frappe.throw("Please select Month")
    if not filters.get("year"):
        frappe.throw("Please select Year")

    month_map = {
        "January": 1, "February": 2,  "March":     3,
        "April":   4, "May":      5,  "June":      6,
        "July":    7, "August":   8,  "September": 9,
        "October": 10,"November": 11, "December":  12,
    }

    month = month_map.get(filters.month)
    year  = int(filters.year)

    from_date = getdate(f"{year}-{month:02d}-01")

    last_day_of_month  = calendar.monthrange(year, month)[1]
    last_date_of_month = getdate(f"{year}-{month:02d}-{last_day_of_month:02d}")
    to_date            = min(last_date_of_month, getdate(today()))
    # to_date = min(last_date_of_month, getdate("2026-09-01"))

    return from_date, to_date


# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEES
# ─────────────────────────────────────────────────────────────────────────────

def get_employees(filters):

    conditions = " WHERE status = 'Active' "

    if filters.branch:
        conditions += " AND branch = %(branch)s"
    if filters.employee:
        conditions += " AND name = %(employee)s"
    if filters.employment_type:
        conditions += " AND employment_type = %(employment_type)s"

    return frappe.db.sql(
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


# ─────────────────────────────────────────────────────────────────────────────
# LEDGER ENTRIES
# ─────────────────────────────────────────────────────────────────────────────

def get_leave_ledger_entries(fetch_from, fetch_to):
    """
    Fetch all submitted Leave Ledger Entries between fetch_from and fetch_to
    (inclusive). fetch_from is opening_date so we capture opening-balance
    entries posted on that date as well.
    """
    return frappe.db.sql(
        """
        SELECT
            employee,
            leave_type,
            transaction_type,
            transaction_name,
            leaves,
            from_date,
            custom_is_penalty
        FROM `tabLeave Ledger Entry`
        WHERE
            docstatus = 1
            AND from_date BETWEEN %s AND %s
        """,
        (fetch_from, fetch_to),
        as_dict=1,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LEAVE TYPES
# ─────────────────────────────────────────────────────────────────────────────

def get_leave_types(filters):
    if filters.get("leave_type"):
        return [filters.leave_type]
    return ["Casual Leave", "Privilege Leave", "Sick Leave"]


# ─────────────────────────────────────────────────────────────────────────────
# PREFIX MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def get_prefix(leave_type):
    return {
        "Casual Leave":    "cl",
        "Privilege Leave": "pl",
        "Sick Leave":      "sl",
    }.get(leave_type, leave_type.lower().replace(" ", "_"))