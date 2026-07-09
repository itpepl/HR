import frappe
from frappe.utils import getdate, nowdate,formatdate,add_days
from datetime import timedelta  
from datetime import datetime, date as sys_date
import frappe,uuid, os, mimetypes, calendar, re
from frappe.utils import formatdate


def check_attendance_lock(date, employee=None):

    # ============================================
    # GET EMPLOYEE BRANCH
    # ============================================
    employee_branch = None

    if employee:
        employee_branch = frappe.db.get_value(
            "Employee",
            employee,
            "branch"
        )

    # ============================================
    # GET ATTENDANCE LOCKS
    # ============================================
    locks = frappe.get_all(
        "Attendance Lock",
        filters={
            "from_date": ["<=", date],
            "to_date": [">=", date],
            "docstatus": ["!=", 2]
        },
        fields=[
            "name",
            "month",
            "branch"
        ],
        order_by="creation desc"
    )

    for lock in locks:

        # ============================================
        # BRANCH CHECK
        # ============================================
        if lock.branch and employee_branch:

            if lock.branch != employee_branch:
                continue

        month = lock.month

        if not month:
            month = formatdate(date, "MMMM yyyy")

        return month

    return None


@frappe.whitelist()
def get_attendance(
    employeeId,
    date=None,
    from_date=None,
    to_date=None,
    status=None,
    limit=None,
    limit_start=0
):
    try:
        if not employeeId:
            frappe.throw("Employee ID is required")

        # If from_date & to_date given → use them
        if from_date and to_date:
            start_date = from_date
            end_date = to_date

        # If only date is given → pick whole month
        elif date:
            specific_date = datetime.strptime(date, "%Y-%m-%d").date()
            current_month = specific_date.month
            current_year = specific_date.year
            total_days_in_month = calendar.monthrange(current_year, current_month)[1]

            start_date = f"{current_year}-{current_month:02d}-01"
            end_date = f"{current_year}-{current_month:02d}-{total_days_in_month}"

        else:
            frappe.throw("Either 'date' OR 'from_date' and 'to_date' is required.")

        # Base filters
        month_filters = [
            ["employee", "=", employeeId],
            ["attendance_date", "between", [start_date, end_date]],
        ]

        # Status filter (optional)
        if status:
            if "," in status:
                status_list = [s.strip() for s in status.split(",")]
                month_filters.append(["status", "in", status_list])
            else:
                month_filters.append(["status", "=", status])

        fields = [
            "name",
            "status",
            "check_in",
            "attendance_date",
            "in_time",
            "out_time",
            "working_hours",
            "shift",
            "half_day_status"
        ]
        # 🔒 Attendance Lock Check
        lock_month = check_attendance_lock(start_date)

        if lock_month:
            return {
                "success": False,
                "message": f"Attendance is locked for {lock_month}",
                "data": None
            }
        # ✅ Total records (without limit)
        total_records = frappe.db.count(
            "Attendance",
            filters=month_filters
        )

        # ✅ Attendance records (with optional limit)
        month_attendance_records = frappe.get_list(
            "Attendance",
            filters=month_filters,
            fields=fields,
            order_by="attendance_date asc",
            limit=limit,
            limit_start=limit_start
        )
        for row in month_attendance_records:
            row["working_hours_display"] = decimal_hours_to_hhmm(row.get("working_hours"))
    except Exception as e:
        frappe.log_error("Error While Fetching Attendance", str(e))
        frappe.clear_messages()

        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None,
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Attendance records retrieved successfully.",
            "data": {
                "from_date": start_date,
                "to_date": end_date,
                "total_records": total_records,  # ✅ added
                "records": month_attendance_records or []
            },
        }

def decimal_hours_to_hhmm(hours):
    if not hours:
        return "00:00"

    total_minutes = int(round(float(hours) * 60))

    h = total_minutes // 60
    m = total_minutes % 60

    return f"{h:02d}:{m:02d}"

# @frappe.whitelist()
# def get_attendance_calendar(employeeId, date):
#     try:
#         import calendar
#         from datetime import datetime, date as sys_date

#         # -----------------------------
#         # VALIDATION
#         # -----------------------------
#         if not employeeId or not date:
#             frappe.throw("Employee ID and Date are required")

#         specific_date = datetime.strptime(date, "%Y-%m-%d").date()
#         current_month = specific_date.month
#         current_year = specific_date.year
#         total_days = calendar.monthrange(current_year, current_month)[1]

#         start_date = f"{current_year}-{current_month:02d}-01"
#         end_date = f"{current_year}-{current_month:02d}-{total_days}"

#         # -----------------------------
#         # FETCH ATTENDANCE DATA
#         # -----------------------------
#         attendance_data = frappe.get_all(
#             "Attendance",
#             filters={
#                 "employee": employeeId,
#                 "attendance_date": ["between", [start_date, end_date]]
#             },
#             fields=[
#                 "attendance_date",
#                 "status",
#                 "in_time",
#                 "out_time",
#                 "working_hours",
#                 "leave_type",
#                 "half_day_status",
#                 "shift",
#                 "leave_application"
#             ]
#         )
#         # return attendance_data
#         attendance_map = {
#             str(row.attendance_date): row
#             for row in attendance_data
#         }
#         leave_map = {
#             "Medical Emergency Leave": "MEL",
#             "Special Maternity Leave": "SML",
#             "Maternity Leave": "ML",
#             "Leave Without Pay": "LWP",
#             "Privilege Leave": "PL",
#             "Sick Leave": "SL",
#             "Compensatory Off": "CO",
#             "Casual Leave": "CL",
#         }

#         # -----------------------------
#         # FETCH HOLIDAYS + RH PAIRS
#         # -----------------------------
#         holiday_map = {}
#         restricted_rows = {}

#         employee = frappe.get_doc("Employee", employeeId)

#         if employee.holiday_list:
#             holiday_doc = frappe.get_doc("Holiday List", employee.holiday_list)

#             for h in holiday_doc.holidays:
#                 holiday_date_str = str(h.holiday_date)

#                 holiday_map[holiday_date_str] = {
#                     "weekly_off": h.weekly_off,
#                     "description": h.description,
#                     "is_half_day": h.is_half_day,
#                     "restricted_holiday": getattr(h, "custom_is_restricted_holiday", 0)
#                 }

#                 # Collect RH pairs
#                 if (
#                     getattr(h, "custom_is_restricted_holiday", 0)
#                     and getattr(h, "custom_restricted_holiday_date", None)
#                 ):
#                     restricted_rows[getdate(h.holiday_date)] = getdate(
#                         h.custom_restricted_holiday_date
#                     )

#             # for h in holiday_doc.holidays:
#             #     holiday_map[str(h.holiday_date)] = {
#             #         "weekly_off": h.weekly_off,
#             #         "description": h.description,
#             #         "is_half_day": h.is_half_day,

#             #     }

#         # -----------------------------
#         # CREATE RH PAIR MAP
#         # -----------------------------
#         rh_pair_map = {}
#         visited = set()
#         pair_counter = 1

#         for holiday_date, pair_date in restricted_rows.items():

#             if holiday_date in visited:
#                 continue

#             pair_label = f"RH{pair_counter}"

#             rh_pair_map[str(holiday_date)] = pair_label
#             rh_pair_map[str(pair_date)] = pair_label

#             visited.add(holiday_date)
#             visited.add(pair_date)

#             pair_counter += 1

#         today = sys_date.today()
#         month_data = []

#         for d in range(1, total_days + 1):
#             date_obj = sys_date(current_year, current_month, d)
#             date_str = str(date_obj)

#             day_data = {
#                 "date": date_str,
#                 "status": "",
#                 "in_time": None,
#                 "out_time": None,
#                 "working_hours": 0,
#                 "other_half_status": None,
#                 "shift":None
#             }

#             # -----------------------------
#             # FUTURE DATE → BLANK
#             # -----------------------------
#             # if date_obj > today:
#             #     month_data.append(day_data)
#             #     continue

#             # -----------------------------
#             # HOLIDAY / WEEKLY OFF / RH
#             # -----------------------------

#             if date_str in holiday_map:
#                 holiday = holiday_map[date_str]

#                 if holiday["weekly_off"]:
#                     day_data["status"] = "WO"

#                 elif holiday.get("restricted_holiday"):
#                     rh_label = rh_pair_map.get(date_str)

#                     if rh_label:
#                         day_data["status"] = rh_label
#                     else:
#                         day_data["status"] = "RH"

#                 else:
#                     day_data["status"] = "H"

#             # if date_str in holiday_map:
#             #     holiday = holiday_map[date_str]
#             #     if holiday["weekly_off"]:
#             #         day_data["status"] = "WO"
#             #     else:
#             #         day_data["status"] = "H"

#             # -----------------------------
#             # ATTENDANCE OVERRIDES HOLIDAY
#             # -----------------------------

#             if date_str in attendance_map:
#                 record = attendance_map[date_str]

#                 if record.status == "Present":
#                     day_data["status"] = "P"

#                 elif record.status == "Half Day":
#                     short_code = leave_map.get(record.leave_type) or "HD"
#                     day_data["status"] = short_code
#                     existing = day_data.get("other_half_status")
#                     if existing in ["Present", "Absent"]:
#                         day_data["other_half_status"] = existing
#                     else:
#                         day_data["other_half_status"] = "P"

#                 elif record.status == "On Leave":
#                     short_code = leave_map.get(record.leave_type) or "L"
#                     day_data["status"] = short_code
#                     if short_code =="CO":
#                         day_data["working_date_co"]=frappe.get_value("Leave Application", record.leave_application, "custom_off_day_date")

#                 elif record.status == "Absent":
#                     day_data["status"] = "A"
#                 elif record.status == "Partially":
#                     day_data["status"] = "PR"
#                 raw_hours = record.working_hours or 0
#                 day_data["in_time"] = record.in_time
#                 day_data["out_time"] = record.out_time
#                 day_data["working_hours"] = decimal_hours_to_hhmm(raw_hours) or 0
#                 day_data["shift"]=record.shift

#             elif date_obj <today and not day_data["status"]:
#                 day_data["status"] = "A"

#             month_data.append(day_data)

#         return {
#             "success": True,
#             "month": f"{current_year}-{current_month:02d}",
#             "attendance": month_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Calendar Attendance API Error")
#         return {
#             "success": False,
#             "message": str(e)
#         }







# ------- UPDATED MOBILE API CODE FOR ATTENDANCE CALANDER VIEW START (29-04-2026)-------

# @frappe.whitelist()
# def get_attendance_calendar(employeeId, date):
#     try:
#         import calendar
#         from datetime import datetime, date as sys_date

#         # -----------------------------
#         # VALIDATION
#         # -----------------------------
#         if not employeeId or not date:
#             frappe.throw("Employee ID and Date are required")

#         specific_date = datetime.strptime(date, "%Y-%m-%d").date()
#         current_month = specific_date.month
#         current_year = specific_date.year
#         total_days = calendar.monthrange(current_year, current_month)[1]

#         start_date = f"{current_year}-{current_month:02d}-01"
#         end_date = f"{current_year}-{current_month:02d}-{total_days}"

#         # -----------------------------
#         # FETCH ATTENDANCE DATA
#         # -----------------------------
#         attendance_data = frappe.get_all(
#             "Attendance",
#             filters={
#                 "employee": employeeId,
#                 "attendance_date": ["between", [start_date, end_date]]
#             },
#             fields=[
#                 "attendance_date",
#                 "status",
#                 "in_time",
#                 "out_time",
#                 "working_hours",
#                 "leave_type",
#                 "half_day_status",
#                 "shift",
#                 "leave_application"
#             ]
#         )

#         attendance_map = {
#             str(row.attendance_date): row
#             for row in attendance_data
#         }

#         leave_map = {
#             "Medical Emergency Leave": "MEL",
#             "Special Maternity Leave": "SML",
#             "Maternity Leave": "ML",
#             "Leave Without Pay": "LWP",
#             "Privilege Leave": "PL",
#             "Sick Leave": "SL",
#             "Compensatory Off": "CO",
#             "Casual Leave": "CL",
#         }

#         # -----------------------------
#         # FETCH EMPLOYEE (for fallback holiday list)
#         # -----------------------------
#         employee = frappe.get_doc("Employee", employeeId)
#         default_holiday_list = employee.holiday_list  # fallback

#         # -----------------------------
#         # FETCH ALL HOLIDAY LIST ASSIGNMENTS for this employee
#         # that are active on or before end_date, sorted desc
#         # so we can pick the right one per date
#         # -----------------------------
#         all_assignments = frappe.db.get_all(
#             "Holiday List Assignment",
#             filters={
#                 "assigned_to": employeeId,
#                 "from_date": ["<=", end_date],
#                 "docstatus": 1
#             },
#             fields=["holiday_list", "from_date"],
#             order_by="from_date desc"
#         )

#         # -----------------------------
#         # HELPER: Get holiday list name for a given date
#         # Picks the assignment with the latest from_date <= given_date
#         # Falls back to employee's default holiday list
#         # -----------------------------
#         def get_holiday_list_for_date(check_date):
#             for assignment in all_assignments:
#                 if getdate(assignment.from_date) <= check_date:
#                     return assignment.holiday_list
#             return default_holiday_list

#         # -----------------------------
#         # CACHE: Load holiday list docs to avoid repeated DB calls
#         # -----------------------------
#         holiday_list_cache = {}

#         def get_holiday_map_and_rh(holiday_list_name):
#             """
#             Returns (holiday_map, rh_pair_map) for a given holiday list name.
#             Cached to avoid redundant frappe.get_doc calls.
#             """
#             if holiday_list_name in holiday_list_cache:
#                 return holiday_list_cache[holiday_list_name]

#             holiday_map = {}
#             rh_pair_map = {}

#             if not holiday_list_name:
#                 holiday_list_cache[holiday_list_name] = (holiday_map, rh_pair_map)
#                 return holiday_map, rh_pair_map

#             holiday_doc = frappe.get_doc("Holiday List", holiday_list_name)
#             restricted_rows = {}

#             for h in holiday_doc.holidays:
#                 holiday_date_str = str(h.holiday_date)
#                 holiday_map[holiday_date_str] = {
#                     "weekly_off": h.weekly_off,
#                     "description": h.description,
#                     "is_half_day": h.is_half_day,
#                     "restricted_holiday": getattr(h, "custom_is_restricted_holiday", 0)
#                 }

#                 if (
#                     getattr(h, "custom_is_restricted_holiday", 0)
#                     and getattr(h, "custom_restricted_holiday_date", None)
#                 ):
#                     restricted_rows[getdate(h.holiday_date)] = getdate(
#                         h.custom_restricted_holiday_date
#                     )

#             # Build RH pair map
#             visited = set()
#             pair_counter = 1
#             for holiday_date, pair_date in restricted_rows.items():
#                 if holiday_date in visited:
#                     continue
#                 pair_label = f"RH{pair_counter}"
#                 rh_pair_map[str(holiday_date)] = pair_label
#                 rh_pair_map[str(pair_date)] = pair_label
#                 visited.add(holiday_date)
#                 visited.add(pair_date)
#                 pair_counter += 1

#             holiday_list_cache[holiday_list_name] = (holiday_map, rh_pair_map)
#             return holiday_map, rh_pair_map

#         # -----------------------------
#         # LOOP THROUGH MONTH DAYS
#         # -----------------------------
#         today = sys_date.today()
#         month_data = []

#         for d in range(1, total_days + 1):
#             date_obj = sys_date(current_year, current_month, d)
#             date_str = str(date_obj)

#             day_data = {
#                 "date": date_str,
#                 "status": "",
#                 "in_time": None,
#                 "out_time": None,
#                 "working_hours": 0,
#                 "other_half_status": None,
#                 "shift": None
#             }

#             # -----------------------------
#             # RESOLVE HOLIDAY LIST FOR THIS DATE
#             # Priority: Holiday List Assignment > Employee default
#             # -----------------------------
#             resolved_holiday_list = get_holiday_list_for_date(date_obj)
#             holiday_map, rh_pair_map = get_holiday_map_and_rh(resolved_holiday_list)

#             # -----------------------------
#             # HOLIDAY / WEEKLY OFF / RH
#             # -----------------------------
#             if date_str in holiday_map:
#                 holiday = holiday_map[date_str]

#                 if holiday["weekly_off"]:
#                     day_data["status"] = "WO"

#                 elif holiday.get("restricted_holiday"):
#                     rh_label = rh_pair_map.get(date_str)
#                     day_data["status"] = rh_label if rh_label else "RH"

#                 else:
#                     day_data["status"] = "H"

#             # -----------------------------
#             # ATTENDANCE OVERRIDES HOLIDAY
#             # -----------------------------
#             if date_str in attendance_map:
#                 record = attendance_map[date_str]

#                 if record.status == "Present":
#                     day_data["status"] = "P"

#                 elif record.status == "Half Day":
#                     short_code = leave_map.get(record.leave_type) or "HD"
#                     day_data["status"] = short_code
#                     existing = day_data.get("other_half_status")
#                     if existing in ["Present", "Absent"]:
#                         day_data["other_half_status"] = existing
#                     else:
#                         day_data["other_half_status"] = "P"

#                 elif record.status == "On Leave":
#                     short_code = leave_map.get(record.leave_type) or "L"
#                     day_data["status"] = short_code
#                     if short_code == "CO":
#                         day_data["working_date_co"] = frappe.get_value(
#                             "Leave Application",
#                             record.leave_application,
#                             "custom_off_day_date"
#                         )

#                 elif record.status == "Absent":
#                     day_data["status"] = "A"

#                 elif record.status == "Partially":
#                     day_data["status"] = "PR"

#                 raw_hours = record.working_hours or 0
#                 day_data["in_time"] = record.in_time
#                 day_data["out_time"] = record.out_time
#                 day_data["working_hours"] = decimal_hours_to_hhmm(raw_hours) or 0
#                 day_data["shift"] = record.shift

#             elif date_obj < today and not day_data["status"]:
#                 day_data["status"] = "A"

#             month_data.append(day_data)
#             # 🔒 Attendance Lock Check
#             lock_month = check_attendance_lock(specific_date)

#             if lock_month:
#                 return {
#                     "success": False,
#                     "message": f"Attendance is locked for {lock_month}",
#                     "attendance": []
#                 }
                
#         return {
#             "success": True,
#             "month": f"{current_year}-{current_month:02d}",
#             "attendance": month_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Calendar Attendance API Error")
#         return {
#             "success": False,
#             "message": str(e)
#         }

# new code attendance show for lock month
@frappe.whitelist()
def get_attendance_calendar(employeeId, date):
    try:
        import calendar
        from datetime import datetime, date as sys_date

        # -----------------------------
        # VALIDATION
        # -----------------------------
        if not employeeId or not date:
            frappe.throw("Employee ID and Date are required")

        specific_date = datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date()

        current_month = specific_date.month
        current_year = specific_date.year

        total_days = calendar.monthrange(
            current_year,
            current_month
        )[1]

        start_date = (
            f"{current_year}-{current_month:02d}-01"
        )

        end_date = (
            f"{current_year}-{current_month:02d}-{total_days}"
        )

        # -----------------------------
        # 🔒 ATTENDANCE LOCK CHECK
        # -----------------------------
        lock_month = check_attendance_lock(
            specific_date
        )

        # -----------------------------
        # FETCH ATTENDANCE DATA
        # -----------------------------
        attendance_data = frappe.get_all(
            "Attendance",
            filters={
                "employee": employeeId,
                "attendance_date": [
                    "between",
                    [start_date, end_date]
                ]
            },
            fields=[
                "attendance_date",
                "status",
                "in_time",
                "out_time",
                "working_hours",
                "leave_type",
                "half_day_status",
                "shift",
                "leave_application",
                "custom_remark"
            ]
        )

        attendance_map = {
            str(row.attendance_date): row
            for row in attendance_data
        }
        # -----------------------------
        # FETCH DRAFT LEAVE APPLICATIONS
        # -----------------------------
        draft_leave_applications = frappe.get_all(
            "Leave Application",
            filters={
                "employee": employeeId,
                "docstatus": 0,
                "from_date": ["<=", end_date],
                "to_date": [">=", start_date]
            },
            fields=[
                "from_date",
                "to_date"
            ]
        )

        draft_leave_dates = set()

        for leave in draft_leave_applications:
            current_date = getdate(leave.from_date)

            while current_date <= getdate(leave.to_date):
                draft_leave_dates.add(str(current_date))
                current_date = add_days(current_date, 1)
        
        # -----------------------------
        # LEAVE SHORT CODES
        # -----------------------------
        leave_map = {
            "Medical Emergency Leave": "MEL",
            "Special Maternity Leave": "SML",
            "Maternity Leave": "ML",
            "Leave Without Pay": "LWP",
            "Privilege Leave": "PL",
            "Sick Leave": "SL",
            "Compensatory Off": "CO",
            "Casual Leave": "CL",
            "Leave Not Approved":"LNA"
        }

        # -----------------------------
        # FETCH EMPLOYEE
        # -----------------------------
        employee = frappe.get_doc(
            "Employee",
            employeeId
        )

        default_holiday_list = (
            employee.holiday_list
        )

        # -----------------------------
        # FETCH HOLIDAY ASSIGNMENTS
        # -----------------------------
        all_assignments = frappe.db.get_all(
            "Holiday List Assignment",
            filters={
                "assigned_to": employeeId,
                "from_date": ["<=", end_date],
                "docstatus": 1
            },
            fields=[
                "holiday_list",
                "from_date"
            ],
            order_by="from_date desc"
        )

        # -----------------------------
        # GET HOLIDAY LIST BY DATE
        # -----------------------------
        def get_holiday_list_for_date(
            check_date
        ):

            for assignment in all_assignments:

                if (
                    getdate(
                        assignment.from_date
                    ) <= check_date
                ):

                    return assignment.holiday_list

            return default_holiday_list

        # -----------------------------
        # HOLIDAY CACHE
        # -----------------------------
        holiday_list_cache = {}

        def get_holiday_map_and_rh(
            holiday_list_name
        ):

            if (
                holiday_list_name
                in holiday_list_cache
            ):

                return holiday_list_cache[
                    holiday_list_name
                ]

            holiday_map = {}
            rh_pair_map = {}

            if not holiday_list_name:

                holiday_list_cache[
                    holiday_list_name
                ] = (
                    holiday_map,
                    rh_pair_map
                )

                return (
                    holiday_map,
                    rh_pair_map
                )

            holiday_doc = frappe.get_doc(
                "Holiday List",
                holiday_list_name
            )

            restricted_rows = {}

            for h in holiday_doc.holidays:

                holiday_date_str = str(
                    h.holiday_date
                )

                holiday_map[
                    holiday_date_str
                ] = {
                    "weekly_off": h.weekly_off,
                    "description": h.description,
                    "is_half_day": h.is_half_day,
                    "restricted_holiday": getattr(
                        h,
                        "custom_is_restricted_holiday",
                        0
                    )
                }

                # RH PAIR
                if (
                    getattr(
                        h,
                        "custom_is_restricted_holiday",
                        0
                    )
                    and getattr(
                        h,
                        "custom_restricted_holiday_date",
                        None
                    )
                ):

                    restricted_rows[
                        getdate(h.holiday_date)
                    ] = getdate(
                        h.custom_restricted_holiday_date
                    )

            # -----------------------------
            # BUILD RH PAIR MAP
            # -----------------------------
            visited = set()

            pair_counter = 1

            for (
                holiday_date,
                pair_date
            ) in restricted_rows.items():

                if holiday_date in visited:
                    continue

                pair_label = (
                    f"RH{pair_counter}"
                )

                rh_pair_map[
                    str(holiday_date)
                ] = pair_label

                rh_pair_map[
                    str(pair_date)
                ] = pair_label

                visited.add(holiday_date)
                visited.add(pair_date)

                pair_counter += 1

            holiday_list_cache[
                holiday_list_name
            ] = (
                holiday_map,
                rh_pair_map
            )

            return (
                holiday_map,
                rh_pair_map
            )

        # -----------------------------
        # LOOP THROUGH MONTH
        # -----------------------------
        today = sys_date.today()

        month_data = []

        for d in range(
            1,
            total_days + 1
        ):

            date_obj = sys_date(
                current_year,
                current_month,
                d
            )

            date_str = str(date_obj)

            day_data = {
                "date": date_str,
                "status": "",
                "in_time": None,
                "out_time": None,
                "working_hours": "00:00",
                "other_half_status": None,
                "shift": None,
                "custom_remark": None
            }

            # -----------------------------
            # HOLIDAY LIST RESOLVE
            # -----------------------------
            resolved_holiday_list = (
                get_holiday_list_for_date(
                    date_obj
                )
            )

            holiday_map, rh_pair_map = (
                get_holiday_map_and_rh(
                    resolved_holiday_list
                )
            )

            # -----------------------------
            # HOLIDAY / WEEKLY OFF / RH
            # -----------------------------
            if date_str in holiday_map:

                holiday = holiday_map[
                    date_str
                ]

                # WEEKLY OFF
                if holiday["weekly_off"]:

                    day_data["status"] = "WO"

                # RESTRICTED HOLIDAY
                elif holiday.get(
                    "restricted_holiday"
                ):

                    rh_label = (
                        rh_pair_map.get(
                            date_str
                        )
                    )

                    day_data["status"] = (
                        rh_label
                        if rh_label
                        else "RH"
                    )

                # HOLIDAY
                else:

                    day_data["status"] = "H"

            # -----------------------------
            # ATTENDANCE OVERRIDES
            # -----------------------------

            if date_str in attendance_map:

                record = attendance_map[date_str]

                # PRESENT
                if record.status == "Present":
                    day_data["status"] = "P"

                # HALF DAY
                elif record.status == "Half Day":

                    short_code = (
                        leave_map.get(record.leave_type)
                        or "HD"
                    )

                    day_data["status"] = short_code

                    existing = day_data.get("other_half_status")

                    if existing in ["Present", "Absent"]:
                        day_data["other_half_status"] = existing
                    else:
                        day_data["other_half_status"] = "P"

                # ON LEAVE
                elif record.status == "On Leave":

                    short_code = (
                        leave_map.get(record.leave_type)
                        or "L"
                    )

                    day_data["status"] = short_code

                    if short_code == "CO":
                        day_data["working_date_co"] = frappe.db.get_value(
                            "Leave Application",
                            record.leave_application,
                            "custom_off_day_date"
                        )

                # ABSENT
                elif record.status == "Absent":
                    day_data["status"] = "A"

                # PARTIALLY
                elif record.status == "Partially":
                    day_data["status"] = "PR"

                # WORK FROM HOME
                elif record.status == "Work From Home":
                    day_data["status"] = "WFH"

                # WEEKLY OFF
                elif record.status == "Weekly Off":
                    day_data["status"] = "WO"

                # RESTRICTED HOLIDAY
                elif record.status == "Restricted Holiday":
                    day_data["status"] = "RH"

                # HOLIDAY
                elif record.status == "Holiday":
                    day_data["status"] = "H"

                # SUSPENDED
                elif record.status == "Suspended":
                    day_data["status"] = "S"

                # COMMON VALUES
                raw_hours = record.working_hours or 0

                day_data["in_time"] = record.in_time
                day_data["out_time"] = record.out_time
                day_data["working_hours"] = decimal_hours_to_hhmm(raw_hours)
                day_data["shift"] = record.shift
                day_data["custom_remark"] = record.custom_remark
            # -----------------------------
            # ABSENT FOR PAST DATE
            # -----------------------------
            # elif (
            #     date_obj < today
            #     and not day_data["status"]
            # ):

            #     day_data["status"] = "A"

            # -----------------------------
            # DRAFT LEAVE APPLICATION
            # -----------------------------
            elif (
                date_str in draft_leave_dates
                and not day_data["status"]
            ):
                day_data["status"] = "LNA"

            # -----------------------------
            # NO ATTENDANCE / NO LEAVE
            # -----------------------------
            # Keep the status blank.
            # -----------------------------
            # DEFAULT STATUS
            # -----------------------------
            # if not day_data["status"]:
            #     day_data["status"] = "LNA"

            month_data.append(day_data)
        
        # -----------------------------
        # FINAL RESPONSE
        # -----------------------------
        return {

            "success": True,

            "month": (
                f"{current_year}-{current_month:02d}"
            ),

            # 🔒 LOCK STATUS
            "is_locked": (
                True
                if lock_month
                else False
            ),

            "lock_message": (
                f"Attendance is locked for {lock_month}"
                if lock_month
                else ""
            ),

            # 📅 CALENDAR DATA
            "attendance": month_data
        }

    except Exception as e:

        frappe.log_error(
            frappe.get_traceback(),
            "Calendar Attendance API Error"
        )

        return {
            "success": False,
            "message": str(e)
        }

# ------- UPDATED MOBILE API CODE FOR ATTENDANCE CALANDER VIEW END (29-04-2026)-------





# @frappe.whitelist()
# def get_attendance_calendar(employeeId, date):
#     try:
#         # -----------------------------
#         # VALIDATION
#         # -----------------------------
#         if not employeeId or not date:
#             frappe.throw("Employee ID and Date are required")

#         specific_date = datetime.strptime(date, "%Y-%m-%d").date()
#         current_month = specific_date.month
#         current_year = specific_date.year
#         total_days = calendar.monthrange(current_year, current_month)[1]

#         start_date = f"{current_year}-{current_month:02d}-01"
#         end_date = f"{current_year}-{current_month:02d}-{total_days}"

#         # -----------------------------
#         # FETCH ATTENDANCE DATA
#         # -----------------------------
#         attendance_data = frappe.get_all(
#             "Attendance",
#             filters={
#                 "employee": employeeId,
#                 "attendance_date": ["between", [start_date, end_date]]
#             },
#             fields=[
#                 "attendance_date",
#                 "status",
#                 "in_time",
#                 "out_time",
#                 "working_hours",
#                 "leave_type"
#             ]
#         )

#         attendance_map = {
#             str(row.attendance_date): row
#             for row in attendance_data
#         }

#         # -----------------------------
#         # HOLIDAY LIST
#         # -----------------------------
#         holiday_map = {}
#         employee = frappe.get_doc("Employee", employeeId)

#         if employee.holiday_list:
#             holiday_doc = frappe.get_doc("Holiday List", employee.holiday_list)
#             for h in holiday_doc.holidays:
#                 holiday_map[str(h.holiday_date)] = {
#                     "weekly_off": h.weekly_off,
#                     "description": h.description,
#                     "is_half_day": h.is_half_day
#                 }

#         today = sys_date.today()
#         month_data = []

#         # -----------------------------
#         # LOOP MONTH DAYS
#         # -----------------------------
#         for d in range(1, total_days + 1):
#             date_obj = sys_date(current_year, current_month, d)
#             date_str = str(date_obj)

#             day_data = {
#                 "date": date_str,
#                 "status": "",              # ✅ DEFAULT BLANK
#                 "in_time": None,
#                 "out_time": None,
#                 "working_hours": 0,
#                 "other_half_status": None
#             }

#             # -----------------------------
#             # FUTURE DATE → BLANK
#             # -----------------------------
#             if date_obj > today:
#                 month_data.append(day_data)
#                 continue

#             # -----------------------------
#             # HOLIDAY / WEEKLY OFF
#             # -----------------------------
#             if date_str in holiday_map:
#                 holiday = holiday_map[date_str]
#                 if holiday["weekly_off"]:
#                     day_data["status"] = "WO"
#                 else:
#                     day_data["status"] = "H"

#             # -----------------------------
#             # ATTENDANCE OVERRIDES ALL
#             # -----------------------------
#             if date_str in attendance_map:
#                 record = attendance_map[date_str]

#                 if record.status == "Present":
#                     day_data["status"] = "P"

#                 elif record.status == "Half Day":
#                     day_data["status"] = "HD"
#                     day_data["other_half_status"] = "HD"

#                 elif record.status == "On Leave":
#                     day_data["status"] = "L"

#                 elif record.status == "Absent":
#                     day_data["status"] = "A"

#                 day_data["in_time"] = record.in_time
#                 day_data["out_time"] = record.out_time
#                 day_data["working_hours"] = record.working_hours or 0

#             # -----------------------------
#             # PAST DATE WITHOUT ATTENDANCE
#             # -----------------------------
#             elif date_obj < today and not day_data["status"]:
#                 day_data["status"] = "A"

#             # 👉 TODAY without attendance stays BLANK

#             month_data.append(day_data)

#         # -----------------------------
#         # RESPONSE
#         # -----------------------------
#         return {
#             "success": True,
#             "month": f"{current_year}-{current_month:02d}",
#             "attendance": month_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Calendar Attendance API Error")
#         return {
#             "success": False,
#             "message": str(e)
#         }

            

# @frappe.whitelist()
# def get_attendance_calendar(employeeId, date):
#     try:
#         if not employeeId or not date:
#             frappe.throw("Employee ID and Date are required")

#         # Parse input date
#         specific_date = datetime.strptime(date, "%Y-%m-%d").date()
#         current_month = specific_date.month
#         current_year = specific_date.year
#         total_days = calendar.monthrange(current_year, current_month)[1]

#         # Start and end dates for attendance query
#         start_date = f"{current_year}-{current_month:02d}-01"
#         end_date = f"{current_year}-{current_month:02d}-{total_days}"

#         # Get attendance records for the month
#         attendance_data = frappe.get_all(
#             "Attendance",
#             filters={
#                 "employee": employeeId,
#                 "attendance_date": ["between", [start_date, end_date]]
#             },
#             fields=[
#                 "attendance_date",
#                 "status",
#                 "in_time",
#                 "out_time",
#                 "working_hours"
#             ]
#         )

#         # Map attendance by date
#         attendance_map = {str(row.attendance_date): row for row in attendance_data}

#         # Get employee and holiday list
#         employee = frappe.get_doc("Employee", employeeId)
#         holiday_map = {}
#         if employee.holiday_list:
#             holiday_doc = frappe.get_doc("Holiday List", employee.holiday_list)
#             for h in holiday_doc.holidays:
#                 holiday_map[str(h.holiday_date)] = {
#                     "weekly_off": h.weekly_off,
#                     "description": h.description,
#                     "is_half_day": h.is_half_day
#                 }

#         # Current date to check future days
#         today = sys_date.today()
#         month_data = []

#         # Loop through the whole month
#         for d in range(1, total_days + 1):
#             date_obj = sys_date(current_year, current_month, d)
#             date_str = str(date_obj)

#             # Initialize default day data
#             day_data = {
#                 "date": date_str,
#                 "status": "A",  # Default Absent
#                 "in_time": None,
#                 "out_time": None,
#                 "working_hours": 0
#             }

#             # ✅ Skip future dates
#             if date_obj > today:
#                 day_data["status"] = ""  # Or "N/A" if you prefer
#                 month_data.append(day_data)
#                 continue

#             # ✅ Holiday List overrides default
#             if date_str in holiday_map:
#                 holiday_info = holiday_map[date_str]
#                 if holiday_info["weekly_off"] == 1:
#                     day_data["status"] = "WO"   # Weekly Off
#                 else:
#                     day_data["status"] = "H"    # Holiday

#             # ✅ Attendance overrides everything
#             if date_str in attendance_map:
#                 record = attendance_map[date_str]
#                 if record.status == "Present":
#                     day_data["status"] = "P"
#                 elif record.status == "On Leave":
#                     day_data["status"] = "L"
#                 else:
#                     day_data["status"] = "A"

#                 day_data["in_time"] = record.in_time
#                 day_data["out_time"] = record.out_time
#                 day_data["working_hours"] = record.working_hours

#             month_data.append(day_data)

#         return {
#             "success": True,
#             "month": f"{current_year}-{current_month}",
#             "attendance": month_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Calendar API Error")
#         return {
#             "success": False,
#             "message": str(e)
#         }

@frappe.whitelist(allow_guest=True)
def attendance_status_list():
    """
    Returns a list of predefined attendance statuses and leave types with colors
    """

    # Predefined attendance statuses
    status_list = [
        {"status": "Present", "color": "#28a745", "code": "P"},       # Green
        {"status": "Absent", "color": "#dc3545", "code": "A"},        # Red
        {"status": "Week Off", "color": "#1f2a56", "code": "WO"},     # Dark Blue
        {"status": "Holiday", "color": "#6f7dff", "code": "H"},       # Purple/Blue
        {"status": "Leave Not Approved", "color": "#F88379", "code": "LNA"},  #  Pink
        # {"status": "Leave Approved", "color": "#9e9e9e", "code": "LA"},       # Grey
        {"status": "Half Day", "color": "#ffa500", "code": "HD"}  ,    # Orange
        {"status": "Partially", "color": "#1100ffff", "code": "PR"},      # Brown
        {"status":"Tour","color":"#9e9e9e","code":"P"} # Grey
        
    ]

    # Hardcoded leave types from your Leave Type DocType
    leave_types = [
        {"status": "Medical Emergency Leave", "color": "#17a2b8", "code": "MEL"},      # Teal
        {"status": "Special Maternity Leave", "color": "#6610f2", "code": "SML"},      # Purple
        {"status": "Maternity Leave", "color": "#6f42c1", "code": "ML"},               # Dark Purple
        {"status": "Leave Without Pay", "color": "#343a40", "code": "LWP"},            # Dark Grey
        {"status": "Privilege Leave", "color": "#20c997", "code": "PL"},              # Greenish
        {"status": "Sick Leave", "color": "#fd7e14", "code": "SL"},                    # Orange
        {"status": "Compensatory Off", "color": "#e83e8c", "code": "CO"},              # Pink
        {"status": "Casual Leave", "color": "#0dcaf0", "code": "CL"}                   # Cyan
    ]

    # Combine both lists
    status_list.extend(leave_types)

    return {
        "success": True,
        "data": status_list
    }
