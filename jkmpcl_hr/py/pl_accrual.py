from datetime import timedelta
import frappe
from frappe.utils import getdate, nowdate
import calendar

from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_allocation.leave_allocation import create_additional_leave_ledger_entry
from jkmpcl_hr.py.utils import get_current_holiday_list, custom_create_additional_leave_ledger_entry



@frappe.whitelist()
def process_pl_after_payroll(dt=None):
# def process_pl_after_payroll(payroll_entry, method=None):
    # start_date = payroll_entry.start_date
    # end_date = payroll_entry.end_date
    # fiscal_year = payroll_entry.fiscal_year

    if dt:
        today = getdate(dt)
    else:
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
        try:
            if emp.final_confirmation_date and getdate(emp.final_confirmation_date) > getdate(end_date):
                frappe.log_error(
                    title=f"Privilege Leave type",
                    message=f"Employee {emp.name}: confirmation date is not set or after the payroll end date. Skipping PL accrual."
                )
                continue
            
            effective_start = max(getdate(start_date), getdate(emp.final_confirmation_date))

            eligible_days, total_days = get_eligible_days(
                emp.name, effective_start, end_date
            )

            if emp.name == "20111: AJAY  KUMAR":
                print(f"\n\n {eligible_days}  {total_days} {pl} \n\n")
            
            pl = round((eligible_days / total_days) * leave_type.custom_monthly_allocation_rate, 2)
            # if emp.name == "20111: AJAY  KUMAR":
            #     return eligible_days, total_days , pl

            attendance_exists = frappe.db.exists(
                "Attendance",
                {
                    "employee": emp.name,
                    "status":["in", ["Present", "On Leave", "Half Day"]],
                    "attendance_date": ["between", [effective_start, end_date]]
                }
            )        
            if not attendance_exists:
                frappe.log_error(f"Skipping PL accrual for Employee {emp.name}", f"No attendance or leave records found between {effective_start} and {end_date}")
                continue
            else:
                if pl > 0:
                    allocate_pl(emp.name, leave_type.name, pl, year_start_date, year_end_date, leave_type.is_carry_forward, effective_start, end_date, eligible_days, today)
        except Exception as e:
            frappe.log_error(title=f"Error processing PL accrual for Employee {emp.name}", message=str(e))
            continue
    frappe.db.commit()

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

from frappe.utils import getdate, get_last_day, add_days, flt
import frappe


# def get_eligible_days(employee, start_date, end_date):
#     """
#     Deduction Based Logic

#     Eligible Days =
#         Total Days
#         - LWP (from Leave Ledger Entry)
#         - Absent (from Attendance)
#         - Partial (based on business rule)

#     No Holiday Logic Used
#     """

#     start_date = getdate(start_date)
#     end_date = getdate(end_date)

#     total_days = (end_date - start_date).days + 1

#     lle = frappe.qb.DocType("Leave Ledger Entry")

#     lwp_query = (
#         frappe.qb.from_(lle)
#         .select(lle.leaves)
#         .where(
#             (lle.employee == employee)
#             & (lle.leave_type == "Leave Without Pay")
#             & (lle.docstatus == 1)
#             & (lle.is_lwp == 1)
#             # & (lle.custom_is_penalty == 0)
#             & (lle.from_date <= end_date)
#             & (lle.to_date >= start_date)
#         )
#     ).run(as_dict=True)

    
#     lwp_days = sum(
#         abs(flt(row.leaves))
#         for row in lwp_query
#     )

#     attendance = frappe.get_all(
#         "Attendance",
#         filters={
#             "employee": employee,
#             "attendance_date": ["between", [start_date, end_date]],
#             "status": ["in", ["Absent", "Partially"]],
#         },
#         fields=["status"],
#     )

#     absent_days = 0
#     partial_days = 0

#     for att in attendance:
#         if att.status in ["Absent", "Partially"]:
#             absent_days += 1
#         # elif att.status == :
#         #     partial_days += 0.5

#     total_deduction = lwp_days + absent_days + partial_days
    

#     eligible_days = total_days - total_deduction
#     if employee == "20111: AJAY  KUMAR":
#         print(f"\n\n {eligible_days}  {total_deduction} {total_days} {start_date} {end_date} \n {lwp_query}  {lwp_days}\n  {attendance}  {total_deduction} {lwp_days} + {absent_days} + {partial_days}\n\n")
#     return max(flt(eligible_days), 0), total_days

def get_eligible_days(employee, start_date, end_date):
    """
    Final Logic: Attendance + Smart Penalty Adjustment

    Rules:
        Present = 1
        Weekly Off / Holiday / RH = 1
        On Leave = 1
        Half Day = 0.5 (or 1 if Comp Off)
        Absent = 0

    Penalty:
        Absent → +1
        Half Day → +0.5 (only remaining portion)
    """

    start_date = getdate(start_date)
    end_date = getdate(end_date)

    total_days = (end_date - start_date).days + 1

    # -------------------------
    # Attendance Map (by date)
    # -------------------------
    attendance_list = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
        },
        fields=["attendance_date", "status", "leave_type", "half_day_status"],
    )
    attendance_map = {att.attendance_date: att for att in attendance_list}
    
    eligible_days = 0
    
    for date in attendance_map:
        att = attendance_map[date]
        status = att.status
        leave_type = att.leave_type
    
        if status == "Half Day":
            if leave_type == "Compensatory Off":
                eligible_days += 1
            elif att.half_day_status == "Present":
                eligible_days += 1
            else:
                eligible_days += 0.5
    
        elif status in [
            "Present",
            "On Leave",
            "Weekly Off",
            "Holiday",
            "Restricted Holiday",
        ]:
            if status == "On Leave" and leave_type != "Leave Without Pay":
                eligible_days += 1
            else:
                eligible_days += 1

        # Absent = 0 (do nothing)

    # -------------------------
    # Penalty Adjustment
    # -------------------------
    lle = frappe.qb.DocType("Leave Ledger Entry")

    penalty_entries = (
        frappe.qb.from_(lle)
        .select(lle.leaves)
        .where(
            (lle.employee == employee)
            & (lle.docstatus == 1)
            & (lle.custom_is_penalty == 1)
            & (lle.is_lwp == 0)
            & (lle.from_date.between(start_date, end_date))
            # & (lle.from_date <= end_date)
            # & (lle.to_date >= start_date)
        )
    ).run(as_dict=True)

    penalty_days_added = sum(
        abs(flt(row.leaves))
        for row in penalty_entries
    )

    
    
    # for row in penalty_entries:
    #     current_date = max(getdate(row.from_date), start_date)
    #     to_date = min(getdate(row.to_date), end_date)

    #     while current_date <= to_date:
    #         att = attendance_map.get(current_date)

    #         if att:
    #             if att.status == "Absent":
    #                 penalty_days_added += 1

    #             elif att.status == "Half Day":
    #                 if att.leave_type != "Compensatory Off":
    #                     penalty_days_added += 0.5

    #         else:
    #             # No attendance → treat as absent
    #             penalty_days_added += 1

    #         current_date += timedelta(days=1)

    # -------------------------
    # Final Eligible Days
    # -------------------------
    final_eligible_days = eligible_days + penalty_days_added

    if employee == "20111: AJAY  KUMAR":
        print(
            f"""
            Attendance Eligible: {eligible_days}
            Penalty Adjustment: {penalty_days_added}
            Final Eligible: {final_eligible_days}
            Total Days: {total_days}
            """
        )

    return max(flt(final_eligible_days), 0), total_days

# def get_eligible_days(employee, start_date, end_date, date):
#     """
#     Eligible:
#     - Present
#     - CL, PL, SL, Comp Off
#     - Holidays & Week-offs
#     Exclude:
#     - Absent
#     - LOP / LWP
#     """

#     total_days = (getdate(end_date) - getdate(start_date)).days + 1

#     attendance = frappe.get_all(
#         "Attendance",
#         {
#             "employee": employee,
#             "attendance_date": ["between", [start_date, end_date]],
#             "status": ["in", ["Present", "On Leave", "Half Day"]]
#         },
#         ("name", "status", "leave_type", "half_day_status")
#     )

#     holiday_list = frappe.db.get_value(
#         "Employee", employee,
#         "holiday_list"
#     )

#     assign_holiday_list = get_current_holiday_list(employee, date)
    
#     if assign_holiday_list:
#         correct_holiday_list =  assign_holiday_list
#     else:
#         correct_holiday_list = holiday_list if holiday_list else None

#     if not correct_holiday_list:
#         frappe.log_error(
#             title=f"Privilege Leave type",
#             message=f"Holiday List not assigned for Employee {employee}"
#         )
#         return 0, total_days

#     holidays = frappe.get_all(
#         "Holiday",
#         {
#             "parent": correct_holiday_list,
#             "holiday_date": ["between", [start_date, end_date]]
#         },
#         ("holiday_date"),
#         as_list=True
#     )

#     holiday_dates = [h[0] for h in holidays]
#     for att in attendance:
#         if att.attendance_date in holiday_dates:
#             holiday_dates.remove(att.attendance_date)

#     eligible_days = 0
#     for att in attendance:
#         if att.status == "Present":
#             eligible_days += 1
#         elif att.status == "On Leave" and att.leave_type != "Leave Without Pay":
#             eligible_days += 1
            
#         elif att.status == "Half Day":
#             if att.half_day_status == "Present" and att.leave_type != "Leave Without Pay":
#                 eligible_days += 1
#             elif att.half_day_status == "Present":
#                 eligible_days += 0.5
#             elif att.leave_type != "Leave Without Pay":
#                 eligible_days += 0.5
    
#     eligible_days += len(holiday_dates)

#     return max(eligible_days, 0), total_days


def allocate_pl(employee, leave_type, pl_days, year_start_date, year_end_date, is_carry_forward, effective_start, end_date, eligible_days, today_date):
    
    if employee == "001100: CL Test Eleven":
        print(f"\n\n allocatinf pl  \n\n")
    effective_start = getdate(effective_start)
    end_date = getdate(end_date)
    
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
        already_allocated = any(
            getdate(row.from_date) == effective_start
            and getdate(row.to_date) == end_date
            for row in doc.custom_leave_accrual
        )
        
        if already_allocated:
        # Accrual already processed for this period
            return
        
        new_allocation = flt(doc.total_leaves_allocated) + flt(pl_days)
                            
        if new_allocation != doc.total_leaves_allocated:
                doc.db_set("total_leaves_allocated", new_allocation, update_modified=False)

                # date = today_date or frappe.flags.current_date or getdate()
                # date = end_date
                # print(f"\n\n main date{date}\n\n")
                custom_create_additional_leave_ledger_entry(doc, pl_days, end_date, is_accrual=1)
            
                frappe.get_doc({
                    "doctype": "Leave Accrual",
                    "parent": doc.name,
                    "parenttype": "Leave Allocation",
                    "parentfield": "custom_leave_accrual",
                    "from_date": effective_start,
                    "to_date": end_date,
                    "eligible_days": eligible_days,
                    "leave_allocated": pl_days,
                }).insert(ignore_permissions=True)

                
                doc.db_set(
                    "custom_last_allocation_date",
                    today_date,
                    update_modified=False
                )
        # doc.new_leaves_allocated += pl_days
        # doc.custom_last_allocation_date = today_date
        # doc.append("custom_leave_accrual", {
        #     "from_date": effective_start,
        #     "to_date": end_date,
        #     "eligible_days": eligible_days,
        #     "leave_allocated": pl_days
        # })
        # doc.submit()
    else:
        doc = frappe.new_doc("Leave Allocation")
        doc.employee = employee
        doc.leave_type = leave_type
        doc.from_date = year_start_date
        doc.to_date = year_end_date
        doc.new_leaves_allocated = pl_days
        doc.carry_forward = 1 if is_carry_forward else 0
        doc.custom_last_allocation_date = end_date
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
