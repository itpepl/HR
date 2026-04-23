import frappe
from frappe import _
from datetime import timedelta

from frappe.utils import cint, flt, nowdate, getdate, datetime, date_diff, cstr
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication, get_leave_balance_on, get_leaves_pending_approval_for_period, get_number_of_leave_days, is_lwp, get_leave_allocation_records, get_leaves_for_period, get_manually_expired_leaves, get_remaining_leaves, get_allocation_expiry_for_cf_leaves, get_holiday_dates_between_range, get_holiday_list_for_employee

from hrms.hr.utils import get_holidays_for_employee



class CustomLeaveApplication(LeaveApplication):
    
    def on_submit(self):
        if self.status in ["Open", "Cancelled"]:
            frappe.throw(_("Only Leave Applications with status 'Approved' and 'Rejected' can be submitted"))

        self.validate_back_dated_application()
        self.update_attendance()
        self.validate_for_self_approval()

        # notify leave applier about approval
        if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
            self.notify_employee()

        self.create_leave_ledger_entry()
        # # create a reverse ledger entry for backdated leave applications for whom expiry entry already exists
        # leave_allocation = self.get_leave_allocation()
        # if not leave_allocation:
        #     return
        # to_date = leave_allocation.get("to_date")
        # can_expire = not frappe.db.get_value("Leave Type", self.leave_type, "is_carry_forward")

        # if to_date < getdate() and can_expire:
        #     args = frappe._dict(
        #         leaves=self.total_leave_days, from_date=to_date, to_date=to_date, is_carry_forward=0
        #     )
        #     create_leave_ledger_entry(self, args)

        self.reload()


def custom_validate_balance_leaves(self):
    precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 2

    if self.from_date and self.to_date:
        self.total_leave_days = custom_get_number_of_leave_days(
            self.employee,
            self.leave_type,
            self.from_date,
            self.to_date,
            self.half_day,
            self.half_day_date,
        )

        if self.total_leave_days <= 0:
            frappe.throw(
                _(
                    "The day(s) on which you are applying for leave are holidays. You need not apply for leave."
                )
            )

        if not is_lwp(self.leave_type):
            leave_balance = custom_get_leave_balance_on(
                self.employee,
                self.leave_type,
                self.from_date,
                self.to_date,
                consider_all_leaves_in_the_allocation_period=True,
                for_consumption=True,
                leave_app_id=self.name,
            )
            
            leave_balance_for_consumption = flt(
                leave_balance.get("leave_balance_for_consumption"), precision
            )

            leave_type = frappe.db.get_value("Leave Type", self.leave_type, "custom_leave_type")

            
            if leave_type not in ["Medical Emergency Leave", "Maternity Leave", "Special Maternity Leave", "Child Adoption Leave"] and self.status != "Rejected" and (
                leave_balance_for_consumption < self.total_leave_days or not leave_balance_for_consumption
            ):
                self.show_insufficient_balance_message(leave_balance_for_consumption)

    

# * OVERRIDING DEFAULT WHITELISTED METHOD
@frappe.whitelist()
def custom_get_leave_balance_on(
    employee: str,
    leave_type: str,
    date: datetime.date,
    to_date: datetime.date | None = None,
    consider_all_leaves_in_the_allocation_period: bool = False,
    for_consumption: bool = False,
    leave_app_id: str | None = None,
):
    """
    Returns leave balance till date
    :param employee: employee name
    :param leave_type: leave type
    :param date: date to check balance on
    :param to_date: future date to check for allocation expiry
    :param consider_all_leaves_in_the_allocation_period: consider all leaves taken till the allocation end date
    :param for_consumption: flag to check if leave balance is required for consumption or display
            eg: employee has leave balance = 10 but allocation is expiring in 1 day so employee can only consume 1 leave
            in this case leave_balance = 10 but leave_balance_for_consumption = 1
            if True, returns a dict eg: {'leave_balance': 10, 'leave_balance_for_consumption': 1}
            else, returns leave_balance (in this case 10)
    """
    if not to_date:
        to_date = nowdate()

    date = getdate(date)

    if leave_type == "Compensatory Off":

        off_day_records = frappe.get_all(
            "Off-Day Work Request",
            filters={
                "employee": employee,
                "docstatus": 1,
                "comp_off_created": 1,
                "leave_application": ["is", "not set"],
            },
            fields=["name", "leave_allocation"],
        )

        valid_balance = 0
        leave_balance_for_consumption = 0
        for rec in off_day_records:
            if not rec.leave_allocation:
                continue
            # * IN CASE LEAVE APPLICATION IS CREATED BUT NOT YET APPROVED OR REJECTED
            if a := frappe.db.exists("Leave Application", {"docstatus":["<",2], "custom_off_day_work_request": rec.name}, "name"):
                if for_consumption and leave_app_id and a == leave_app_id:
                    leave_balance_for_consumption += 1
                continue

            allocation_to_date = frappe.db.get_value(
                "Leave Allocation",
                rec.leave_allocation,
                "to_date",
            )

            if allocation_to_date and getdate(allocation_to_date) >= date:
                valid_balance += 1
                leave_balance_for_consumption +=1

        if for_consumption:
            return {
                "leave_balance": valid_balance,
                "leave_balance_for_consumption": leave_balance_for_consumption,
            }

        
        return valid_balance

    allocation_records = get_leave_allocation_records(employee, date, leave_type)
    allocation = allocation_records.get(leave_type, frappe._dict())
    end_date = (
        allocation.to_date if (allocation and cint(consider_all_leaves_in_the_allocation_period)) else date
    )
    
    cf_expiry = get_allocation_expiry_for_cf_leaves(employee, leave_type, to_date, allocation.from_date)

    leaves_taken = get_leaves_for_period(employee, leave_type, allocation.from_date, end_date)
    manually_expired_leaves = get_manually_expired_leaves(
        employee, leave_type, allocation.from_date, end_date
    )
    remaining_leaves = get_remaining_leaves(
        allocation, leaves_taken, date, cf_expiry, manually_expired_leaves
    )

    leaves_pending = get_leaves_pending_approval_for_period(employee, leave_type, allocation.from_date, to_date)
    
    
    if leaves_pending:
        leave_app_list = get_pending_leaves_app_id(employee, leave_type, allocation.from_date, to_date)
        frappe.log_error("custom_leave_balance_on", f"{leave_app_list}")
        if leave_app_list and leave_app_id and leave_app_id in leave_app_list:
            
            leaves_pending -= frappe.db.get_value("Leave Application", leave_app_id, "total_leave_days") or 0 
            
        frappe.log_error("custom_leaves_pending", f"{leaves_pending}")
    
    if for_consumption:
        
        remaining_leaves["leave_balance_for_consumption"] = remaining_leaves.get("leave_balance") - leaves_pending
        remaining_leaves["leave_balance"] = remaining_leaves.get("leave_balance") - leaves_pending
        return remaining_leaves
    else:
        return remaining_leaves.get("leave_balance") - leaves_pending

def get_pending_leaves_app_id(employee, leave_type, from_date, to_date):
    leave_app_ids = frappe.db.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "status": "Open",
        },
        or_filters={
            "from_date": ["between", (from_date, to_date)],
            "to_date": ["between", (from_date, to_date)],
        },
        pluck="name",
    )

    return leave_app_ids


def custom_update_attendance(self):
    if self.status != "Approved":
        return

    for dt in daterange(getdate(self.from_date), getdate(self.to_date)):
        date = dt.strftime("%Y-%m-%d")

        attendance_name = frappe.db.exists(
            "Attendance",
            dict(
                employee=self.employee,
                attendance_date=date,
                docstatus=("!=", 2),
            ),
        )

        # ALWAYS create/update attendance (no skipping)
        self.create_or_update_attendance(attendance_name, date) 
    
# def custom_create_or_update_attendance(self, attendance_name, date):
    
#     day_type = get_day_type(self.employee, date)

#     #  If it's holiday/weekoff → override leave logic
#     if day_type:
#         status = day_type
#     else:
#         status = (
#             "Half Day"
#             if self.half_day_date and getdate(date) == getdate(self.half_day_date)
#             else "On Leave"
#         )

#     has_checkin = frappe.db.exists(
#         "Employee Checkin",
#         {
#             "employee": self.employee,
#             "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]],
#         },
#     )

#     if attendance_name:
#         doc = frappe.get_doc("Attendance", attendance_name)
#         if doc.status == "Present":
#             return
#         half_day_status = None
#         modify_half_day_status = 0

#         if status == "Half Day":
#             half_day_status = "Present" if has_checkin else "Absent"
#             modify_half_day_status = 1 if has_checkin and doc.status == "Absent" else 0

#         doc.db_set(
#             {
#                 "status": status,
#                 "leave_type": self.leave_type,
#                 "leave_application": self.name,
#                 "half_day_status": half_day_status,
#                 "modify_half_day_status": modify_half_day_status,
#             }
#         )

#     else:
#         doc = frappe.new_doc("Attendance")
#         doc.employee = self.employee
#         doc.employee_name = self.employee_name
#         doc.attendance_date = date
#         doc.company = self.company
#         doc.leave_type = self.leave_type
#         doc.leave_application = self.name
#         doc.status = status

#         if status == "Half Day":
#             doc.half_day_status = "Present" if has_checkin else "Absent"
#             doc.modify_half_day_status = 1 if has_checkin else 0
#         else:
#             doc.half_day_status = None
#             doc.modify_half_day_status = 0

#         doc.flags.ignore_validate = True
#         doc.insert(ignore_permissions=True)
#         doc.submit()

def custom_create_or_update_attendance(self, attendance_name, date):

    SPECIAL_LEAVE_TYPES = [
        "Leave Without Pay",
        "Maternity Leave",
        "Special Maternity Leave",
        "Child Adoption Leave",
        "Medical Emergency Leave",
    ]

    leave_type_name = frappe.db.get_value("Leave Type", self.leave_type, "custom_leave_type")

    day_type = get_day_type(self.employee, date)

    # 🔥 CORE LOGIC CHANGE
    if leave_type_name in SPECIAL_LEAVE_TYPES:
        # ALWAYS mark as leave (ignore holiday/weekoff)
        status = (
            "Half Day"
            if self.half_day_date and getdate(date) == getdate(self.half_day_date)
            else "On Leave"
        )
    else:
        # Existing behavior
        if day_type:
            status = day_type
        else:
            status = (
                "Half Day"
                if self.half_day_date and getdate(date) == getdate(self.half_day_date)
                else "On Leave"
            )

    has_checkin = frappe.db.exists(
        "Employee Checkin",
        {
            "employee": self.employee,
            "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]],
        },
    )

    if attendance_name:
        doc = frappe.get_doc("Attendance", attendance_name)

        # Don't override Present
        if doc.status == "Present":
            return
        half_day_status = None
        modify_half_day_status = 0

        if status == "Half Day":
            half_day_status = "Present" if has_checkin else "Absent"
            modify_half_day_status = 1 if has_checkin and doc.status == "Absent" else 0

        doc.db_set(
            {
                "status": status,
                "leave_type": self.leave_type,
                "leave_application": self.name,
                "half_day_status": half_day_status,
                "modify_half_day_status": modify_half_day_status,
            }
        )

    else:
        doc = frappe.new_doc("Attendance")
        doc.employee = self.employee
        doc.employee_name = self.employee_name
        doc.attendance_date = date
        doc.company = self.company
        doc.leave_type = self.leave_type
        doc.leave_application = self.name
        doc.status = status

        if status == "Half Day":
            doc.half_day_status = "Present" if has_checkin else "Absent"
            doc.modify_half_day_status = 1 if has_checkin else 0
        else:
            doc.half_day_status = None
            doc.modify_half_day_status = 0

        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True)
        doc.submit()





# * OVERRIDING WHITELISTED METHOD

@frappe.whitelist()
def custom_get_number_of_leave_days(
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	half_day: int | str | None = None,
	half_day_date: datetime.date | str | None = None,
	holiday_list: str | None = None,
) -> float:
    """Returns number of leave days between 2 dates after considering half day and holidays
    (Based on the include_holiday setting in Leave Type)"""
    
    print(f"\n\n Custom Method Called adasdasdasdasda \n\n")
    number_of_days = 0
    if cint(half_day) == 1:
        if getdate(from_date) == getdate(to_date):
            number_of_days = 0.5
        elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(to_date):
            number_of_days = date_diff(to_date, from_date) + 0.5
        else:
            number_of_days = date_diff(to_date, from_date) + 1
    else:
        number_of_days = date_diff(to_date, from_date) + 1

    if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
        print(f"\n\n  number of days {number_of_days}  {custom_get_holidays(employee, from_date, to_date, holiday_list=holiday_list)} {flt(number_of_days) - flt(custom_get_holidays(employee, from_date, to_date, holiday_list=holiday_list))} \n\n")
        number_of_days = flt(number_of_days) - flt(
            # get_holidays(employee, from_date, to_date, holiday_list=holiday_list)
            custom_get_holidays(employee, from_date, to_date, holiday_list=holiday_list)
        )
    return number_of_days



@frappe.whitelist()
def custom_get_holidays(employee, from_date, to_date, holiday_list=None):
    """Get holidays between two dates with Restricted Holiday pair logic"""

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    holiday_dates = get_holiday_dates_between_range(employee, from_date, to_date)

    if not holiday_dates:
        return 0

    if not holiday_list:
        holiday_list = get_holiday_list_for_employee(employee, as_on=from_date)

    if not holiday_list:
        return len(holiday_dates)

    valid_holidays = []

    holiday_records = frappe.get_all(
        "Holiday",
        filters={"parent": holiday_list, "holiday_date": ["in", holiday_dates]},
        fields=[
            "holiday_date",
            "weekly_off",
            "custom_is_restricted_holiday",
            "custom_restricted_holiday_date",
        ],
    )

    
    if not holiday_records:
        return len(holiday_dates)

    pair_dates = [
        d.get("custom_restricted_holiday_date")
        for d in holiday_records
        if d.get("custom_is_restricted_holiday") and d.get("custom_restricted_holiday_date")
    ]

    pair_holiday_map = {}

    if pair_dates:
        
        for p_date in pair_dates:
            pair_holiday_list = frappe.get_all(
                "Holiday List Assignment",
                {
                    "assigned_to": employee,
                    "from_date": ["<=", p_date],
                    "docstatus": 1,
                },
                order_by="from_date desc",
                limit=1,
                pluck="holiday_list",
            )

            pair_holiday_list = pair_holiday_list[0] if pair_holiday_list else holiday_list

            pair_doc = frappe.db.get_value(
                "Holiday",
                {
                    "parent": pair_holiday_list,
                    "holiday_date": p_date,
                },
                ["holiday_date", "weekly_off"],
                as_dict=True,
            )

            if pair_doc:
                pair_holiday_map[p_date] = pair_doc

    for hd in holiday_records:

        holiday_date = hd.get("holiday_date")
        pair_date = hd.get("custom_restricted_holiday_date")

        # Normal holiday
        if not hd.get("custom_is_restricted_holiday"):
            
            valid_holidays.append(holiday_date)
            continue

        # If current date weekly off
        if hd.get("weekly_off"):
            valid_holidays.append(holiday_date)
            continue
        
        if pair_date and getdate(holiday_date) < getdate(pair_date):            
            valid_holidays.append(holiday_date)
            continue
        
        pair_doc = pair_holiday_map.get(pair_date)

        # If pair date weekly off
        if pair_doc and pair_doc.get("weekly_off"):
            valid_holidays.append(holiday_date)
            continue
        
        # Attendance check
        if pair_date and frappe.db.exists(
            "Attendance",
            {
                "employee": employee,
                "attendance_date": pair_date,
                "status": ["in", ["Present", "Half Day", "On Leave", "Weekly Off"]],
            },
            
            'status'
        ):
            
            valid_holidays.append(holiday_date)
    return len(valid_holidays)
# @frappe.whitelist()
# def custom_get_holidays(employee, from_date, to_date, holiday_list=None):
#     """Get holidays between two dates with Restricted Holiday pair logic"""
    
#     from_date = getdate(from_date)
#     to_date = getdate(to_date)

#     holiday_dates = get_holiday_dates_between_range(employee, from_date, to_date)
#     print(f"\n\n holiday dates {holiday_dates}\n\n")
#     if not holiday_dates:
#         return 0

#     if not holiday_list:
#         holiday_list = get_holiday_list_for_employee(employee, as_on=from_date)

#     if not holiday_list:
#         return len(holiday_dates)

#     valid_holidays = []
    
#     holiday_records = frappe.db.get_all(
#         "Holiday",
#         filters={"parent": holiday_list, "holiday_date":["in", holiday_dates]},
#         fields=[
#             "holiday_date",
#             "weekly_off",
#             "custom_is_restricted_holiday",
#             "custom_restricted_holiday_date",
#         ],
#     )
    
#     if not holiday_records:
#         return len(holiday_dates)
    
#     print(f"\n\n holiday records {holiday_records}\n\n")
#     pair_holiday_dates = []
#     pair_holiday_map = {}

#     pair_dates = [d.get("custom_restricted_holiday_date") for d in holiday_records if d.get("custom_is_restricted_holiday") and d.get("custom_restricted_holiday_date")]
    
#     if pair_dates:
#         pair_holiday_dates = frappe.db.get_all("Holiday", {"parent": holiday_list, "holiday_date":["in", pair_dates]}, ["holiday_date", "weekly_off", "custom_is_restricted_holiday", "custom_restricted_holiday_date"])
#         if pair_holiday_dates:
#             pair_holiday_map = {pd.get("holiday_date"): pd for pd in pair_holiday_dates}
        
    
#     for hd in holiday_records:
#         if not hd.get("custom_is_restricted_holiday"):
#             valid_holidays.append(hd.get("holiday_date"))
#         elif hd.get("weekly_off"):
#             valid_holidays.append(hd.get("holiday_date"))
#         else:
#             if pair_holiday_map:
#                 if pair_holiday_map[hd.get("custom_restricted_holiday_date")].get("weekly_off"):
#                     valid_holidays.append(hd.get("holiday_date"))
                
#                 elif not frappe.db.exists("Attendance", {"employee": employee, "attendance_date":hd.get("custom_restricted_holiday_date"), "docstatus":["!=", 2]}):
#                     valid_holidays.append(hd.get("holiday_date"))
    
#     return len(valid_holidays)
    # else:
    #     pair_holiday_dates = {}
        
        
    
    
    # if pair_holiday_dates:    
    #     for dt in holiday_records:
    #         for pdt in pair_holiday_dates:
    #             if dt.get("holiday_date") == pdt.get("custom_restricted_holiday_date") and pdt.get("holiday_date") == dt.get("custom_restricted_holiday_date"):
    #                 combined_holiday_dates.append ({"cur_holiday": dt,"pair_holiday": pdt})
    #                 break
                        
    # if not combined_holiday_dates:
    #     return len(holiday_dates)

    # for hd in combined_holiday_dates:
    #     if not hd.get("cur_holiday").get("weekly_off") and not hd.get("pair_holiday").get("weekly_off"):
    #         pass
    #     else:
    #         valid_holidays
        
        
        
    #         pair_date = getdate(hd.get("custom_restricted_holiday_date"))
            
    #         if frappe.db.exists("Attendance", {"employee": employee, "attendance_date": pair_date, "docstatus":["!=", 2]}):
    #             valid_holidays.append(hd.get("holiday_date"))
                
                
    #     else:
    #         valid_holidays.append(hd.get("holiday_date"))
    

def daterange(start_date, end_date):
	for n in range(int((end_date - start_date).days) + 1):
		yield start_date + timedelta(n)

# def custom_update_attendance(self):
#         if self.status != "Approved":
#             return

#         holiday_dates = []
#         if not frappe.db.get_value("Leave Type", self.leave_type, "include_holiday"):
#             holiday_dates = custom_get_holiday_dates_for_employee(self.employee, self.from_date, self.to_date)
            
        
#         for dt in daterange(getdate(self.from_date), getdate(self.to_date)):
#             date = dt.strftime("%Y-%m-%d")
#             # check for existing attenadnce absent or if half day with half day status absent,
#             attendance_name = frappe.db.exists( 
#                 "Attendance",
#                 dict(
#                     employee=self.employee,
#                     attendance_date=date,
#                     docstatus=("!=", 2),
#                 ),
#             )
#             # don't mark attendance for holidays
#             # if leave type does not include holidays within leaves as leaves
            
#             # if date in holiday_dates:
#             #     if attendance_name:
#             #         # cancel and delete existing attendance for holidays
#             #         attendance = frappe.get_doc("Attendance", attendance_name)
#             #         attendance.flags.ignore_permissions = True
#             #         if attendance.docstatus == 1:
#             #             attendance.cancel()
#             #         frappe.delete_doc("Attendance", attendance_name, force=1)
#             #     continue

#             self.create_or_update_attendance(attendance_name, date)




def custom_get_holiday_dates_for_employee(employee, start_date, end_date):
    """Return a list of holiday dates for the given employee between start_date and end_date"""

    start_date = getdate(start_date)
    end_date = getdate(end_date)

    holidays = get_holidays_for_employee(employee, start_date, end_date)

    if not holidays:
        return []

    holiday_dates = [h.holiday_date for h in holidays]

    holiday_list = get_holiday_list_for_employee(employee, as_on=start_date)

    if not holiday_list:
        return [cstr(d) for d in holiday_dates]

    valid_holidays = []

    holiday_records = frappe.get_all(
        "Holiday",
        filters={"parent": holiday_list, "holiday_date": ["in", holiday_dates]},
        fields=[
            "holiday_date",
            "weekly_off",
            "custom_is_restricted_holiday",
            "custom_restricted_holiday_date",
        ],
    )

    if not holiday_records:
        return [cstr(d) for d in holiday_dates]

    pair_dates = [
        d.custom_restricted_holiday_date
        for d in holiday_records
        if d.custom_is_restricted_holiday and d.custom_restricted_holiday_date
    ]

    pair_holiday_map = {}

    if pair_dates:
        for p_date in pair_dates:
            pair_holiday_list = frappe.get_all(
                "Holiday List Assignment",
                {
                    "assigned_to": employee,
                    "from_date": ["<=", p_date],
                    "docstatus": 1,
                },
                order_by="from_date desc",
                limit=1,
                pluck="holiday_list",
            )

            pair_holiday_list = pair_holiday_list[0] if pair_holiday_list else holiday_list

            pair_doc = frappe.db.get_value(
                "Holiday",
                {
                    "parent": pair_holiday_list,
                    "holiday_date": p_date,
                },
                ["holiday_date", "weekly_off"],
                as_dict=True,
            )

            if pair_doc:
                pair_holiday_map[p_date] = pair_doc
        # pair_holidays = frappe.get_all(
        #     "Holiday",
        #     filters={"parent": holiday_list, "holiday_date": ["in", pair_dates]},
        #     fields=["holiday_date", "weekly_off"],
        # )

        # pair_holiday_map = {p.holiday_date: p for p in pair_holidays}

    for hd in holiday_records:

        holiday_date = hd.holiday_date
        pair_date = hd.custom_restricted_holiday_date

        # normal holiday
        if not hd.custom_is_restricted_holiday:
            valid_holidays.append(holiday_date)
            continue

        # if current date weekly off
        if hd.weekly_off:
            valid_holidays.append(holiday_date)
            continue
        
        if pair_date and getdate(holiday_date) < getdate(pair_date):
            valid_holidays.append(holiday_date)
            continue
        pair_doc = pair_holiday_map.get(pair_date)

        # if pair weekly off
        if pair_doc and pair_doc.weekly_off:
            valid_holidays.append(holiday_date)
            continue

        # attendance rule
        if pair_date and frappe.db.exists(
            "Attendance",
            {
                "employee": employee,
                "attendance_date": pair_date,
                "status": "Present",
            },
        ):
            valid_holidays.append(holiday_date)

    return [cstr(d) for d in valid_holidays]



def get_day_type(employee, date):
    holiday_list = get_holiday_list_for_employee(employee, as_on=date)

    if not holiday_list:
        return None

    holiday = frappe.db.get_value(
        "Holiday",
        {
            "parent": holiday_list,
            "holiday_date": date,
        },
        [
            "weekly_off",
            "custom_is_restricted_holiday",
        ],
        as_dict=True,
    )

    if not holiday:
        return None

    # PRIORITY: Weekly Off > Holiday > Restricted Holiday
    if holiday.weekly_off:
        return "Weekly Off"
    elif holiday.custom_is_restricted_holiday:
        return "Restricted Holiday"
    else:
        return "Holiday"