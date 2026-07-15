# import frappe
# from frappe.utils import getdate, date_diff
# from calendar import isleap
# from datetime import timedelta
# from frappe.utils import getdate, date_diff, cint


# def validate(self, method):

#     if not self.employee:
#         return

#     # =====================================
#     # Employee Details
#     # =====================================
#     employee = frappe.get_doc("Employee", self.employee)

#     # =====================================
#     # Only Confirmed Employee Allowed
#     # =====================================
#     if employee.employment_type != "Confirmed":
#         frappe.throw(
#             "Only Confirmed employees can apply for LTA."
#         )

#     # =====================================
#     # Employee Suspension Status
#     # =====================================
#     if employee.status == "Suspended":
#         frappe.throw(
#             "Suspended employees are not allowed to apply for LTA."
#         )

#     # =====================================
#     # Final Confirmation Date
#     # =====================================
#     if not employee.final_confirmation_date:
#         frappe.throw(
#             "Employee Final Confirmation Date is missing."
#         )

#     confirmation_date = getdate(
#         employee.final_confirmation_date
#     )

#     # =====================================
#     # HR Settings
#     # =====================================
#     lta_limit = (
#         frappe.db.get_single_value(
#             "HR Settings",
#             "custom_lta_per_year"
#         )
#     )

#     total_lta_amount = 0
#     applicable_lta = 0

#     # =====================================
#     # Leave Applications
#     # =====================================
#     leave_applications = frappe.get_all(
#         "Leave Application",
#         filters={
#             "employee": self.employee,
#             "status": "Approved",
#             "docstatus": 1
#         },
#         fields=[
#             "name",
#             "from_date",
#             "to_date",
#             "leave_type"
#         ],
#         order_by="to_date desc"
#     )

#     # =====================================
#     # Loop Expense Rows
#     # =====================================
#     for row in self.expenses:

#         if row.expense_type != "LTA":
#             continue

#         total_lta_amount += (row.amount or 0)

#         if not row.expense_date:
#             frappe.throw(
#                 f"Expense Date is required in row {row.idx}"
#             )

#         expense_date = getdate(row.expense_date)

#         # =====================================
#         # Suspension Period Validation
#         # =====================================
#         if employee.custom_suspended_from_date:

#             suspended_from = getdate(
#                 employee.custom_suspended_from_date
#             )

#             if not employee.custom_suspended_to_date:

#                 if expense_date >= suspended_from:
#                     frappe.throw(
#                         f"Employee is under suspension since "
#                         f"{frappe.format(suspended_from)}. "
#                         f"LTA claim is not allowed until suspension is revoked."
#                     )

#             else:

#                 suspended_to = getdate(
#                     employee.custom_suspended_to_date
#                 )

#                 if suspended_from <= expense_date <= suspended_to:
#                     frappe.throw(
#                         f"Employee was under suspension from "
#                         f"{frappe.format(suspended_from)} to "
#                         f"{frappe.format(suspended_to)}. "
#                         f"LTA claim cannot be applied during this period."
#                     )

        
#         # =====================================
#         # Leave Validation
#         # =====================================
#         valid_leave_found = False
#         continuous_dates = set()
#         qualifying_leave_to = None

#         for leave in leave_applications:

#             if leave.leave_type not in [
#                 "Casual Leave",
#                 "Privilege Leave"
#             ]:
#                 continue

#             leave_from = getdate(leave.from_date)
#             leave_to = getdate(leave.to_date)

#             # =====================================
#             # Leave Must Be In Same Claim Year
#             # =====================================
#             expense_year = expense_date.year

#             if leave_from.year != leave_to.year:
#                 continue

#             if leave_to.year != expense_year:
#                 continue

#             # =====================================
#             # LTA Cannot Be Claimed Before Leave Completion
#             # =====================================
#             if expense_date < leave_to:
#                 continue

#             # =====================================
#             # Ignore Leave Before Confirmation
#             # =====================================
#             if leave_to < confirmation_date:
#                 continue

#             if leave_from < confirmation_date:
#                 leave_from = confirmation_date

#             total_days = (
#                 date_diff(leave_to, leave_from) + 1
#             )

#             # =====================================
#             # Minimum 4 Days Leave Required
#             # =====================================
#             if total_days < 4:
#                 continue

#             # =====================================
#             # Claim Within 30 Days After Leave End
#             # =====================================
#             # days_after_leave = date_diff(
#             #     expense_date,
#             #     leave_to
#             # )

#             # if days_after_leave < 0:
#             #     continue

#             # if days_after_leave > 30:
#             #     continue

#             valid_leave_found = True
#             qualifying_leave_to = leave_to

#             current_date = leave_from

#             while current_date <= leave_to:
#                 continuous_dates.add(current_date)
#                 current_date += timedelta(days=1)

#             break
#         # for leave in leave_applications:

#         #     if leave.leave_type not in [
#         #         "Casual Leave",
#         #         "Privilege Leave"
#         #     ]:
#         #         continue

#         #     leave_from = getdate(leave.from_date)
#         #     leave_to = getdate(leave.to_date)

#         #     # =====================================
#         #     # LTA Cannot Be Claimed Before Leave Completion
#         #     # =====================================
#         #     if expense_date < leave_to:
#         #         continue

#         #     # Ignore leaves before confirmation
#         #     if leave_to < confirmation_date:
#         #         continue

#         #     if leave_from < confirmation_date:
#         #         leave_from = confirmation_date

#         #     total_days = (
#         #         date_diff(leave_to, leave_from) + 1
#         #     )

#         #     if total_days < 4:
#         #         continue

#         #     # =====================================
#         #     # Claim Within 30 Days
#         #     # =====================================
#         #     days_after_leave = date_diff(
#         #         expense_date,
#         #         leave_to
#         #     )

#         #     if days_after_leave < 0:
#         #         continue

#         #     if days_after_leave > 30:
#         #         continue

#         #     valid_leave_found = True
#         #     qualifying_leave_to = leave_to

#         #     current_date = leave_from

#         #     while current_date <= leave_to:
#         #         continuous_dates.add(current_date)
#         #         current_date += timedelta(days=1)

#         #     break

#         if not valid_leave_found:
#             frappe.throw(
#                 "Employee must complete minimum 4 continuous days CL/PL leave and apply for LTA only after leave completion and within 30 days from leave end date."
#             )
#         # =====================================
#         # LTA Entitlement Year
#         # =====================================
#         claim_year = qualifying_leave_to.year

#         # =====================================
#         # Add Weekoff + HolidaysWhat is the value of lta_limit?
#         # =====================================
#         if continuous_dates:

#             min_date = min(continuous_dates)
#             max_date = max(continuous_dates)

#             holiday_dates = set()

#             if employee.holiday_list:

#                 holidays = frappe.get_all(
#                     "Holiday",
#                     filters={
#                         "parent": employee.holiday_list
#                     },
#                     fields=["holiday_date"]
#                 )

#                 holiday_dates = {
#                     getdate(h.holiday_date)
#                     for h in holidays
#                 }

#             current_date = min_date

#             while current_date <= max_date:

#                 # Saturday / Sunday
#                 if current_date.weekday() in [5, 6]:
#                     continuous_dates.add(current_date)

#                 if current_date in holiday_dates:
#                     continuous_dates.add(current_date)

#                 current_date += timedelta(days=1)

#         sorted_dates = sorted(continuous_dates)

#         max_streak = 1
#         streak = 1

#         for i in range(1, len(sorted_dates)):

#             if (
#                 sorted_dates[i]
#                 - sorted_dates[i - 1]
#             ).days == 1:

#                 streak += 1
#                 max_streak = max(
#                     max_streak,
#                     streak
#                 )

#             else:
#                 streak = 1

#         if max_streak < 4:
#             frappe.throw(
#                 "Minimum 4 continuous days (Leave + Holiday + Weekoff) required for LTA."
#             )

#         # =====================================
#         # LTA Claim Count Validation
#         # =====================================

#         existing_claim_count = 0

#         existing_lta_claims = frappe.db.sql("""
#             SELECT
#                 ec.name,
#                 ecd.expense_date
#             FROM `tabExpense Claim` ec
#             INNER JOIN `tabExpense Claim Detail` ecd
#                 ON ecd.parent = ec.name
#             WHERE ec.employee = %s
#             AND ecd.expense_type = 'LTA'
#             AND ec.docstatus != 2
#             AND ec.name != %s
#         """, (
#             self.employee,
#             self.name
#         ), as_dict=True)

#         for claim in existing_lta_claims:

#             existing_expense_date = getdate(claim.expense_date)

#             existing_claim_year = existing_expense_date.year

#             matching_leave = frappe.db.sql("""
#                 SELECT to_date
#                 FROM `tabLeave Application`
#                 WHERE employee = %s
#                 AND status = 'Approved'
#                 AND docstatus = 1
#                 AND to_date <= %s
#                 ORDER BY to_date DESC
#                 LIMIT 1
#             """, (
#                 self.employee,
#                 existing_expense_date
#             ), as_dict=True)

#             if matching_leave:
#                 existing_claim_year = getdate(
#                     matching_leave[0].to_date
#                 ).year

#             if existing_claim_year == claim_year:
#                 existing_claim_count += 1

#         if existing_claim_count >= cint(lta_limit):
#             frappe.msgprint(
#                 f"""
#                 Claim Year : {claim_year}
#                 Existing Count : {existing_claim_count}
#                 """
#             )

#             frappe.throw(
#                 f"Only {lta_limit} LTA claim(s) are allowed for year {claim_year}."
#             )

#         # =====================================
#         # Salary Structure Assignment
#         # Based on Qualifying Leave End Date
#         # =====================================
#         salary = frappe.db.sql("""
#             SELECT base
#             FROM `tabSalary Structure Assignment`
#             WHERE employee = %s
#             AND docstatus = 1
#             AND from_date <= %s
#             ORDER BY from_date DESC
#             LIMIT 1
#         """, (
#             self.employee,
#             qualifying_leave_to
#         ), as_dict=True)
#         if not salary:
#             frappe.throw(
#                 "Salary Structure Assignment not found for qualifying leave date."
#             )

#         monthly_basic = salary[0].base or 0

#         if monthly_basic <= 0:
#             frappe.throw(
#                 "Monthly Basic Salary must be greater than 0."
#             )

#         # =====================================
#         # LTA Calculation
#         # =====================================
#         total_days_in_year = (
#             366 if isleap(claim_year) else 365
#         )

#         start_of_year = getdate(
#             f"{claim_year}-01-01"
#         )

#         end_of_year = getdate(
#             f"{claim_year}-12-31"
#         )

#         confirmed_start = max(
#             confirmation_date,
#             start_of_year
#         )

#         confirmed_days = (
#             date_diff(
#                 end_of_year,
#                 confirmed_start
#             ) + 1
#         )

#         if confirmed_days < 0:
#             confirmed_days = 0

#         applicable_lta = round(
#             monthly_basic *
#             (
#                 confirmed_days /
#                 total_days_in_year
#             )
#         )

#     # =====================================
#     # Final Amount Validation
#     # =====================================
#     if total_lta_amount > applicable_lta:

#         frappe.throw(
#             f"""
#             <b>LTA Policy Validation</b><br><br>

#             Maximum allowed LTA amount as per company policy:
#             <b>₹{applicable_lta}</b><br><br>

#             Your current LTA claim amount:
#             <b>₹{total_lta_amount}</b><br><br>

#             """
#         )


import frappe
from frappe.utils import getdate, date_diff, cint
from calendar import isleap
from datetime import timedelta


# =====================================================
# Helper: Fiscal Year Bounds (Apr 1 - Mar 31)
# =====================================================
def get_fiscal_year_bounds(reference_date=None):
    reference_date = getdate(reference_date or getdate())
    if reference_date.month >= 4:
        start_year = reference_date.year
    else:
        start_year = reference_date.year - 1
    start = getdate(f"{start_year}-04-01")
    end = getdate(f"{start_year + 1}-03-31")
    return start, end


# =====================================================
# Whitelisted: Called from JS on Employee change
# =====================================================
@frappe.whitelist()
def get_fiscal_periods(employee, expense_claim=None):
    today = getdate()

    current_start, current_end = get_fiscal_year_bounds(today)
    prev_start, prev_end = get_fiscal_year_bounds(current_start - timedelta(days=1))

    result = {
        "lta_period_from": current_start,
        "lta_period_to": current_end,
        "last_availed_from": None,
        "last_availed_to": None,
    }

    filters_sql = """
        employee = %s
        AND docstatus != 2
        AND custom_period_of_leave_to IS NOT NULL
        AND custom_period_of_leave_to BETWEEN %s AND %s
    """
    values = [employee, prev_start, prev_end]

    if expense_claim:
        filters_sql += " AND name != %s"
        values.append(expense_claim)

    previous_claim = frappe.db.sql(f"""
        SELECT name FROM `tabExpense Claim`
        WHERE {filters_sql}
        LIMIT 1
    """, tuple(values), as_dict=True)

    if previous_claim:
        result["last_availed_from"] = prev_start
        result["last_availed_to"] = prev_end

    return result


# =====================================================
# Shared: CL / PL / PH / WO breakdown for a period
# =====================================================
def compute_lta_day_breakdown(employee_doc, period_from, period_to):
    period_from = getdate(period_from)
    period_to = getdate(period_to)

    leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee_doc.name,
            "status": "Approved",
            "docstatus": 1,
            "leave_type": ["in", ["Casual Leave", "Privilege Leave"]]
        },
        fields=["name", "from_date", "to_date", "leave_type"]
    )

    leave_day_type = {}
    for leave in leave_applications:
        leave_from = getdate(leave.from_date)
        leave_to = getdate(leave.to_date)
        d = max(leave_from, period_from)
        end = min(leave_to, period_to)
        while d <= end:
            leave_day_type.setdefault(d, leave.leave_type)
            d += timedelta(days=1)

    holiday_dates = set()
    if employee_doc.holiday_list:
        holidays = frappe.get_all(
            "Holiday",
            filters={"parent": employee_doc.holiday_list},
            fields=["holiday_date"]
        )
        holiday_dates = {getdate(h.holiday_date) for h in holidays}

    day_type = {}
    d = period_from
    while d <= period_to:
        if d in leave_day_type:
            day_type[d] = "CL" if leave_day_type[d] == "Casual Leave" else "PL"
        elif d in holiday_dates:
            day_type[d] = "PH"
        elif d.weekday() in [5, 6]:
            day_type[d] = "WO"
        d += timedelta(days=1)

    covered_dates = sorted(day_type.keys())

    max_streak = 0
    current_streak = 0
    streak_start = None
    best_start = None
    best_end = None
    prev_date = None

    for dt in covered_dates:
        if prev_date is not None and (dt - prev_date).days == 1:
            current_streak += 1
        else:
            streak_start = dt
            current_streak = 1

        if current_streak > max_streak:
            max_streak = current_streak
            best_start = streak_start
            best_end = dt

        prev_date = dt

    cl_count = pl_count = ph_count = wo_count = 0

    if best_start and best_end:
        d = best_start
        while d <= best_end:
            t = day_type[d]
            if t == "CL":
                cl_count += 1
            elif t == "PL":
                pl_count += 1
            elif t == "PH":
                ph_count += 1
            elif t == "WO":
                wo_count += 1
            d += timedelta(days=1)

    total_days = cl_count + pl_count + ph_count + wo_count

    return {
        "cl_count": cl_count,
        "pl_count": pl_count,
        "ph_count": ph_count,
        "wo_count": wo_count,
        "total_days": total_days,
    }


# =====================================================
# Whitelisted: Called from JS on Period Of Leave change
# =====================================================
@frappe.whitelist()
def get_lta_leave_details(employee, period_from, period_to):
    employee_doc = frappe.get_doc("Employee", employee)
    breakdown = compute_lta_day_breakdown(employee_doc, period_from, period_to)

    breakdown["sanctioned_days"] = frappe.db.get_single_value(
        "HR Settings", "custom_lta_sanctioned_days"
    )
    return breakdown


# =====================================================
# validate() — server-side safety net (client can't be trusted)
# =====================================================
def validate(self, method):

    if not self.employee:
        return

    employee = frappe.get_doc("Employee", self.employee)

    if employee.employment_type != "Confirmed":
        frappe.throw("Only Confirmed employees can apply for LTA.")

    if employee.status == "Suspended":
        frappe.throw("Suspended employees are not allowed to apply for LTA.")

    if not employee.final_confirmation_date:
        frappe.throw("Employee Final Confirmation Date is missing.")

    confirmation_date = getdate(employee.final_confirmation_date)

    # ---- Fiscal periods (recomputed server-side, JS only does it for UX) ----
    fiscal_periods = get_fiscal_periods(self.employee, expense_claim=self.name)
    self.custom_lta_period_from = fiscal_periods["lta_period_from"]
    self.custom_lta_period_to = fiscal_periods["lta_period_to"]
    self.custom_period_of_last_lta_availed_from = fiscal_periods["last_availed_from"]
    self.custom_period_of_last_lta_availed_to = fiscal_periods["last_availed_to"]

    lta_limit = frappe.db.get_single_value("HR Settings", "custom_lta_per_year")
    self.custom_availed_or_sanctioned_no_of_days = frappe.db.get_single_value(
        "HR Settings", "custom_lta_sanctioned_days"
    )

    if not self.custom_period_of_leave_from or not self.custom_period_of_leave_to:
        frappe.throw("Period Of Leave (From and To) is required for LTA claim.")

    period_from = getdate(self.custom_period_of_leave_from)
    period_to = getdate(self.custom_period_of_leave_to)

    if period_from > period_to:
        frappe.throw("Period Of Leave From date cannot be after the To date.")

    if period_from < confirmation_date:
        frappe.throw(
            "Period Of Leave cannot start before the employee's Final Confirmation Date."
        )

    # ---- Suspension overlap ----
    if employee.custom_suspended_from_date:
        suspended_from = getdate(employee.custom_suspended_from_date)

        if not employee.custom_suspended_to_date:
            overlaps = period_to >= suspended_from
            suspended_to_msg = ""
        else:
            suspended_to = getdate(employee.custom_suspended_to_date)
            overlaps = period_from <= suspended_to and period_to >= suspended_from
            suspended_to_msg = f" to {frappe.format(suspended_to)}"

        if overlaps:
            frappe.throw(
                f"Employee was under suspension from "
                f"{frappe.format(suspended_from)}{suspended_to_msg}. "
                f"The Period Of Leave ({frappe.format(period_from)} to {frappe.format(period_to)}) "
                f"overlaps with the suspension period. LTA claim cannot be applied."
            )

    # ---- CL/PL/PH/WO breakdown (same helper used by JS) ----
    breakdown = compute_lta_day_breakdown(employee, period_from, period_to)

    self.custom_cl = breakdown["cl_count"]
    self.custom_pl = breakdown["pl_count"]
    self.custom_ph = breakdown["ph_count"]
    self.custom_wo = breakdown["wo_count"]
    self.custom_total = breakdown["total_days"]

    total_days = breakdown["total_days"]
    claim_year = period_to.year

    if int(total_days) < int(self.custom_availed_or_sanctioned_no_of_days):
        frappe.throw(
            f"Minimum {self.custom_availed_or_sanctioned_no_of_days} continuous days "
            f"(Leave + Holiday + Weekoff) are required for LTA."
        )

    # ---- Salary Structure Assignment ----
    salary = frappe.db.sql("""
        SELECT base FROM `tabSalary Structure Assignment`
        WHERE employee = %s AND docstatus = 1 AND from_date <= %s
        ORDER BY from_date DESC LIMIT 1
    """, (self.employee, period_to), as_dict=True)

    if not salary:
        frappe.throw("Salary Structure Assignment not found for the Period Of Leave end date.")

    monthly_basic = salary[0].base or 0

    if monthly_basic <= 0:
        frappe.throw("Monthly Basic Salary must be greater than 0.")

    # ---- LTA Claim Count Validation ----
    existing_claim_count = 0

    existing_lta_claims = frappe.db.sql("""
        SELECT ec.name, ec.custom_period_of_leave_to
        FROM `tabExpense Claim` ec
        WHERE ec.employee = %s AND ec.docstatus != 2
        AND ec.name != %s AND ec.custom_period_of_leave_to IS NOT NULL
    """, (self.employee, self.name), as_dict=True)

    for claim in existing_lta_claims:
        if getdate(claim.custom_period_of_leave_to).year == claim_year:
            existing_claim_count += 1

    if existing_claim_count >= cint(lta_limit):
        frappe.msgprint(f"Claim Year : {claim_year}\nExisting Count : {existing_claim_count}")
        frappe.throw(f"Only {lta_limit} LTA claim(s) are allowed for year {claim_year}.")

    # ---- LTA Entitlement Calculation ----
    total_days_in_year = 366 if isleap(claim_year) else 365
    start_of_year = getdate(f"{claim_year}-01-01")
    end_of_year = getdate(f"{claim_year}-12-31")
    confirmed_start = max(confirmation_date, start_of_year)
    confirmed_days = max(date_diff(end_of_year, confirmed_start) + 1, 0)

    applicable_lta = round(monthly_basic * (confirmed_days / total_days_in_year))

    # ---- Loop Expense Rows ----
    total_lta_amount = 0

    for row in self.expenses:
        if row.expense_type != "LTA":
            continue

        total_lta_amount += (row.amount or 0)

        if not row.expense_date:
            frappe.throw(f"Expense Date is required in row {row.idx}")

        expense_date = getdate(row.expense_date)

        if employee.custom_suspended_from_date:
            suspended_from = getdate(employee.custom_suspended_from_date)

            if not employee.custom_suspended_to_date:
                if expense_date >= suspended_from:
                    frappe.throw(
                        f"Employee is under suspension since {frappe.format(suspended_from)}. "
                        f"LTA claim is not allowed until suspension is revoked."
                    )
            else:
                suspended_to = getdate(employee.custom_suspended_to_date)
                if suspended_from <= expense_date <= suspended_to:
                    frappe.throw(
                        f"Employee was under suspension from {frappe.format(suspended_from)} "
                        f"to {frappe.format(suspended_to)}. LTA claim cannot be applied during this period."
                    )

    if total_lta_amount > applicable_lta:
        frappe.throw(f"""
            <b>LTA Policy Validation</b><br><br>
            Maximum allowed LTA amount as per company policy: <b>₹{applicable_lta}</b><br><br>
            Your current LTA claim amount: <b>₹{total_lta_amount}</b><br><br>
        """)