import frappe
from frappe.utils import getdate, nowdate
import calendar
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on



def process_pl_after_payroll():
# def process_pl_after_payroll(payroll_entry, method=None):
    # start_date = payroll_entry.start_date
    # end_date = payroll_entry.end_date
    # fiscal_year = payroll_entry.fiscal_year

    today = getdate(nowdate())

    if today.month == 1:
        prev_month_year = today.year - 1
        prev_month = 12
    else:
        prev_month_year = today.year
        prev_month = today.month - 1

    start_date = getdate(f"{prev_month_year}-{prev_month:02d}-01")

    last_day = calendar.monthrange(prev_month_year, prev_month)[1]
    end_date = getdate(f"{prev_month_year}-{prev_month:02d}-{last_day}")

    if start_date.month >= 4:
        year_start_date = getdate(f"{start_date.year}-04-01")
        year_end_date = getdate(f"{start_date.year + 1}-03-31")
    else:
        year_start_date = getdate(f"{start_date.year - 1}-04-01")
        year_end_date = getdate(f"{start_date.year}-03-31")

    leave_type = frappe.db.get_value(
        "Leave Type",
        {"custom_leave_type": "Privilege Leave"},
        ("name", "custom_monthly_allocation_rate", "max_leaves_allowed", "is_carry_forward", "allow_encashment"),
        as_dict=True
    )

    if not leave_type:
        frappe.log_error(
            title=f"Privilege Leave type",
            message="Privilege Leave type not found. PL Accrual process aborted."
        )
        return
    
    employees = get_confirmed_employees()

    if not employees:
        frappe.log_error(
            title=f"Privilege Leave type",
            message="No confirmed employees found. PL Accrual process aborted."
        )
        return

    for emp in employees:
        if emp.final_confirmation_date and getdate(emp.final_confirmation_date) > getdate(end_date):
            frappe.log_error(
                title=f"Privilege Leave type",
                message="Employee {emp.name}: confirmation date is not set or after the payroll end date. Skipping PL accrual."
            )
            continue
        
        effective_start = max(getdate(start_date), getdate(emp.final_confirmation_date))

        eligible_days, total_days = get_eligible_days(
            emp.name, effective_start, end_date
        )

        pl = round((eligible_days / total_days) * leave_type.custom_monthly_allocation_rate, 2)

        if pl > 0:
            allocate_pl(emp.name, leave_type.name, pl, year_start_date, year_end_date, leave_type.is_carry_forward, effective_start, end_date, eligible_days)


def get_confirmed_employees():
    return frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "employment_type": "Confirmed"
        },
        fields=["name", "final_confirmation_date"],
        order_by="name"
    )


def get_eligible_days(employee, start_date, end_date):
    """
    Eligible:
    - Present
    - CL, PL, SL, Comp Off
    - Holidays & Week-offs
    Exclude:
    - Absent
    - LOP / LWP
    """

    total_days = (getdate(end_date) - getdate(start_date)).days + 1

    attendance = frappe.get_all(
        "Attendance",
        {
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
            "status": ["in", ["Present", "On Leave", "Half Day"]]
        },
        ("name", "status", "leave_type", "half_day_status")
    )

    holiday_list = frappe.db.get_value(
        "Employee", employee,
        "holiday_list"
    )

    if not holiday_list:
        frappe.log_error(
            title=f"Privilege Leave type",
            message=f"Holiday List not assigned for Employee {employee}"
        )
        return 0, total_days

    holidays = frappe.get_all(
        "Holiday",
        {
            "parent": holiday_list,
            "holiday_date": ["between", [start_date, end_date]]
        },
        ("holiday_date"),
        as_list=True
    )

    holiday_dates = [h[0] for h in holidays]
    for att in attendance:
        if att.attendance_date in holiday_dates:
            holiday_dates.remove(att.attendance_date)

    eligible_days = 0
    for att in attendance:
        if att.status == "Present":
            eligible_days += 1
        elif att.status == "On Leave" and att.leave_type != "Leave Without Pay":
            eligible_days += 1
        elif att.status == "Half Day":
            if att.half_day_status == "Present" and att.leave_type != "Leave Without Pay":
                eligible_days += 1
            elif att.half_half_day_status == "Present":
                eligible_days += 0.5
            elif att.att.leave_type != "Leave Without Pay":
                eligible_days += 0.5

    eligible_days += len(holiday_dates)

    return max(eligible_days, 0), total_days


def allocate_pl(employee, leave_type, pl_days, year_start_date, year_end_date, is_carry_forward, effective_start, end_date, eligible_days):
    allocation = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "from_date": ["between", [year_start_date, year_end_date]],
            "to_date": year_end_date,
            "docstatus": 1
        },
        limit=1
    )

    if allocation:
        doc = frappe.get_doc("Leave Allocation", allocation[0].name)
        doc.new_leaves_allocated += pl_days
        doc.append("custom_leave_accrual", {
            "from_date": effective_start,
            "to_date": end_date,
            "eligible_days": eligible_days,
            "leave_allocated": pl_days
        })
        doc.submit()
    else:
        doc = frappe.new_doc("Leave Allocation")
        doc.employee = employee
        doc.leave_type = leave_type
        doc.from_date = year_start_date
        doc.to_date = year_end_date
        doc.new_leaves_allocated = pl_days
        doc.carry_forward = 1 if is_carry_forward else 0
        doc.append("custom_leave_accrual", {
            "from_date": effective_start,
            "to_date": end_date,
            "eligible_days": eligible_days,
            "leave_allocated": pl_days
        })
        doc.insert(ignore_permissions=True)
        doc.submit()


# def auto_encash_pl():
#     leave_type = frappe.db.get_value(
#         "Leave Type",
#         {"custom_leave_type": "Privilege Leave"},
#         ("name", "custom_maximum_leave_balance"),
#         as_dict=True
#     )

#     employees = get_confirmed_employees()

#     date = "2026-05-21"

#     for emp in employees:
#         print("Processing Employee:", emp.name)
#         balance = get_leave_balance_on(emp.name, leave_type.name, date)
#         print("balance:", balance)
#         print("Max Leaves Allowed:", leave_type.custom_maximum_leave_balance)

#         if balance <= leave_type.custom_maximum_leave_balance:
#             continue
#         excess = balance - leave_type.custom_maximum_leave_balance
#         print("Excess:", excess)

#         if excess > 0:
#             encash = frappe.new_doc("Leave Encashment")
#             encash.employee = emp.name
#             encash.leave_type = leave_type.name
#             encash.encashment_days = excess
#             encash.encashment_amount = 500
#             encash.insert(ignore_permissions=True)
#             encash.submit()
