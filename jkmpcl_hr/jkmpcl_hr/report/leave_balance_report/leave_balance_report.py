# ---------------------------------------- Leave Required Report Updated Code (08-05-2026) ----------------------------------------

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

    # from_date        → 1st of the filtered month
    # to_date          → min(last day of month, today)
    #                    ONLY used for: accrued and deduction cutoff
    # to_date_full_mth → always the last calendar day of the filtered month
    #                    used for: fetching leave applications AND
    #                    computing availed current month / availed till last month
    #                    so approved future-dated leaves in the same month are counted
    from_date, to_date, to_date_full_mth = get_date_range(filters)

    employees   = get_employees(filters)
    leave_types = get_leave_types(filters)

    # ── Determine which Financial Year window we are in ───────────────────────
    fy_accrual_start, opening_date = get_fy_boundaries(from_date)

    is_fy2025 = (opening_date == FY2025_OPENING_DATE)

    # ── Fetch ALL relevant ledger entries (allocations + penalties only) ──────
    # to_date used here so future accruals not yet posted are excluded
    ledger_entries = get_leave_ledger_entries(opening_date, to_date)

    # ── Fetch Leave Applications using full month-end date ────────────────────
    # to_date_full_mth ensures leaves approved for later in the month
    # (e.g. leave starting 29-Jun when today is 26-Jun) are not missed
    leave_applications = get_leave_applications(opening_date, to_date_full_mth)

    # ── Pre-fetch custom_opening_balance for SL allocations on opening_date ──
    sl_opening_balance_map = {}
    if not is_fy2025:
        sl_opening_balance_map = get_sl_custom_opening_balances(
            ledger_entries, opening_date
        )

    # ── Holiday / Weekly-off exclusion setup ───────────────────────────────────
    # NOTE: We no longer look at the Leave Type's "include_holiday" checkbox to
    # decide whether a holiday-list date should be excluded from availed count.
    # That was a static, per-leave-type setting and couldn't tell the difference
    # between "this holiday was never taken as leave" vs "this holiday was
    # actually approved as leave" (e.g. the 2nd Restricted Holiday pair date).
    # Instead we now check the Attendance record for that exact date: if it's
    # marked "On Leave" (linked to a Leave Application of this leave type), the
    # date is counted as availed regardless of it being a holiday-list date.
    emp_holiday_list_map = get_employee_holiday_lists(employees, to_date_full_mth)
    holiday_dates_map = get_holiday_dates_map(
        set(emp_holiday_list_map.values()), opening_date, to_date_full_mth
    )
    on_leave_attendance_map = get_on_leave_attendance_dates(
        employees, leave_types, opening_date, to_date_full_mth
    )

    # ── Previous-month boundaries ─────────────────────────────────────────────
    # availed_prev_end  : last day of previous month  (None for first FY month)
    # prev_month_start  : first day of previous month (None for first FY month)
    is_first_month_of_fy = (
        from_date == fy_accrual_start
        or (
            not is_fy2025
            and from_date == opening_date
        )
    )

    if is_first_month_of_fy:
        availed_prev_end = None
        prev_month_start = None
    else:
        availed_prev_end = add_days(from_date, -1)           # last day of prev month
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

        emp_holiday_dates = holiday_dates_map.get(
            emp_holiday_list_map.get(emp.name), set()
        )

        for lt in leave_types:

            prefix = get_prefix(lt)

            opening               = 0.0
            accrued               = 0.0
            availed_till_last_mth = 0.0
            availed_current_mth   = 0.0
            deduction_current_mth = 0.0

            # Holiday-list dates are excluded from availed count by default;
            # the exception is any date where Attendance actually shows
            # "On Leave" for this employee + leave type (e.g. a leave taken
            # on the 2nd Restricted Holiday pair date).
            exclude_holidays_for_lt = emp_holiday_dates
            on_leave_dates_for_lt   = on_leave_attendance_map.get(
                (emp.name, lt), set()
            )

            # ──────────────────────────────────────────────────────────────────
            # PASS 1 — Ledger entries
            # Handles: Opening Balance, Accrued, Deduction (penalty)
            # Does NOT handle availed — that is done in PASS 2 using
            # Leave Application doctype directly so cross-month pro-rating
            # works correctly for ALL leave types.
            # ──────────────────────────────────────────────────────────────────

            for entry in ledger_entries:

                if entry.employee   != emp.name: continue
                if entry.leave_type != lt:       continue

                leaves     = flt(entry.leaves)
                e_date     = getdate(entry.from_date)
                txn_type   = entry.transaction_type
                is_penalty = entry.custom_is_penalty

                # ── 1. OPENING BALANCE ────────────────────────────────────────
                if (
                    e_date == opening_date
                    and txn_type == "Leave Allocation"
                    and not is_penalty
                ):
                    if is_fy2025:
                        opening += leaves
                    else:
                        if lt == "Casual Leave":
                            # CL lapses at year-end → opening allocation → Accrued
                            accrued += leaves
                        elif lt == "Sick Leave":
                            key       = (emp.name, lt)
                            custom_ob = sl_opening_balance_map.get(key, 0.0)
                            opening  += custom_ob
                            new_grant = leaves - custom_ob
                            if new_grant > 0:
                                accrued += new_grant
                        elif lt == "Privilege Leave":
                            opening += leaves

                # ── 2. ACCRUED ────────────────────────────────────────────────
                # Gated by to_date (today-clipped) — only post-opening
                # allocation entries up to today count as accrued
                elif (
                    fy_accrual_start <= e_date <= to_date
                    and txn_type == "Leave Allocation"
                    and not is_penalty
                ):
                    accrued += leaves

                # ── 3. DEDUCTION CURRENT MONTH (penalty) ─────────────────────
                # Gated by to_date (today-clipped) — only penalties up to
                # today count in the current month
                elif (
                    from_date <= e_date <= to_date
                    and txn_type == "Leave Allocation"
                    and is_penalty
                ):
                    deduction_current_mth += abs(leaves)

                elif (
                    prev_month_start is not None
                    and availed_prev_end is not None
                    and opening_date <= e_date <= availed_prev_end
                    and txn_type == "Leave Allocation"
                    and is_penalty
                ):
                    availed_till_last_mth += abs(leaves)

            # ──────────────────────────────────────────────────────────────────
            # PASS 2 — Leave Applications (availed figures, ALL leave types)
            #
            # Key design decisions:
            #
            # 1. We use to_date_full_mth (last day of month) as the window end
            #    for BOTH availed_till_last_month and availed_current_month.
            #    This is critical: a leave starting 29-Jun (approved on 24-Jun)
            #    must appear in June's availed even when today is 26-Jun.
            #    Without this, the leave is fetched by SQL but then clipped
            #    to 0 days because max(29-Jun, 01-Jun)=29-Jun > min(02-Jul, 26-Jun)=26-Jun.
            #
            # 2. availed_till_last_month uses the full last-day of the
            #    previous month as its window end (availed_prev_end), which is
            #    already a complete calendar date, so no change needed there.
            #
            # 3. get_leave_days_in_period clips to the overlap of the leave
            #    period and the window, so cross-month leaves are correctly
            #    split — e.g. leave 29-Jun to 02-Jul in June window gives 2 days.
            #
            # 4. Holiday-list dates are excluded UNLESS Attendance shows the
            #    date was actually taken "On Leave" (on_leave_dates_for_lt) —
            #    see comment above where exclude_holidays_for_lt is set.
            # ──────────────────────────────────────────────────────────────────

            for leave in leave_applications:

                if leave.employee   != emp.name: continue
                if leave.leave_type != lt:       continue

                leave_from = getdate(leave.from_date)
                leave_to   = getdate(leave.to_date)

                # Availed Till Last Month
                # Window: opening_date → availed_prev_end (full month boundary)
                if availed_prev_end is not None:
                    availed_till_last_mth += get_leave_days_in_period(
                        leave_from, leave_to,
                        opening_date, availed_prev_end,
                        half_day=leave.half_day,
                        holiday_dates=exclude_holidays_for_lt,
                        on_leave_dates=on_leave_dates_for_lt,
                    )

                # Availed Current Month
                # Window: from_date → to_date_full_mth (last day of report month)
                # Using to_date_full_mth instead of to_date (today) ensures
                # approved leaves for later in the current month are counted.
                availed_current_mth += get_leave_days_in_period(
                    leave_from, leave_to,
                    from_date, to_date_full_mth,        # ← KEY FIX
                    half_day=leave.half_day,
                    holiday_dates=exclude_holidays_for_lt,
                    on_leave_dates=on_leave_dates_for_lt,
                )

            # ── Derived columns ───────────────────────────────────────────────
            total_availed = (
                availed_till_last_mth
                + availed_current_mth
                + deduction_current_mth
            )
            closing = opening + accrued - total_availed

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


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: LEAVE DAYS IN PERIOD (cross-month pro-rating)
# ─────────────────────────────────────────────────────────────────────────────

def get_leave_days_in_period(leave_from, leave_to, report_from, report_to,
                              half_day=False, holiday_dates=None, on_leave_dates=None):
    """
    Return the number of leave days of a leave application that fall
    within [report_from, report_to], EXCLUDING any date present in
    holiday_dates (weekly offs / holidays / restricted holidays) UNLESS
    that specific date is present in on_leave_dates — meaning Attendance
    actually recorded the employee as "On Leave" (linked to a Leave
    Application of this leave type) on that date, e.g. a leave taken on
    the 2nd Restricted Holiday pair date.
    """
    start = max(leave_from, report_from)
    end   = min(leave_to,   report_to)

    if start > end:
        return 0.0

    holiday_dates  = holiday_dates or set()
    on_leave_dates = on_leave_dates or set()

    if half_day:
        # Single-day half-day leave: only exclude if it's a holiday-list
        # date AND Attendance doesn't confirm it was actually taken as leave.
        if start in holiday_dates and start not in on_leave_dates:
            return 0.0
        return 0.5

    if not holiday_dates:
        return float((end - start).days + 1)

    days = 0
    d = start
    while d <= end:
        if d not in holiday_dates or d in on_leave_dates:
            days += 1
        d += timedelta(days=1)

    return float(days)


def get_leave_type_holiday_inclusion(leave_types):
    """dict: leave_type -> bool(include_holiday)

    NOTE: No longer used to decide holiday exclusion in the report — kept
    here in case it's still useful elsewhere. See on_leave_attendance_map /
    get_on_leave_attendance_dates for the current (Attendance-driven) logic.
    """
    result = {}
    for lt in leave_types:
        include_holiday = frappe.db.get_value("Leave Type", lt, "include_holiday")
        result[lt] = bool(include_holiday)
    return result


def get_on_leave_attendance_dates(employees, leave_types, fetch_from, fetch_to):
    """
    dict: (employee, leave_type) -> set(date) for every date on which
    Attendance is submitted with status "On Leave" (or "Half Day", which
    also gets linked to a Leave Application/Leave Type), for that employee
    and leave type, within [fetch_from, fetch_to].

    This is the authoritative source for "was this specific date actually
    consumed as leave" — including holiday-list dates such as the 2nd
    Restricted Holiday pair date, where Attendance is correctly updated to
    "On Leave" (see get_day_type / custom_create_or_update_attendance).
    """
    if not employees or not leave_types:
        return {}

    emp_names = [e.name for e in employees]

    rows = frappe.db.sql(
        """
        SELECT employee, leave_type, attendance_date
        FROM `tabAttendance`
        WHERE docstatus = 1
          AND status IN ('On Leave', 'Half Day')
          AND leave_application IS NOT NULL
          AND leave_application != ''
          AND employee IN %(employees)s
          AND leave_type IN %(leave_types)s
          AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
        """,
        {
            "employees": emp_names,
            "leave_types": leave_types,
            "from_date": fetch_from,
            "to_date": fetch_to,
        },
        as_dict=True,
    )

    result = {}
    for r in rows:
        key = (r.employee, r.leave_type)
        result.setdefault(key, set()).add(getdate(r.attendance_date))

    return result


def get_employee_holiday_lists(employees, reference_date):
    """
    dict: employee -> holiday_list to use, resolved as:
      1. Latest Holiday List Assignment (applicable_for='Employee') with
         from_date <= reference_date
      2. Employee.holiday_list
      3. Company.default_holiday_list
    """
    if not employees:
        return {}

    emp_names = [e.name for e in employees]

    assignment_rows = frappe.db.sql(
        """
        SELECT assigned_to AS employee, holiday_list
        FROM `tabHoliday List Assignment`
        WHERE applicable_for = 'Employee'
          AND assigned_to IN %(names)s
          AND from_date <= %(ref_date)s
        ORDER BY assigned_to, from_date DESC
        """,
        {"names": emp_names, "ref_date": reference_date},
        as_dict=True,
    )

    assignment_map = {}
    for r in assignment_rows:
        if r.employee not in assignment_map:
            assignment_map[r.employee] = r.holiday_list

    emp_rows = frappe.db.sql(
        """
        SELECT name, holiday_list, company
        FROM `tabEmployee`
        WHERE name IN %(names)s
        """,
        {"names": emp_names},
        as_dict=True,
    )
    emp_field_map   = {r.name: r.holiday_list for r in emp_rows}
    emp_company_map = {r.name: r.company for r in emp_rows}

    companies = {c for c in emp_company_map.values() if c}
    company_default_map = {}
    if companies:
        co_rows = frappe.db.sql(
            """SELECT name, default_holiday_list FROM `tabCompany` WHERE name IN %(names)s""",
            {"names": list(companies)}, as_dict=True,
        )
        company_default_map = {c.name: c.default_holiday_list for c in co_rows}

    result = {}
    for emp in emp_names:
        holiday_list = (
            assignment_map.get(emp)
            or emp_field_map.get(emp)
            or company_default_map.get(emp_company_map.get(emp))
        )
        result[emp] = holiday_list

    return result


def get_holiday_dates_map(holiday_lists, fetch_from, fetch_to):
    """dict: holiday_list -> set(date) of every Holiday between fetch_from/fetch_to"""
    holiday_lists = {h for h in holiday_lists if h}
    if not holiday_lists:
        return {}

    rows = frappe.db.sql(
        """
        SELECT parent AS holiday_list, holiday_date
        FROM `tabHoliday`
        WHERE parent IN %(lists)s
          AND holiday_date BETWEEN %(from_date)s AND %(to_date)s
        """,
        {"lists": list(holiday_lists), "from_date": fetch_from, "to_date": fetch_to},
        as_dict=True,
    )

    result = {}
    for r in rows:
        result.setdefault(r.holiday_list, set()).add(getdate(r.holiday_date))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: FETCH LEAVE APPLICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_leave_applications(fetch_from, fetch_to):
    """
    Fetch all Final Approved Leave Applications whose leave period overlaps
    [fetch_from, fetch_to].

    fetch_from = opening_date of the FY (e.g. 01-Apr-2026)
    fetch_to   = to_date_full_mth = last calendar day of the report month
                 (NOT today — using today would exclude leaves starting
                 after today but still within the report month)
    """
    return frappe.db.sql(
        """
        SELECT
            employee,
            leave_type,
            from_date,
            to_date,
            total_leave_days,
            half_day
        FROM `tabLeave Application`
        WHERE
            docstatus = 1
            AND status = 'Approved'
            AND to_date   >= %s
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
    Fetch the linked Leave Allocation doc and read custom_opening_balance.

    Returns dict: (employee, leave_type) → custom_opening_balance
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

    FY 2025  (Dec-2025 → Mar-2026)
        fy_accrual_start = 2025-12-01
        opening_date     = 2025-11-30

    FY 2026+ (Apr-YYYY → Mar-YYYY+1)
        fy_accrual_start = YYYY-04-02  (day after opening to avoid double-count)
        opening_date     = YYYY-04-01
    """
    fy2025_end = getdate("2026-03-31")
    if NEW_SCHEME_START <= from_date <= fy2025_end:
        return NEW_SCHEME_START, FY2025_OPENING_DATE

    fy_year          = from_date.year if from_date.month >= 4 else from_date.year - 1
    fy_start         = getdate(f"{fy_year}-04-01")
    fy_accrual_start = add_days(fy_start, 1)   # 02-Apr-YYYY

    return fy_accrual_start, fy_start


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: DATE ARITHMETIC
# ─────────────────────────────────────────────────────────────────────────────

def add_days(date, n):
    """Return date + n calendar days as a date object."""
    return date + timedelta(days=n)


# ─────────────────────────────────────────────────────────────────────────────
# COLUMNS
# ─────────────────────────────────────────────────────────────────────────────

def get_columns(leave_types):

    columns = [
        {"label": "Employee",      "fieldname": "employee",      "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Branch",        "fieldname": "branch",        "fieldtype": "Data", "width": 120},
        {"label": "Designation",   "fieldname": "designation",   "fieldtype": "Data", "width": 140},
    ]

    for lt in leave_types:
        prefix = get_prefix(lt)
        label  = prefix.upper()

        columns.extend([
            {"label": f"{label} Opening Balance",        "fieldname": f"{prefix}_opening",               "fieldtype": "Float", "width": 140},
            {"label": f"{label} Accrued Balance",        "fieldname": f"{prefix}_accrued",               "fieldtype": "Float", "width": 140},
            {"label": f"{label} Availed Till Last Month","fieldname": f"{prefix}_availed_last_month",    "fieldtype": "Float", "width": 170},
            {"label": f"{label} Availed Current Month",  "fieldname": f"{prefix}_availed_current_month", "fieldtype": "Float", "width": 170},
            {"label": f"{label} Deduction Current Month","fieldname": f"{prefix}_deduction",             "fieldtype": "Float", "width": 180},
            {"label": f"{label} Total Availed",          "fieldname": f"{prefix}_total_availed",         "fieldtype": "Float", "width": 140},
            {"label": f"{label} Closing Balance",        "fieldname": f"{prefix}_closing",               "fieldtype": "Float", "width": 140},
        ])

    return columns


# ─────────────────────────────────────────────────────────────────────────────
# DATE RANGE FROM FILTERS
# ─────────────────────────────────────────────────────────────────────────────

def get_date_range(filters):
    """
    Returns (from_date, to_date, to_date_full_mth).

    from_date        : 1st of the filtered month
    to_date          : min(last day of month, today)
                       → used ONLY for accrued/deduction cutoff
    to_date_full_mth : last calendar day of the filtered month (never clipped)
                       → used for Leave Application fetch window AND
                         availed current month calculation window
    """
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

    from_date        = getdate(f"{year}-{month:02d}-01")
    last_day         = calendar.monthrange(year, month)[1]
    to_date_full_mth = getdate(f"{year}-{month:02d}-{last_day:02d}")
    to_date          = min(to_date_full_mth, getdate(today()))

    return from_date, to_date, to_date_full_mth


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
        SELECT name, employee_name, branch, designation, employment_type
        FROM `tabEmployee`
        {conditions}
        """,
        filters,
        as_dict=1,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LEDGER ENTRIES (Allocations + Penalties ONLY — availed handled separately)
# ─────────────────────────────────────────────────────────────────────────────

def get_leave_ledger_entries(fetch_from, fetch_to):
    """
    Fetch Leave Ledger Entries of type 'Leave Allocation' only.
    fetch_to = to_date (today-clipped) so future allocations are excluded.

    Leave Application rows are excluded here — availed figures are computed
    directly from tabLeave Application for accurate cross-month pro-rating.
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
            AND transaction_type = 'Leave Allocation'
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