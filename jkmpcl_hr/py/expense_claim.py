import frappe
from frappe.utils import getdate, date_diff, cint,today,add_days
from calendar import isleap
from datetime import timedelta
from jkmpcl_hr.py.utils import  get_emp_hr_manager, get_ceo_user, get_emp_review_manager


# =====================================================
# Helper: Fiscal Year Bounds (Apr 1 - Mar 31)
# =====================================================
# def get_fiscal_year_bounds(reference_date=None):
#     reference_date = getdate(reference_date or getdate())
#     if reference_date.month >= 4:
#         start_year = reference_date.year
#     else:
#         start_year = reference_date.year - 1
#     start = getdate(f"{start_year}-04-01")
#     end = getdate(f"{start_year + 1}-03-31")
#     return start, end


def get_calendar_year_bounds(date):
    date = getdate(date)
    start = getdate(f"{date.year}-01-01")
    end = getdate(f"{date.year}-12-31")
    return start, end

@frappe.whitelist()
def get_calendar_periods(employee, expense_claim=None):
    today = getdate()

    current_start, current_end = get_calendar_year_bounds(today)

    result = {
        "lta_period_from": current_start,
        "lta_period_to": current_end,
        "last_availed_from": None,
        "last_availed_to": None,
    }

    conditions = """
        employee = %s
        AND docstatus != 2
    """

    values = [employee]

    if expense_claim and not expense_claim.startswith("New"):
        conditions += " AND name != %s"
        values.append(expense_claim)

    previous_claim = frappe.db.sql(
        f"""
        SELECT
            name,
            creation
        FROM `tabExpense Claim`
        WHERE {conditions}
        ORDER BY creation DESC
        LIMIT 1
        """,
        tuple(values),
        as_dict=True,
    )

    if previous_claim:
        calendar_start, calendar_end = get_calendar_year_bounds(
            getdate(previous_claim[0].creation)
        )

        result["last_availed_from"] = calendar_start
        result["last_availed_to"] = calendar_end

    return result


# ------UPDATED CODE ON 24-07-2026 for WO and PH not displayed issue in LTA claim form------

# def compute_lta_day_breakdown(employee_doc, period_from, period_to):
#     period_from = getdate(period_from)
#     period_to = getdate(period_to)

#     holiday_list = frappe.db.get_value(
#         "Holiday List Assignment",
#         {"assigned_to": employee_doc.name},
#         "holiday_list",
#         order_by="from_date desc",
#     )
    
#     if not holiday_list:
#         holiday_list = employee_doc.holiday_list

#     holiday_dates = {}
#     if holiday_list:
#         holidays = frappe.get_all(
#             "Holiday",
#             filters={"parent": holiday_list},
#             fields=["holiday_date", "weekly_off"],
#         )
#         # holiday_dates = {getdate(h.holiday_date) for h in holidays}
#         holiday_dates = {
#             getdate(h.holiday_date): "WO" if h.weekly_off else "PH"
#             for h in holidays
#         }

#     leave_applications = frappe.get_all(
#         "Leave Application",
#         filters={
#             "employee": employee_doc.name,
#             "status": "Approved",
#             "docstatus": 1,
#             "leave_type": ["in", ["Casual Leave", "Privilege Leave"]]
#         },
#         fields=["name", "from_date", "to_date", "leave_type", "half_day", "half_day_date"]
#     )

#     leave_day_type = {}
#     half_day_leaves = {}

#     for leave in leave_applications:
#         leave_from = getdate(leave.from_date)
#         leave_to = getdate(leave.to_date)
#         d = max(leave_from, period_from)
#         end = min(leave_to, period_to)

#         while d <= end:
#             # Mark half-day dates separately — they should NOT be counted as
#             # full CL/PL days, but should still keep continuity intact.
#             if cint(leave.half_day) and leave.half_day_date and getdate(leave.half_day_date) == d:
#                 half_day_leaves[d] = leave.leave_type
#             elif d not in holiday_dates:  # Don't mark holidays/weekly offs as leave
#                 leave_day_type.setdefault(d, leave.leave_type)
#             d += timedelta(days=1)

            

#     # ---- Classify EVERY day in the period ----
#     day_type = {}
#     d = period_from
#     while d <= period_to:
#         if d in leave_day_type:
#             day_type[d] = "CL" if leave_day_type[d] == "Casual Leave" else "PL"
#         elif d in holiday_dates:
#             day_type[d] = holiday_dates[d]
#         # elif d.weekday() in [5, 6]:
#         #     day_type[d] = "WO"
#         elif d in half_day_leaves:
#             # Half day: keeps continuity (bridges the streak) but is NOT
#             # counted in CL/PL/PH/WO totals, and does not count toward
#             # the LTA "total days" requirement.
#             day_type[d] = "HD"
#         else:
#             day_type[d] = "WD"  # ordinary working day
#         d += timedelta(days=1)

#     # ---- Full-period counts (used for display: CL/PL/PH/WO/Total) ----
#     cl_count = pl_count = ph_count = wo_count = wd_count = 0
#     for t in day_type.values():
#         if t == "CL":
#             cl_count += 1
#         elif t == "PL":
#             pl_count += 1
#         elif t == "PH":
#             ph_count += 1
#         elif t == "WO":
#             wo_count += 1
#         elif t == "WD":
#             wd_count += 1
#         # HD -> intentionally not counted anywhere

#     # Add half-day counts
#     for leave_type in half_day_leaves.values():
#         if leave_type == "Casual Leave":
#             cl_count += 0.5
#         elif leave_type == "Privilege Leave":
#             pl_count += 0.5

#     total_days = cl_count + pl_count + ph_count + wo_count  # HD excluded entirely

#     # ---- Longest continuous streak (used only for LTA eligibility check) ----
#     # HD days are treated as "transparent" — they don't break the streak,
#     # but they also don't extend/count it. Only CL/PL/PH/WO days increment
#     # the streak length; consecutive HD days are simply skipped over.
#     covered_dates = sorted(dt for dt, t in day_type.items() if t not in ("WD", "HD"))

#     max_streak = 0
#     current_streak = 0
#     streak_start = None
#     best_start = None
#     best_end = None
#     prev_counted_date = None

#     d = period_from
#     while d <= period_to:
#         t = day_type[d]

#         if t == "HD":
#             # bridge day — do nothing, don't reset, don't count
#             d += timedelta(days=1)
#             continue

#         if t == "WD":
#             # real break in continuity
#             current_streak = 0
#             prev_counted_date = None
#             d += timedelta(days=1)
#             continue

#         # t is CL/PL/PH/WO
#         if prev_counted_date is not None:
#             # check if only HD days sit between prev_counted_date and d
#             gap_days = (d - prev_counted_date).days
#             bridged = all(
#                 day_type.get(prev_counted_date + timedelta(days=i)) == "HD"
#                 for i in range(1, gap_days)
#             ) if gap_days > 1 else (gap_days == 1)

#             if bridged:
#                 current_streak += 1
#             else:
#                 streak_start = d
#                 current_streak = 1
#         else:
#             streak_start = d
#             current_streak = 1

#         if current_streak > max_streak:
#             max_streak = current_streak
#             best_start = streak_start
#             best_end = d

#         prev_counted_date = d
#         d += timedelta(days=1)

#     return {
#         "cl_count": cl_count,
#         "pl_count": pl_count,
#         "ph_count": ph_count,
#         "wo_count": wo_count,
#         "wd_count": wd_count,
#         "total_days": total_days,
#         "max_continuous_streak": max_streak,
#         "streak_start": best_start,
#         "streak_end": best_end,
#     }



def compute_lta_day_breakdown(employee_doc, period_from, period_to):
    period_from = getdate(period_from)
    period_to = getdate(period_to)

    holiday_list = frappe.db.get_value(
        "Holiday List Assignment",
        {"assigned_to": employee_doc.name},
        "holiday_list",
        order_by="from_date desc",
    )

    if not holiday_list:
        holiday_list = employee_doc.holiday_list

    holiday_dates = {}

    if holiday_list:
        holidays = frappe.get_all(
            "Holiday",
            filters={"parent": holiday_list},
            fields=["holiday_date", "weekly_off"],
        )

        holiday_dates = {
            getdate(h.holiday_date): "WO" if h.weekly_off else "PH"
            for h in holidays
        }

    leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee_doc.name,
            "status": "Approved",
            "docstatus": 1,
            "leave_type": ["in", ["Casual Leave", "Privilege Leave"]],
        },
        fields=[
            "name",
            "from_date",
            "to_date",
            "leave_type",
            "half_day",
            "half_day_date",
        ],
    )

    leave_day_type = {}
    half_day_leaves = {}

    for leave in leave_applications:
        leave_from = getdate(leave.from_date)
        leave_to = getdate(leave.to_date)

        d = max(leave_from, period_from)
        end = min(leave_to, period_to)

        while d <= end:

            # Half-day leave
            # It should not be counted as a full CL/PL day,
            # but should keep continuity intact.
            if (
                cint(leave.half_day)
                and leave.half_day_date
                and getdate(leave.half_day_date) == d
            ):
                half_day_leaves[d] = leave.leave_type

            # Do not mark holidays / weekly offs as leave
            elif d not in holiday_dates:
                leave_day_type.setdefault(
                    d,
                    leave.leave_type
                )

            d += timedelta(days=1)

    # ---------------------------------------------------------
    # Classify EVERY day in the period
    # ---------------------------------------------------------

    day_type = {}

    d = period_from

    while d <= period_to:

        if d in leave_day_type:
            day_type[d] = (
                "CL"
                if leave_day_type[d] == "Casual Leave"
                else "PL"
            )

        elif d in holiday_dates:
            day_type[d] = holiday_dates[d]

        elif d in half_day_leaves:
            # Half day keeps continuity but is not counted
            # as a complete LTA day.
            day_type[d] = "HD"

        else:
            day_type[d] = "WD"

        d += timedelta(days=1)

    # ---------------------------------------------------------
    # Full-period counts
    # ---------------------------------------------------------

    cl_count = 0
    pl_count = 0
    ph_count = 0
    wo_count = 0
    wd_count = 0

    for t in day_type.values():

        if t == "CL":
            cl_count += 1

        elif t == "PL":
            pl_count += 1

        elif t == "PH":
            ph_count += 1

        elif t == "WO":
            wo_count += 1

        elif t == "WD":
            wd_count += 1

        # HD intentionally not counted here

    # ---------------------------------------------------------
    # Add half-day counts
    # ---------------------------------------------------------

    for leave_type in half_day_leaves.values():

        if leave_type == "Casual Leave":
            cl_count += 0.5

        elif leave_type == "Privilege Leave":
            pl_count += 0.5

    # HD excluded entirely from total_days
    total_days = (
        cl_count
        + pl_count
        + ph_count
        + wo_count
    )

    # ---------------------------------------------------------
    # Longest continuous streak
    #
    # Rules:
    #
    # 1. WD breaks the streak.
    #
    # 2. HD is transparent:
    #       - does not increase streak
    #       - does not break streak
    #
    # 3. CL / PL / PH / WO increase the streak.
    #
    # 4. IMPORTANT:
    #    A streak MUST NOT cross a calendar year.
    #
    #    Example:
    #
    #       30-Dec-2025 CL
    #       31-Dec-2025 CL
    #       01-Jan-2026 CL
    #       02-Jan-2026 CL
    #
    #    This becomes:
    #
    #       2025 -> 2 days
    #       2026 -> 2 days
    #
    #    NOT one 4-day streak.
    # ---------------------------------------------------------

    max_streak = 0
    current_streak = 0

    streak_start = None
    best_start = None
    best_end = None

    prev_counted_date = None

    d = period_from

    while d <= period_to:

        t = day_type[d]

        # -----------------------------------------------------
        # Half-day:
        # Transparent for continuity.
        # -----------------------------------------------------

        if t == "HD":
            d += timedelta(days=1)
            continue

        # -----------------------------------------------------
        # Working day:
        # Completely breaks continuity.
        # -----------------------------------------------------

        if t == "WD":
            current_streak = 0
            prev_counted_date = None
            streak_start = None

            d += timedelta(days=1)
            continue

        # -----------------------------------------------------
        # At this point t is one of:
        #
        # CL / PL / PH / WO
        # -----------------------------------------------------

        if prev_counted_date is not None:

            # -------------------------------------------------
            # IMPORTANT:
            #
            # Do NOT allow a streak to cross calendar years.
            #
            # Example:
            #
            # prev_counted_date = 31-Dec-2025
            # d                  = 01-Jan-2026
            #
            # This starts a NEW streak.
            # -------------------------------------------------

            if prev_counted_date.year != d.year:

                streak_start = d
                current_streak = 1

            else:

                # Number of calendar days between
                # previous counted day and current day.
                gap_days = (
                    d - prev_counted_date
                ).days

                # Check whether ONLY HD days exist
                # between the two counted dates.
                if gap_days > 1:

                    bridged = all(
                        day_type.get(
                            prev_counted_date
                            + timedelta(days=i)
                        ) == "HD"
                        for i in range(1, gap_days)
                    )

                else:

                    # Directly consecutive date
                    bridged = gap_days == 1

                if bridged:
                    current_streak += 1

                else:
                    streak_start = d
                    current_streak = 1

        else:

            # No previous counted day.
            streak_start = d
            current_streak = 1

        # -----------------------------------------------------
        # Update maximum streak
        # -----------------------------------------------------

        if current_streak > max_streak:

            max_streak = current_streak
            best_start = streak_start
            best_end = d

        prev_counted_date = d

        d += timedelta(days=1)

    # ---------------------------------------------------------
    # Return breakdown
    # ---------------------------------------------------------

    return {
        "cl_count": cl_count,
        "pl_count": pl_count,
        "ph_count": ph_count,
        "wo_count": wo_count,
        "wd_count": wd_count,
        "total_days": total_days,
        "max_continuous_streak": max_streak,
        "streak_start": best_start,
        "streak_end": best_end,
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

def on_submit(self,method):
    self.approval_status = "Approved"
# =====================================================
# validate() — server-side safety net (client can't be trusted)
# =====================================================
def validate(self, method):

    if not self.employee:
        return
    
    self.payable_account = "Payroll Payable - JKMPCL"

    employee = frappe.get_doc("Employee", self.employee)

    if employee.employment_type != "Confirmed" and self.custom_expense_claim_type == "LTA":
        frappe.throw("Only Confirmed employees can apply for LTA.")

    if employee.status == "Suspended":
        frappe.throw("Suspended employees are not allowed to apply for LTA.")

    if not employee.final_confirmation_date and self.custom_expense_claim_type == "LTA":
        frappe.throw("Employee Final Confirmation Date is missing.")

    confirmation_date = getdate(employee.final_confirmation_date)

    # ---- Fiscal periods (recomputed server-side, JS only does it for UX) ----
    # fiscal_periods = get_fiscal_periods(self.employee, expense_claim=self.name)
    calendar_periods = get_calendar_periods(self.employee, expense_claim=self.name)
    self.custom_lta_period_from = calendar_periods["lta_period_from"]
    self.custom_lta_period_to = calendar_periods["lta_period_to"]
    self.custom_period_of_last_lta_availed_from = calendar_periods["last_availed_from"]
    self.custom_period_of_last_lta_availed_to = calendar_periods["last_availed_to"]

    lta_limit = frappe.db.get_single_value("HR Settings", "custom_lta_per_year")
    self.custom_availed_or_sanctioned_no_of_days = frappe.db.get_single_value(
        "HR Settings", "custom_lta_sanctioned_days"
    )

    # if not self.custom_period_of_leave_from or not self.custom_period_of_leave_to and self.custom_expense_claim_type == "LTA":
    #     frappe.throw("Period Of Leave (From and To) is required for LTA claim.")

    from_date = getdate(self.custom_period_of_leave_from)
    to_date = getdate(self.custom_period_of_leave_to)
    today_date = getdate(today())
    min_allowed_date = add_days(today_date, -30)

    # From Date cannot be in the future
    if from_date > today_date:
        frappe.throw(
            "Period Of Leave (From) cannot be greater than today's date."
        )

    # From Date cannot be older than 30 days
    if from_date < min_allowed_date and self.custom_expense_claim_type == "LTA":
        frappe.throw(
            f"Period Of Leave (From) cannot be earlier than {min_allowed_date.strftime('%d-%m-%Y')}. You can only apply for the last 30 days."
        )

    # To Date cannot be before From Date
    if to_date < from_date and self.custom_expense_claim_type == "LTA":
        frappe.throw(
            "Period Of Leave (To) cannot be earlier than Period Of Leave (From)."
        )

    # LTA leave period cannot cross calendar years
    if (
        self.custom_expense_claim_type == "LTA"
        and from_date.year != to_date.year
    ):
        frappe.throw(
            "LTA Period Of Leave cannot cross the calendar year. "
            "The Period Of Leave From and To dates must be within the same calendar year."
        )

    # To Date cannot be in the future
    if to_date > today_date and self.custom_expense_claim_type == "LTA":
        frappe.throw(
            f"Period Of Leave (To) cannot be greater than today's date ({today_date.strftime('%d-%m-%Y')}). Please select today's date or an earlier date."
        )

    period_from = getdate(self.custom_period_of_leave_from)
    period_to = getdate(self.custom_period_of_leave_to)

    if period_from > period_to and self.custom_expense_claim_type == "LTA":
        frappe.throw("Period Of Leave From date cannot be after the To date.")

    if period_from < confirmation_date and self.custom_expense_claim_type == "LTA":
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

    if int(breakdown["max_continuous_streak"]) < int(self.custom_availed_or_sanctioned_no_of_days) and self.custom_expense_claim_type == "LTA":
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

    if monthly_basic <= 0 and self.custom_expense_claim_type == "LTA":
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

    if (
        self.custom_expense_claim_type == "LTA"
        and existing_claim_count >= cint(lta_limit)
    ):
        frappe.throw(
            ("Only {0} LTA claim(s) are allowed for the year {1}.").format(
                lta_limit, claim_year
            )
        )

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


def get_role_users(role):
    return [
        d.user
        for d in frappe.get_all(
            "Has Role",
            filters={
                "role": role,
                "parenttype": "User",
            },
            fields=["parent as user"],
        )
    ]


def share_expense_claim(doc,method):
    old_doc = doc.get_doc_before_save()

    if not old_doc or old_doc.workflow_state == doc.workflow_state:
        return

    if doc.workflow_state == "Approved by Reporting Manager":
        hr_manager = get_emp_hr_manager(doc.employee)

        if hr_manager:
            frappe.share.add_docshare(
                doc.doctype,
                doc.name,
                hr_manager,
                read=1,
                write=1,
                select=1,
                submit=1,
                flags={"ignore_share_permission": True},
            )

    elif doc.workflow_state == "Approved by HR":

        users = set()

        # CEO
        if (
            frappe.session.user != "Administrator"
        ):
            users.update(get_role_users("CEO"))

        # PIC
        if frappe.session.user != "Administrator":
            users.update(get_role_users("PIC"))

        # GAO
        if (
            frappe.session.user != "Administrator"
        ):
            users.update(get_role_users("GAO"))

        for user in users:
            frappe.share.add_docshare(
                doc.doctype,
                doc.name,
                user,
                read=1,
                write=1,
                select=1,
                submit=1,
                share=1,
                flags={"ignore_share_permission": True},
            )