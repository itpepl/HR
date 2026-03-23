# Copyright (c) 2026, SanskarTechnolab and contributors
# For license information, please see license.txt

from calendar import monthrange
from datetime import date
from itertools import groupby

from pypika import Field
from pypika.terms import Criterion

import frappe
from frappe import _
from frappe.query_builder import Case
from frappe.query_builder.functions import Count, Extract, Sum, Abs
from frappe.utils import cint, cstr, formatdate, getdate
from frappe.utils.nestedset import get_descendants_of

from hrms.utils import date_diff, get_date_range

from jkmpcl_hr.py.utils import get_current_holiday_list

Filters = frappe._dict

# holiday_cache = {}


def get_dynamic_holiday_status(employee: str, dt: date) -> str | None:
    """
    Returns:
        "Holiday"
        "Weekly Off"
        None
    """
    holiday_list = get_current_holiday_list(employee, dt)

    if not holiday_list:
        return None

    holiday = frappe.db.get_value(
        "Holiday",
        {
            "parent": holiday_list,
            "holiday_date": dt
        },
        ["weekly_off"],
        as_dict=True
    )

    if not holiday:
        return None

    if holiday.weekly_off:
        return "Weekly Off"

    return "Holiday"

# def get_dynamic_holiday_status(employee: str, dt: date) -> str | None:
# 	key = (employee, dt)

# 	if key in holiday_cache:
# 		return holiday_cache[key]


# 	holiday_list = get_current_holiday_list(employee, dt)
# 	if employee == "20082: Harshiya Gupta":
# 		frappe.log_error(f"{employee}:{holiday_list}", "Holiday List")


# 	if not holiday_list:
# 		holiday_cache[key] = None
# 		return None

# 	holiday = frappe.db.get_value(
# 		"Holiday",
# 		{
# 			"parent": holiday_list,
# 			"holiday_date": dt
# 		},
# 		["weekly_off"],
# 		as_dict=True
# 	)

# 	if not holiday:
# 		holiday_cache[key] = None
# 		return None

# 	status = "Weekly Off" if holiday.weekly_off else "Holiday"
# 	holiday_cache[key] = status
# 	return status


status_map = {
	"Present": "P",
	"Absent": "A",
	"Half Day/Other Half Absent": "HD/A",
	"Half Day/Other Half Present": "HD/P",
	"Partially": "PR",
	# "Work From Home": "WFH",
	# "Half Day": "HD",
	"On Leave": "L",
	"Holiday": "H",
	"Weekly Off": "WO",
	"Restricted Holiday": "RH",
}

day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def execute(filters: Filters | None = None) -> tuple:
	filters = frappe._dict(filters or {})

	if not filters.filter_based_on:
		frappe.throw(_("Please select Filter Based On"))

	if filters.filter_based_on == "Month" and not (filters.month and filters.year):
		frappe.throw(_("Please select month and year."))

	if filters.filter_based_on == "Date Range":
		if not (filters.start_date and filters.end_date):
			frappe.throw(_("Please set the date range."))
		if getdate(filters.start_date) > getdate(filters.end_date):
			frappe.throw(_("Start date cannot be greater than end date."))
		if date_diff(filters.end_date, filters.start_date) > 90:
			frappe.throw(_("Please set a date range less than 90 days."))

	if not filters.company:
		frappe.throw(_("Please select company."))

	if filters.company:
		filters.companies = [filters.company]
		if filters.include_company_descendants:
			filters.companies.extend(get_descendants_of("Company", filters.company))

	attendance_map = get_attendance_map(filters)
	if not attendance_map:
		frappe.msgprint(_("No attendance records found."), alert=True, indicator="orange")
		return [], [], None, None

	columns = get_columns(filters)
	data = get_data(filters, attendance_map)

	if not data:
		frappe.msgprint(_("No attendance records found for this criteria."), alert=True, indicator="orange")
		return columns, [], None, None

	message = get_message() if not filters.summarized_view else ""
	chart = get_chart_data(attendance_map, filters)

	return columns, data, message, chart


def get_message() -> str:
	message = ""
	colors = [
    "green",
    "red",
    "orange",
    "#914EE3",
    "#3187D8",
    "#3187D8",
    "#878787",
    "#878787",
    "#FF8800",  # NEW
]

	count = 0
	for status, abbr in status_map.items():
		# if not status == "Half Day":
			message += f"""
				<span style='border-left: 2px solid {colors[count]}; padding-right: 12px; padding-left: 5px; margin-right: 3px;'>
					{_(status)} - {abbr}
				</span>
			"""
			count += 1

	return message


def get_columns(filters: Filters) -> list[dict]:
	columns = []

	if filters.group_by:
		options_mapping = {
			"Branch": "Branch",
			"Grade": "Employee Grade",
			"Department": "Department",
			"Designation": "Designation",
		}
		options = options_mapping.get(filters.group_by)
		columns.append(
			{
				"label": _(filters.group_by),
				"fieldname": frappe.scrub(filters.group_by),
				"fieldtype": "Link",
				"options": options,
				"width": 120,
			}
		)

	columns.extend(
		[
			{
				"label": _("Employee"),
				"fieldname": "employee",
				"fieldtype": "Link",
				"options": "Employee",
				"width": 135,
			},
			{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 120},
		]
	)

	if filters.summarized_view:
		columns.extend(
			[
				{
					"label": _("Total Present"),
					"fieldname": "total_present",
					"fieldtype": "Float",
					"width": 110,
				},
				{"label": _("Total Leaves"), "fieldname": "total_leaves", "fieldtype": "Float", "width": 110},
				{"label": _("Total Absent"), "fieldname": "total_absent", "fieldtype": "Float", "width": 110},
				{
					"label": _("Total Holidays"),
					"fieldname": "total_holidays",
					"fieldtype": "Float",
					"width": 120,
				},
				{
					"label": _("Unmarked Days"),
					"fieldname": "unmarked_days",
					"fieldtype": "Float",
					"width": 130,
				},
			]
		)
		columns.extend(get_columns_for_leave_types())
		columns.extend(get_penalty_columns())
		columns.extend(
			[
				{
					"label": _("Total Late Entries"),
					"fieldname": "total_late_entries",
					"fieldtype": "Float",
					"width": 140,
				},
				{
					"label": _("Total Early Exits"),
					"fieldname": "total_early_exits",
					"fieldtype": "Float",
					"width": 140,
				},
			]
		)
	else:
		# columns.append({"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 120})
		# columns.extend(get_columns_for_days(filters))
  
		columns.extend(get_columns_for_days(filters))  # date columns first
		columns.extend(get_additional_summary_columns())  # then your new columns

	return columns


def get_columns_for_leave_types() -> list[dict]:
	leave_types = frappe.db.get_all("Leave Type", pluck="name")
	types = []
	for entry in leave_types:
		types.append({"label": entry, "fieldname": frappe.scrub(entry), "fieldtype": "Float", "width": 120})

	return types


def get_penalty_columns():
	return [
		{
			"label": "Casual Leave Penalty",
			"fieldname": "casual_leave_penalty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": "Sick Leave Penalty",
			"fieldname": "sick_leave_penalty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": "Privilege Leave Penalty",
			"fieldname": "privilege_leave_penalty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": "Leave Without Pay Penalty",
			"fieldname": "leave_without_pay_penalty",
			"fieldtype": "Float",
			"width": 120
		},
	]


def get_columns_for_days(filters: Filters) -> list[dict]:
	days = []
	dates_in_period = get_dates_in_period(filters)
	for d in dates_in_period:
		d = getdate(d)
		# gets abbr from weekday number
		abbr_weekday = day_abbr[d.weekday()]
		# sets days as 1 Mon, 2 Tue, 3 Wed
		label = f"{d.day} {abbr_weekday}"
		days.append({"label": label, "fieldtype": "Data", "fieldname": d.strftime("%d-%m-%Y"), "width": 65})

	return days


def get_dates_in_period(filters: Filters) -> list[str]:
	dates_in_period = []
	if filters.filter_based_on == "Month":
		total_days = get_total_days_in_month(filters)
		# forms the datelist from selected year and month from filters
		dates_in_period = [
			f"{cstr(filters.year)}-{cstr(filters.month)}-{cstr(day)}" for day in range(1, total_days + 1)
		]
	if filters.filter_based_on == "Date Range":
		dates_in_period = get_date_range(filters.start_date, filters.end_date)

	return dates_in_period


def get_total_days_in_month(filters: Filters) -> int:
	return monthrange(cint(filters.year), cint(filters.month))[1]


def get_date_condition(docfield: Field, filters: Filters) -> Criterion:
	if filters.filter_based_on == "Month":
		return (Extract("month", docfield) == filters.month) & (Extract("year", docfield) == filters.year)
	if filters.filter_based_on == "Date Range":
		return (docfield >= filters.start_date) & (docfield <= filters.end_date)


def get_data(filters: Filters, attendance_map: dict) -> list[dict]:
	employee_details, group_by_param_values = get_employee_related_details(filters)
	holiday_map = get_holiday_map(filters)
	data = []

	if filters.group_by:
		group_by_column = frappe.scrub(filters.group_by)

		for value in group_by_param_values:
			if not value:
				continue

			records = get_rows(employee_details[value], filters, holiday_map, attendance_map)

			if records:
				data.append({group_by_column: value})
				data.extend(records)

	else:
		data = get_rows(employee_details, filters, holiday_map, attendance_map)

	return data


# def get_attendance_map(filters: Filters) -> dict:
# 	"""Returns a dictionary of employee wise attendance map as per shifts for all the days of the month like
# 	{
# 	    'employee1': {
# 	            'Morning Shift': {1: 'Present', 2: 'Absent', ...}
# 	            'Evening Shift': {1: 'Absent', 2: 'Present', ...}
# 	    },
# 	    'employee2': {
# 	            'Afternoon Shift': {1: 'Present', 2: 'Absent', ...}
# 	            'Night Shift': {1: 'Absent', 2: 'Absent', ...}
# 	    },
# 	    'employee3': {
# 	            None: {1: 'On Leave'}
# 	    }
# 	}
# 	"""
# 	attendance_list = get_attendance_records(filters)
# 	attendance_map = {}
# 	leave_map = {}

# 	for d in attendance_list:
# 		if d.status == "On Leave":
# 			leave_map.setdefault(d.employee, {}).setdefault(d.shift, []).append(d.attendance_date)
# 			continue

# 		if d.shift is None:
# 			d.shift = ""

# 		# attendance_map.setdefault(d.employee, {}).setdefault(d.shift, {})
# 		# attendance_map[d.employee][d.shift][d.attendance_date] = d.status

# 		attendance_map.setdefault(d.employee, {}).setdefault(d.shift, {})
# 		attendance_map[d.employee][d.shift][d.attendance_date] = {
# 			"status": d.status,
# 			"leave_type": d.leave_type
# 		}

def get_attendance_map(filters: Filters) -> dict:
	"""
	Returns a dictionary of employee-wise attendance map per shift and date.
	Each date entry ALWAYS stores a dict:
	{
		"status": "Present" / "On Leave" / "Half Day/Other Half Present" ...
		"leave_type": "Casual Leave" / None
	}
	"""

	attendance_list = get_attendance_records(filters)
	attendance_map = {}

	for d in attendance_list:
		# normalize shift
		shift = d.shift or ""

		attendance_map.setdefault(d.employee, {}).setdefault(shift, {})

		attendance_map[d.employee][shift][d.attendance_date] = {
			"status": d.status,
			"leave_type": d.leave_type,
			"is_penalize": d.custom_is_penalize,
    	"penalty_leave_type": d.custom_penalty_leave_type,
			"penalty_leave_count": d.custom_penalty_leave_count,
		}

	return attendance_map


	# leave is applicable for the entire day so all shifts should show the leave entry

	# for employee, leave_days in leave_map.items():
	# 	for assigned_shift, dates in leave_days.items():
	# 		# no attendance records exist except leaves
	# 		if employee not in attendance_map:
	# 			attendance_map.setdefault(employee, {}).setdefault(assigned_shift, {})

	# 		for d in dates:
	# 			for shift in attendance_map[employee].keys():
	# 				attendance_map[employee][shift][d] = "On Leave"

	for employee, leave_days in leave_map.items():
		for assigned_shift, dates in leave_days.items():
			if employee not in attendance_map:
				attendance_map.setdefault(employee, {}).setdefault(assigned_shift, {})

			for d in dates:
				for shift in attendance_map[employee].keys():
					attendance_map[employee][shift][d] = {
						"status": "On Leave",
						"leave_type": None
					}

	return attendance_map


def get_attendance_records(filters: Filters) -> list[dict]:
	Attendance = frappe.qb.DocType("Attendance")
	attendance_date_condition = get_date_condition(Attendance.attendance_date, filters)
	status = (
		frappe.qb.terms.Case()
		.when(
			((Attendance.status == "Half Day") & (Attendance.half_day_status == "Present")),
			"Half Day/Other Half Present",
		)
		.when(
			((Attendance.status == "Half Day") & (Attendance.half_day_status == "Absent")),
			"Half Day/Other Half Absent",
		)
		.else_(Attendance.status)
	)
	query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.employee,
			Attendance.attendance_date,
			(status).as_("status"),
			Attendance.shift,
			Attendance.leave_type,
			Attendance.custom_is_penalize,
    	Attendance.custom_penalty_leave_type,
			Attendance.custom_penalty_leave_count,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.company.isin(filters.companies))
			& (attendance_date_condition)
		)
	)

	if filters.employee:
		query = query.where(Attendance.employee == filters.employee)
	query = query.orderby(Attendance.employee, Attendance.attendance_date)

	return query.run(as_dict=1)


def get_current_user_branch():
	user = frappe.session.user

	# Skip Administrator / Guest
	if user in ("Administrator", "Guest"):
		return None

	employee = frappe.db.get_value(
		"Employee",
		{"user_id": user},
		["name", "branch"],
		as_dict=True
	)

	return employee.branch if employee else None




def get_employee_related_details(filters: Filters) -> tuple[dict, list]:
	"""Returns
	1. nested dict for employee details
	2. list of values for the group by filter
	"""
	Employee = frappe.qb.DocType("Employee")

	user_branch = get_current_user_branch()
	
	joining_date_condition = get_date_condition(Employee.date_of_joining, filters)

	query = (
		frappe.qb.from_(Employee)
		.select(
			Employee.name,
			Employee.employee_name,
			Employee.designation,
			Employee.grade,
			Employee.department,
			Employee.branch,
			Employee.company,
			Employee.holiday_list,
			(Employee.date_of_joining).as_("joined_date"),
			Case()
			.when(
				joining_date_condition,
				1,
			)
			.else_(0)
			.as_("joined_in_current_period"),
		)
		.where(Employee.company.isin(filters.companies))
	)

	if user_branch:
		query = query.where(Employee.branch == user_branch)
	if filters.employee:
		query = query.where(Employee.name == filters.employee)

	group_by = filters.group_by
	if group_by:
		group_by = group_by.lower()
		query = query.orderby(group_by)

	employee_details = query.run(as_dict=True)

	group_by_param_values = []
	emp_map = {}

	if group_by:
		group_key = lambda d: "" if d[group_by] is None else d[group_by]  # noqa
		for parameter, employees in groupby(sorted(employee_details, key=group_key), key=group_key):
			group_by_param_values.append(parameter)
			emp_map.setdefault(parameter, frappe._dict())

			for emp in employees:
				emp_map[parameter][emp.name] = emp
	else:
		for emp in employee_details:
			emp_map[emp.name] = emp

	return emp_map, group_by_param_values


def get_holiday_map(filters: Filters) -> dict[str, list[dict]]:
	"""
	Returns a dict of holidays falling in the filter month and year
	with list name as key and list of holidays as values like
	{
	        'Holiday List 1': [
	                {'day_of_month': '0' , 'weekly_off': 1},
	                {'day_of_month': '1', 'weekly_off': 0}
	        ],
	        'Holiday List 2': [
	                {'day_of_month': '0' , 'weekly_off': 1},
	                {'day_of_month': '1', 'weekly_off': 0}
	        ]
	}
	"""
	# add default holiday list too
	holiday_lists = frappe.db.get_all("Holiday List", pluck="name")
	default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")
	holiday_lists.append(default_holiday_list)

	holiday_map = frappe._dict()
	Holiday = frappe.qb.DocType("Holiday")

	holiday_condition = get_date_condition(Holiday.holiday_date, filters)

	for d in holiday_lists:
		if not d:
			continue

		holidays = (
			frappe.qb.from_(Holiday)
			.select(Holiday.holiday_date, Holiday.weekly_off)
			.where((Holiday.parent == d) & (holiday_condition))
		).run(as_dict=True)
		holiday_map.setdefault(d, holidays)

	return holiday_map


# def get_rows(employee_details: dict, filters: Filters, holiday_map: dict, attendance_map: dict) -> list[dict]:
# 	records = []
# 	default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")

# 	for employee, details in employee_details.items():
# 		emp_holiday_list = details.holiday_list or default_holiday_list
# 		holidays = holiday_map.get(emp_holiday_list)

# 		if filters.summarized_view:
# 			attendance = get_attendance_status_for_summarized_view(
# 				employee, filters, holidays, details.joined_in_current_period, details.joined_date
# 			)
# 			if not attendance:
# 				continue

# 			leave_summary = get_leave_summary(employee, filters)
# 			penalty_leave_summary = get_penalty_leave_summary(employee, filters)
# 			entry_exits_summary = get_entry_exits_summary(employee, filters)

# 			row = {"employee": employee, "employee_name": details.employee_name}
# 			set_defaults_for_summarized_view(filters, row)
# 			row.update(attendance)
# 			row.update(leave_summary)
# 			row.update(penalty_leave_summary)
# 			row.update(entry_exits_summary)

# 			records.append(row)
# 		else:
# 			employee_attendance = attendance_map.get(employee)
# 			if not employee_attendance:
# 				continue

# 			# attendance_for_employee = get_attendance_status_for_detailed_view(
# 			# 	employee, filters, employee_attendance, holidays
# 			# )
# 			# # set employee details in the first row
# 			# for record in attendance_for_employee:
# 			# 	record.update({"employee": employee, "employee_name": details.employee_name})

# 			# records.extend(attendance_for_employee)
   
# 			rh_map = get_employee_restricted_holiday_map(employee, filters)

# 			attendance_row = get_attendance_status_for_detailed_view(
# 				employee,
# 				filters,
# 				employee_attendance,
# 				holidays,
# 				rh_map
# 			)

# 			attendance_row.update({
# 				"employee": employee,
# 				"employee_name": details.employee_name
# 			})

# 			records.append(attendance_row)

# 	return records

def get_rows(employee_details: dict, filters: Filters, holiday_map: dict, attendance_map: dict) -> list[dict]:
    records = []
    default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")

    for employee, details in employee_details.items():
        emp_holiday_list = details.holiday_list or default_holiday_list
        holidays = holiday_map.get(emp_holiday_list)

        if filters.summarized_view:
            attendance = get_attendance_status_for_summarized_view(
                employee, filters, holidays, details.joined_in_current_period, details.joined_date
            )
            if not attendance:
                continue

            leave_summary = get_leave_summary(employee, filters)
            penalty_leave_summary = get_penalty_leave_summary(employee, filters)
            entry_exits_summary = get_entry_exits_summary(employee, filters)

            row = {"employee": employee, "employee_name": details.employee_name}
            set_defaults_for_summarized_view(filters, row)
            row.update(attendance)
            row.update(leave_summary)
            row.update(penalty_leave_summary)
            row.update(entry_exits_summary)

            records.append(row)

        else:
            employee_attendance = attendance_map.get(employee)
            if not employee_attendance:
                continue

            # ✅ RH MAP (employee-wise)
            rh_map = get_employee_restricted_holiday_map(employee, filters)

            # ✅ Daily attendance row
            attendance_row = get_attendance_status_for_detailed_view(
                employee,
                filters,
                employee_attendance,
                holidays,
                rh_map
            )

            rejected_leave_days = get_rejected_leave_days(employee, filters)

            # ✅ ADD NEW METRICS (IMPORTANT)
            metrics = calculate_attendance_metrics(
                employee,
                filters,
                employee_attendance,
                rh_map,
								rejected_leave_days
            )

            # ✅ Merge everything
            attendance_row.update({
                "employee": employee,
                "employee_name": details.employee_name
            })

            attendance_row.update(metrics)

            records.append(attendance_row)

    return records


def set_defaults_for_summarized_view(filters, row):
	for entry in get_columns(filters):
		if entry.get("fieldtype") == "Float":
			row[entry.get("fieldname")] = 0.0


def get_attendance_status_for_summarized_view(
	employee: str, filters: Filters, holidays: list, joined_in_current_period: int, joined_date: int
) -> dict:
	"""Returns dict of attendance status for employee like
	{'total_present': 1.5, 'total_leaves': 0.5, 'total_absent': 13.5, 'total_holidays': 8, 'unmarked_days': 5}
	"""
	summary, attendance_days = get_attendance_summary_and_days(employee, filters)
	if not any(summary.values()):
		return {}

	total_days = get_dates_in_period(filters)
	total_holidays = total_unmarked_days = 0

	for d in total_days:
		d = getdate(d)
		if d in attendance_days or (joined_in_current_period and d < joined_date):
			continue

		# status = get_holiday_status(d, holidays)
		# if status in ["Weekly Off", "Holiday"]:
		# 	total_holidays += 1
		# elif not status:
		# 	total_unmarked_days += 1

		holiday_status = get_dynamic_holiday_status(employee, d)

		if holiday_status in ["Weekly Off", "Holiday"]:
			total_holidays += 1
		elif not holiday_status:
			total_unmarked_days += 1

	return {
		"total_present": summary.total_present + summary.total_half_days,
		"total_leaves": summary.total_leaves + summary.total_half_days,
		"total_absent": summary.total_absent,
		"total_holidays": total_holidays,
		"unmarked_days": total_unmarked_days,
	}


def get_attendance_summary_and_days(employee: str, filters: Filters) -> tuple[dict, list]:
	Attendance = frappe.qb.DocType("Attendance")

	present_case = (
		frappe.qb.terms.Case()
		.when(((Attendance.status == "Present") | (Attendance.status == "Work From Home")), 1)
		.else_(0)
	)
	sum_present = Sum(present_case).as_("total_present")

	absent_case = frappe.qb.terms.Case().when(Attendance.status == "Absent", 1).else_(0)
	sum_absent = Sum(absent_case).as_("total_absent")

	leave_case = frappe.qb.terms.Case().when(Attendance.status == "On Leave", 1).else_(0)
	sum_leave = Sum(leave_case).as_("total_leaves")

	half_day_case = frappe.qb.terms.Case().when(Attendance.status == "Half Day", 0.5).else_(0)
	sum_half_day = Sum(half_day_case).as_("total_half_days")

	attendance_date_condition = get_date_condition(Attendance.attendance_date, filters)

	summary = (
		frappe.qb.from_(Attendance)
		.select(
			sum_present,
			sum_absent,
			sum_leave,
			sum_half_day,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.employee == employee)
			& (Attendance.company.isin(filters.companies))
			& (attendance_date_condition)
		)
	).run(as_dict=True)

	days = (
		frappe.qb.from_(Attendance)
		.select(Extract("day", Attendance.attendance_date).as_("day_of_month"))
		.distinct()
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.employee == employee)
			& (Attendance.company.isin(filters.companies))
			& (attendance_date_condition)
		)
	).run(pluck=True)

	return summary[0], days


def get_attendance_status_for_detailed_view(
    employee: str, filters: Filters, employee_attendance: dict, holidays: list, rh_map: dict
) -> dict:
	# total_days = get_dates_in_period(filters)
	# row = {}

	# for d in total_days:
	# 	dt = getdate(d)
	# 	entries = []

	# 	for shift, status_dict in employee_attendance.items():
	# 		if dt in status_dict:
	# 			entries.append(status_dict[dt])

	# 	status = merge_shift_attendance_for_day(entries)

	# 	# if status is None and holidays:
	# 	# 	status = get_holiday_status(dt, holidays)
	# 	if status is None:
	# 		status = get_dynamic_holiday_status(employee, dt)

	# 	row[dt.strftime("%d-%m-%Y")] = status_map.get(status, status or "")

	# return row
 
	total_days = get_dates_in_period(filters)
	row = {}

	for d in total_days:
		dt = getdate(d)
		key = dt.strftime("%d-%m-%Y")
		entries = []

		for shift, status_dict in employee_attendance.items():
			if dt in status_dict:
				entries.append(status_dict[dt])

		# Step 1 → Merge attendance
		status = merge_shift_attendance_for_day(entries)

		# ✅ Priority 1 → Attendance (SOURCE OF TRUTH)
		if status:
			row[key] = status_map.get(status, status)
			continue

		# ✅ Priority 2 → Restricted Holiday Pairing
		# Only show RH label if attendance record exists with status "Restricted Holiday"
		# Do NOT show for future dates or dates with no attendance record
		if dt in rh_map:
			rh_attendance_exists = frappe.db.exists(
				"Attendance",
				{
					"employee": employee,
					"attendance_date": dt,
					"status": "Restricted Holiday",
					"docstatus": 1,
				}
			)
			if rh_attendance_exists:
				row[key] = rh_map[dt]
				continue

		# ✅ Priority 3 → Empty
		row[key] = ""

	return row

# def get_attendance_status_for_detailed_view(
# 	employee: str, filters: Filters, employee_attendance: dict, holidays: list
# ) -> dict:
# 	total_days = get_dates_in_period(filters)
# 	row = {}

# 	for d in total_days:
# 		dt = getdate(d)
# 		entries = []

# 		for shift, status_dict in employee_attendance.items():
# 			if dt in status_dict:
# 				entries.append(status_dict[dt])

# 		# ✅ FIRST: check holiday
# 		holiday_status = get_holiday_status(dt, holidays) if holidays else None

# 		# ✅ SECOND: merge attendance
# 		status = merge_shift_attendance_for_day(entries)

# 		# ✅ FINAL DECISION
# 		if status:
# 			# already colored HTML or value
# 			row[dt.strftime("%d-%m-%Y")] = status

# 		elif holiday_status == "Holiday":
# 			row[dt.strftime("%d-%m-%Y")] = "H"

# 		elif holiday_status == "Weekly Off":
# 			row[dt.strftime("%d-%m-%Y")] = "WO"

# 		else:
# 			row[dt.strftime("%d-%m-%Y")] = ""

# 	return row




def get_holiday_status(holiday_date: date, holidays: list) -> str:
	status = None
	if holidays:
		for holiday in holidays:
			if holiday_date == holiday.get("holiday_date"):
				if holiday.get("weekly_off"):
					status = "Weekly Off"
				else:
					status = "Holiday"
				break
	return status


def get_leave_summary(employee: str, filters: Filters) -> dict[str, float]:
	"""Returns a dict of leave type and corresponding leaves taken by employee like:
	{'leave_without_pay': 1.0, 'sick_leave': 2.0}
	"""
	Attendance = frappe.qb.DocType("Attendance")
	day_case = frappe.qb.terms.Case().when(Attendance.status == "Half Day", 0.5).else_(1)
	sum_leave_days = Sum(day_case).as_("leave_days")

	attendance_date_condition = get_date_condition(Attendance.attendance_date, filters)

	leave_details = (
		frappe.qb.from_(Attendance)
		.select(Attendance.leave_type, sum_leave_days)
		.where(
			(Attendance.employee == employee)
			& (Attendance.docstatus == 1)
			& (Attendance.company.isin(filters.companies))
			& ((Attendance.leave_type.isnotnull()) | (Attendance.leave_type != ""))
			& (attendance_date_condition)
		)
		.groupby(Attendance.leave_type)
	).run(as_dict=True)

	leaves = {}
	for d in leave_details:
		leave_type = frappe.scrub(d.leave_type)
		leaves[leave_type] = d.leave_days

	return leaves


def get_penalty_leave_summary(employee: str, filters: Filters) -> dict:

    Attendance = frappe.qb.DocType("Attendance")

    attendance_date_condition = get_date_condition(
        Attendance.attendance_date, filters
    )

    penalty_leaves = (
        frappe.qb.from_(Attendance)
        .select(Attendance.custom_penalty_leave_type, Sum(Abs(Attendance.custom_penalty_leave_count)).as_("leave_days"))
        .where(
            (Attendance.employee == employee)
            & (Attendance.docstatus == 1)
            & (Attendance.custom_penalty_leave_type.isnotnull())
            & (Attendance.company.isin(filters.companies))
            & (attendance_date_condition)
        )
        .groupby(Attendance.custom_penalty_leave_type)
    ).run(as_dict=True)

    leaves = {}

    for d in penalty_leaves:
        leave_type = frappe.scrub(d.custom_penalty_leave_type)
        leaves[f"{leave_type}_penalty"] = d.leave_days

    return leaves


def get_entry_exits_summary(employee: str, filters: Filters) -> dict[str, float]:
	"""Returns total late entries and total early exits for employee like:
	{'total_late_entries': 5, 'total_early_exits': 2}
	"""
	Attendance = frappe.qb.DocType("Attendance")

	late_entry_case = frappe.qb.terms.Case().when(Attendance.late_entry == "1", "1")
	count_late_entries = Count(late_entry_case).as_("total_late_entries")

	early_exit_case = frappe.qb.terms.Case().when(Attendance.early_exit == "1", "1")
	count_early_exits = Count(early_exit_case).as_("total_early_exits")

	attendance_date_condition = get_date_condition(Attendance.attendance_date, filters)

	entry_exits = (
		frappe.qb.from_(Attendance)
		.select(count_late_entries, count_early_exits)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.employee == employee)
			& (Attendance.company.isin(filters.companies))
			& (attendance_date_condition)
		)
	).run(as_dict=True)

	return entry_exits[0]


@frappe.whitelist()
def get_attendance_years() -> str:
	"""Returns all the years for which attendance records exist"""
	Attendance = frappe.qb.DocType("Attendance")
	year_list = (
		frappe.qb.from_(Attendance).select(Extract("year", Attendance.attendance_date).as_("year")).distinct()
	).run(as_dict=True)

	if year_list:
		year_list.sort(key=lambda d: d.year, reverse=True)
	else:
		year_list = [frappe._dict({"year": getdate().year})]

	return "\n".join(cstr(entry.year) for entry in year_list)


def get_chart_data(attendance_map: dict, filters: Filters) -> dict:
	days = get_columns_for_days(filters)
	labels = []
	absent = []
	present = []
	leave = []

	for day in days:
		labels.append(day["label"])
		total_absent_on_day = total_leaves_on_day = total_present_on_day = 0

		for __, attendance_dict in attendance_map.items():
			for __, attendance in attendance_dict.items():
				attendance_on_day = attendance.get(getdate(day["fieldname"], parse_day_first=True))

				if attendance_on_day == "On Leave":
					# leave should be counted only once for the entire day
					total_leaves_on_day += 1
					break
				elif attendance_on_day == "Absent":
					total_absent_on_day += 1
				elif attendance_on_day in ["Present", "Work From Home"]:
					total_present_on_day += 1
				elif attendance_on_day == "Half Day":
					total_present_on_day += 0.5
					total_leaves_on_day += 0.5

		absent.append(total_absent_on_day)
		present.append(total_present_on_day)
		leave.append(total_leaves_on_day)

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Absent"), "values": absent},
				{"name": _("Present"), "values": present},
				{"name": _("Leave"), "values": leave},
			],
		},
		"type": "line",
		"colors": ["red", "green", "blue"],
	}

# def merge_shift_attendance_for_day(statuses: list[str]) -> str | None:
# 	if not statuses:
# 		return None

# 	# Highest priority
# 	if any(s in ("Present", "Work From Home") for s in statuses):
# 		return "Present"

# 	# Preserve HD/P explicitly
# 	if any(s == "Half Day/Other Half Present" for s in statuses):
# 		return "Half Day/Other Half Present"

# 	# Preserve HD/A explicitly
# 	if any(s == "Half Day/Other Half Absent" for s in statuses):
# 		return "Half Day/Other Half Absent"

# 	# Generic Half Day
# 	if any(s == "Half Day" for s in statuses):
# 		return "Half Day"

# 	if any(s == "On Leave" for s in statuses):
# 		return "On Leave"

# 	if any(s == "Absent" for s in statuses):
# 		return "Absent"

# 	return None
def merge_shift_attendance_for_day(entries: list[dict]) -> str | None:
	if not entries:
		return None

	statuses = [e["status"] for e in entries]
	leave_types = [e.get("leave_type") for e in entries if e.get("leave_type")]

	is_penalize = any(e.get("is_penalize") for e in entries)
	penalty_leave_types = [e.get("penalty_leave_type") for e in entries if e.get("penalty_leave_type")]
	
	leave_abbr = get_leave_type_abbr(leave_types[0]) if leave_types else None
	penalty_leave_abbr = get_leave_type_abbr(penalty_leave_types[0]) if penalty_leave_types else None

	# Present overrides everything
	if any(s in ("Present") for s in statuses):
		return "Present"
	
	# Penalized Half Day → P/HD-LeaveType
	if is_penalize and penalty_leave_abbr:
		if any(s in ("Half Day", "Half Day/Other Half Present", "Half Day/Other Half Absent") for s in statuses):
			return (
				f"<span style='color:green'>P</span>"
				f"<span style='color:#E5533D'>/HD-{penalty_leave_abbr}</span>"
			)

	# Half Day + Leave Type
	if leave_abbr:
		if "Half Day/Other Half Present" in statuses:
			return f"<span style='color:#914EE3'>{leave_abbr}/P</span>"

		if "Half Day/Other Half Absent" in statuses:
			return f"<span style='color:orange'>{leave_abbr}/A</span>"

		if "On Leave" in statuses:
			return f"<span style='color:#3187D8'>{leave_abbr}</span>"

	# Half Day without Leave Type
	if "Half Day/Other Half Present" in statuses:
		return "Half Day/Other Half Present"

	if "Half Day/Other Half Absent" in statuses:
		return "Half Day/Other Half Absent"

	if "Half Day" in statuses:
		return "<span style='color:orange'>HD</span>"

	if "Partially" in statuses:
			return f"<span style='color:#3187D8'>PR</span>"

	if "On Leave" in statuses:
		return "On Leave"

	if "Absent" in statuses:
		return "Absent"

	if "Holiday" in statuses:
		return "H"

	if "Weekly Off" in statuses:
		return "WO"

	return None



def get_leave_type_abbr(leave_type: str) -> str:
	if not leave_type:
		return ""
	words = leave_type.split()
	return "".join(word[0] for word in words).upper()




















# import frappe
# from frappe import _


# def execute(filters: dict | None = None):
# 	"""Return columns and data for the report.

# 	This is the main entry point for the report. It accepts the filters as a
# 	dictionary and should return columns and data. It is called by the framework
# 	every time the report is refreshed or a filter is updated.
# 	"""
# 	columns = get_columns()
# 	data = get_data()

# 	return columns, data


# def get_columns() -> list[dict]:
# 	"""Return columns for the report.

# 	One field definition per column, just like a DocType field definition.
# 	"""
# 	return [
# 		{
# 			"label": _("Column 1"),
# 			"fieldname": "column_1",
# 			"fieldtype": "Data",
# 		},
# 		{
# 			"label": _("Column 2"),
# 			"fieldname": "column_2",
# 			"fieldtype": "Int",
# 		},
# 	]


# def get_data() -> list[list]:
# 	"""Return data for the report.

# 	The report data is a list of rows, with each row being a list of cell values.
# 	"""
# 	return [
# 		["Row 1", 1],
# 		["Row 2", 2],
# 	]

def get_employee_restricted_holiday_map(employee, filters):
    """
    Returns RH mapping per employee based on their holiday list assignment
    Example:
    {
        date1: "RH1",
        paired_date1: "RH1",
        date2: "RH2",
        paired_date2: "RH2",
    }
    """

    dates = get_dates_in_period(filters)
    rh_map = {}
    counter = 1
    processed_pairs = set()

    for d in dates:
        dt = getdate(d)

        holiday_list = get_current_holiday_list(employee, dt)
        if not holiday_list:
            continue

        holiday = frappe.db.get_value(
            "Holiday",
            {
                "parent": holiday_list,
                "holiday_date": dt,
                "custom_is_restricted_holiday": 1
            },
            ["holiday_date", "custom_restricted_holiday_date"],
            as_dict=True
        )

        if not holiday:
            continue

        main_date = holiday.holiday_date
        pair_date = holiday.custom_restricted_holiday_date

        # Avoid duplicate pair counting
        key = tuple(sorted([str(main_date), str(pair_date)]))
        if key in processed_pairs:
            continue

        label = f"RH{counter}"

        rh_map[getdate(main_date)] = label

        if pair_date:
            rh_map[getdate(pair_date)] = label

        processed_pairs.add(key)
        counter += 1

    return rh_map


def get_additional_summary_columns():
    return [
        {"label": "Present Days", "fieldname": "present_days", "fieldtype": "Float", "width": 120},
        {"label": "WO", "fieldname": "weekly_off", "fieldtype": "Float", "width": 80},
        {"label": "HO", "fieldname": "holiday", "fieldtype": "Float", "width": 80},
        {"label": "RH", "fieldname": "restricted_holiday", "fieldtype": "Float", "width": 80},
        {"label": "CO", "fieldname": "comp_off", "fieldtype": "Float", "width": 80},
        {"label": "Leave", "fieldname": "paid_leave", "fieldtype": "Float", "width": 100},
        {"label": "Leave Penalty", "fieldname": "leave_penalty", "fieldtype": "Float", "width": 140},
        {"label": "PR", "fieldname": "partial", "fieldtype": "Float", "width": 80},
        {"label": "UAB", "fieldname": "uab", "fieldtype": "Float", "width": 100},
        {"label": "LWP", "fieldname": "lwp", "fieldtype": "Float", "width": 80},
        {"label": "LWP Penalty", "fieldname": "lwp_penalty", "fieldtype": "Float", "width": 140},
        {"label": "Net Payable Days", "fieldname": "net_payable_days", "fieldtype": "Float", "width": 160},
    ]


# def calculate_attendance_metrics(employee, filters, employee_attendance, rh_map):
#     metrics = {
#         "present_days": 0,
#         "weekly_off": 0,
#         "holiday": 0,
#         "restricted_holiday": 0,
#         "comp_off": 0,
#         "paid_leave": 0,
#         "leave_penalty": 0,
#         "partial": 0,
#         "uab": 0,
#         "lwp": 0,
#         "lwp_penalty": 0,
#     }

#     dates = get_dates_in_period(filters)

#     for d in dates:
#         dt = getdate(d)
#         entries = []

#         for shift, status_dict in employee_attendance.items():
#             if dt in status_dict:
#                 entries.append(status_dict[dt])

#         status = merge_shift_attendance_for_day(entries)

#         # PRESENT
#         if status == "Present":
#             metrics["present_days"] += 1

#         elif status == "Half Day/Other Half Present":
#             metrics["present_days"] += 0.5
#             metrics["paid_leave"] += 0.5

#         elif status == "Half Day/Other Half Absent":
#             metrics["present_days"] += 0.5
#             metrics["uab"] += 0.5

#         # WEEKLY OFF / HOLIDAY
#         elif status == "Weekly Off":
#             metrics["weekly_off"] += 1

#         elif status == "Holiday":
#             metrics["holiday"] += 1

#         # RESTRICTED HOLIDAY
#         elif status == "Restricted Holiday":
#             metrics["restricted_holiday"] += 1

#         elif dt in rh_map:
#             metrics["restricted_holiday"] += 1

#         # PARTIAL
#         elif status == "Partially":
#             metrics["partial"] += 1

#         # LEAVE
#         elif status == "On Leave":
#             if entries:
#                 leave_type = entries[0].get("leave_type")

#                 if leave_type == "Leave Without Pay":
#                     metrics["lwp"] += 1
#                 elif leave_type == "Compensatory Off":
#                     metrics["comp_off"] += 1
#                 else:
#                     metrics["paid_leave"] += 1

#         # ABSENT → UAB
#         elif status == "Absent":
#             metrics["uab"] += 1

#         # PENALTY
#         for e in entries:
#             if e.get("is_penalize"):
#                 penalty_type = e.get("penalty_leave_type")

#                 if penalty_type == "Leave Without Pay":
#                     metrics["lwp_penalty"] += 1
#                 else:
#                     metrics["leave_penalty"] += 1

#     # NET PAYABLE DAYS
#     metrics["net_payable_days"] = (
#         metrics["present_days"]
#         + metrics["weekly_off"]
#         + metrics["holiday"]
#         + metrics["restricted_holiday"]
#         + metrics["comp_off"]
#         + metrics["paid_leave"]
#         + metrics["leave_penalty"]
#     )

#     return metrics


# def calculate_attendance_metrics(employee, filters, employee_attendance, rh_map):
#     metrics = {
#         "present_days": 0,
#         "weekly_off": 0,
#         "holiday": 0,
#         "restricted_holiday": 0,
#         "comp_off": 0,
#         "paid_leave": 0,
#         "leave_penalty": 0,
#         "partial": 0,
#         "uab": 0,
#         "lwp": 0,
#         "lwp_penalty": 0,
#     }

#     dates = get_dates_in_period(filters)

#     for d in dates:
#         dt = getdate(d)
#         entries = []

#         # Collect all shift entries
#         for shift, status_dict in employee_attendance.items():
#             if dt in status_dict:
#                 entries.append(status_dict[dt])

#         # ------------------------
#         # ✅ WEEKLY OFF (FIXED)
#         # ------------------------
#         if any(e.get("status") == "Weekly Off" for e in entries):
#             metrics["weekly_off"] += 1
#             continue

#         # ------------------------
#         # ✅ HOLIDAY (FIXED)
#         # ------------------------
#         if any(e.get("status") == "Holiday" for e in entries):
#             metrics["holiday"] += 1
#             continue

#         # ------------------------
#         # Merge attendance after WO/HO check
#         # ------------------------
#         status = merge_shift_attendance_for_day(entries)

#         # ------------------------
#         # PRESENT
#         # ------------------------
#         if status == "Present":
#             metrics["present_days"] += 1

#         elif status == "Half Day/Other Half Present":
#             metrics["present_days"] += 0.5
#             metrics["paid_leave"] += 0.5

#         elif status == "Half Day/Other Half Absent":
#             metrics["present_days"] += 0.5
#             metrics["uab"] += 0.5

#         # ------------------------
#         # RESTRICTED HOLIDAY
#         # ------------------------
#         elif status == "Restricted Holiday":
#             metrics["restricted_holiday"] += 1

#         elif dt in rh_map:
#             metrics["restricted_holiday"] += 1

#         # ------------------------
#         # PARTIAL
#         # ------------------------
#         elif status == "Partially":
#             metrics["partial"] += 1

#         # ------------------------
#         # LEAVE
#         # ------------------------
#         elif status == "On Leave":
#             if entries:
#                 leave_type = entries[0].get("leave_type")

#                 if leave_type == "Leave Without Pay":
#                     metrics["lwp"] += 1
#                 elif leave_type == "Compensatory Off":
#                     metrics["comp_off"] += 1
#                 else:
#                     metrics["paid_leave"] += 1

#         # ------------------------
#         # ABSENT → UAB
#         # ------------------------
#         elif status == "Absent":
#             metrics["uab"] += 1

#         # ------------------------
#         # PENALTY (from raw entries)
#         # ------------------------
#         for e in entries:
#             if e.get("is_penalize"):
#                 penalty_type = e.get("penalty_leave_type")

#                 if penalty_type == "Leave Without Pay":
#                     metrics["lwp_penalty"] += 1
#                 else:
#                     metrics["leave_penalty"] += 1

#     # ------------------------
#     # NET PAYABLE DAYS
#     # ------------------------
#     metrics["net_payable_days"] = (
#         metrics["present_days"]
#         + metrics["weekly_off"]
#         + metrics["holiday"]
#         + metrics["restricted_holiday"]
#         + metrics["comp_off"]
#         + metrics["paid_leave"]
#         + metrics["leave_penalty"]
#     )

#     return metrics




def calculate_attendance_metrics(employee, filters, employee_attendance, rh_map, rejected_leave_days):
    metrics = {
        "present_days": 0,
        "weekly_off": 0,
        "holiday": 0,
        "restricted_holiday": 0,
        "comp_off": 0,
        "paid_leave": 0,
        "leave_penalty": 0,
        "partial": 0,
        "uab": 0,
        "lwp": 0,
        "lwp_penalty": 0,
    }

    dates = get_dates_in_period(filters)

    for d in dates:
        dt = getdate(d)
        entries = []

        for shift, status_dict in employee_attendance.items():
            if dt in status_dict:
                entries.append(status_dict[dt])

        # ─────────────────────────────────────────────────────────────
        # NO ATTENDANCE RECORD — skip entirely
        # WO, HO, RH are only counted when an actual submitted
        # attendance record exists with the corresponding status
        # ─────────────────────────────────────────────────────────────
        if not entries:
            continue

        # ─────────────────────────────────────────────────────────────
        # ATTENDANCE RECORD EXISTS
        # Use raw_status from DB (not merged HTML string) for comparisons
        # ─────────────────────────────────────────────────────────────
        raw_status   = entries[0].get("status")
        leave_type   = entries[0].get("leave_type")
        is_penalize = any(e.get("is_penalize") for e in entries)

        # ✅ Read actual stored penalty count (stored as negative e.g. -0.5, -1)
        penalty_days = abs(
            float(
                next(
                    (e.get("penalty_leave_count", 0) or 0
                     for e in entries if e.get("is_penalize")),
                    0
                )
            )
        )
        # Fallback if field is null/missing — infer from status
        if is_penalize and penalty_days == 0:
            if raw_status in (
                "Half Day/Other Half Present",
                "Half Day/Other Half Absent",
                "Half Day",
                "Partially",
            ):
                penalty_days = 0.5
            else:
                penalty_days = 1.0

        penalty_type = next(
            (e.get("penalty_leave_type") for e in entries if e.get("penalty_leave_type")),
            None
        )

        # ── Weekly Off ───────────────────────────────────────────────
        if raw_status == "Weekly Off":
            metrics["weekly_off"] += 1
            continue

        # ── Holiday ──────────────────────────────────────────────────
        if raw_status == "Holiday":
            metrics["holiday"] += 1
            continue

        # ── Restricted Holiday ───────────────────────────────────────
        if raw_status == "Restricted Holiday":
            metrics["restricted_holiday"] += 1
            continue

        # ── Present (full day) ───────────────────────────────────────
        if raw_status == "Present":
            metrics["present_days"] += 1
            # Penalty check: present but penalised for something
            # (e.g. late entry penalty already applied by scheduler)
            if is_penalize:
                _add_penalty(metrics, penalty_type, penalty_days)
            continue

       # ── Half Day / Other Half Present ────────────────────────────
        # Employee was on LEAVE for one half, PRESENT for the other half
        # → 0.5 present + leave consumed
        # Compensatory Off is always deducted as full day (1.0)
        # All other leave types are deducted as half day (0.5)
        if raw_status in ("Half Day/Other Half Present", "Half Day"):
            metrics["present_days"] += 0.5
            leave_days_to_deduct = 1.0 if leave_type == "Compensatory Off" else 0.5
            _add_leave(metrics, leave_type, leave_days_to_deduct)

            if is_penalize:
                _add_penalty(metrics, penalty_type, penalty_days)
            continue

        # ── Half Day / Other Half Absent ─────────────────────────────
        # Always count the absent half as UAB
        # If penalty also applied → add to penalty bucket as well
        if raw_status == "Half Day/Other Half Absent":
            metrics["present_days"] += 0.5
            metrics["uab"] += 0.5
            if is_penalize:
                _add_penalty(metrics, penalty_type, penalty_days)
            continue

        # ── Partially (single checkin — in OR out only) ──────────────
        # Partial presence counted separately; penalty for the missing punch
        if raw_status == "Partially":
            metrics["partial"] += 1
            if is_penalize:
                _add_penalty(metrics, penalty_type, penalty_days)
            continue

        # ── On Leave (full day) ──────────────────────────────────────
        if raw_status == "On Leave":
            _add_leave(metrics, leave_type, 1)
            if is_penalize:
                _add_penalty(metrics, penalty_type, penalty_days)
            continue

        # ── Absent (full day) ────────────────────────────────────────
        # Always count as UAB regardless of penalty
        # If penalty also applied → add to penalty bucket as well
        if raw_status == "Absent":
            metrics["uab"] += 1
            if is_penalize:
                _add_penalty(metrics, penalty_type, penalty_days)
            continue

        # ── RH via rh_map — only count if attendance record explicitly
        # has status "Restricted Holiday", handled above in raw_status check
        # This fallback is intentionally removed to avoid double counting
        pass
				
		# ✅ Add rejected leave days to UAB
    metrics["uab"] += float(rejected_leave_days or 0)

    # ─────────────────────────────────────────────────────────────────
    # NET PAYABLE DAYS
    # ─────────────────────────────────────────────────────────────────
    metrics["net_payable_days"] = (
        metrics["present_days"]
        + metrics["weekly_off"]
        + metrics["holiday"]
        + metrics["restricted_holiday"]
        + metrics["comp_off"]
        + metrics["paid_leave"]
        + metrics["leave_penalty"]
    )

    return metrics


# ─────────────────────────────────────────────────────────────────────
# HELPERS — keep the main function readable
# ─────────────────────────────────────────────────────────────────────

def _add_leave(metrics: dict, leave_type: str | None, days: float):
    """Route leave days to the correct leave bucket."""
    if leave_type == "Leave Without Pay":
        metrics["lwp"] += days
    elif leave_type == "Compensatory Off":
        metrics["comp_off"] += days
    else:
        metrics["paid_leave"] += days


def _add_penalty(metrics: dict, penalty_leave_type: str | None, days: float):
    """Route penalty days to the correct penalty bucket."""
    if penalty_leave_type == "Leave Without Pay":
        metrics["lwp_penalty"] += days
    else:
        metrics["leave_penalty"] += days


def get_rejected_leave_days(employee: str, filters: Filters) -> float:
    """
    Returns total days where employee applied for leave but
    the Leave Application was Rejected for the filter period.
    """
    LeaveApplication = frappe.qb.DocType("Leave Application")
    attendance_date_condition = get_date_condition(LeaveApplication.from_date, filters)

    rejected_leaves = (
        frappe.qb.from_(LeaveApplication)
        .select(LeaveApplication.from_date, LeaveApplication.to_date, LeaveApplication.total_leave_days)
        .where(
            (LeaveApplication.employee == employee)
            & (LeaveApplication.status == "Rejected")
            & (LeaveApplication.docstatus == 2)
            & (attendance_date_condition)
        )
    ).run(as_dict=True)

    total = 0.0
    for leave in rejected_leaves:
        total += float(leave.total_leave_days or 0)

    return total
