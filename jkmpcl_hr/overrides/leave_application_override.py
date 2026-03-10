import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate, getdate, datetime
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication, get_leave_balance_on, get_leaves_pending_approval_for_period, get_number_of_leave_days, is_lwp, get_leave_allocation_records, get_leaves_for_period, get_manually_expired_leaves, get_remaining_leaves, get_allocation_expiry_for_cf_leaves




def custom_validate_balance_leaves(self):
    precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 2

    if self.from_date and self.to_date:
        self.total_leave_days = get_number_of_leave_days(
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
    print(f"\n\n CUSTOM CALLED get_leave_balance_on\n\n")
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

        for rec in off_day_records:
            if not rec.leave_allocation:
                continue

            allocation_to_date = frappe.db.get_value(
                "Leave Allocation",
                rec.leave_allocation,
                "to_date",
            )

            if allocation_to_date and getdate(allocation_to_date) >= date:
                valid_balance += 1

        if for_consumption:
            return {
                "leave_balance": valid_balance,
                "leave_balance_for_consumption": valid_balance,
            }

        print(f"\n\n  VALID BALANCE {valid_balance} \n\n")
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



def custom_create_or_update_attendance(self, attendance_name, date):
    status = (
        "Half Day" if self.half_day_date and getdate(date) == getdate(self.half_day_date) else "On Leave"
    )
    has_checkin = frappe.db.exists("Employee Checkin", {"employee": self.employee, "time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]]})
    
    
    if attendance_name:
        # update existing attendance, change absent to on leave or half day
        doc = frappe.get_doc("Attendance", attendance_name)
        
        half_day_status = None
        modify_half_day_status = 0
                
        # half_day_status = None if status == "On Leave" else "Present"
        # modify_half_day_status = 1 if doc.status == "Absent" and status == "Half Day" else 0
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
        # make new attendance and submit it
        doc = frappe.new_doc("Attendance")
        doc.employee = self.employee
        doc.employee_name = self.employee_name
        doc.attendance_date = date
        doc.company = self.company
        doc.leave_type = self.leave_type
        doc.leave_application = self.name
        doc.status = status
        # doc.half_day_status = "Present" if status == "Half Day" else None
        # doc.modify_half_day_status = 1 if status == "Half Day" else 0
    
        if status == "Half Day":
            doc.half_day_status = "Present" if has_checkin else "Absent"
            doc.modify_half_day_status = 1 if has_checkin else 0
        else:
            doc.half_day_status = None
            doc.modify_half_day_status = 0
    
        doc.flags.ignore_validate = True  # ignores check leave record validation in attendance
        doc.insert(ignore_permissions=True)
        doc.submit()
