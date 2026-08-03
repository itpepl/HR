# FSR - Field Staff TA/DA Report
#
# ASSUMPTIONS (adjust field names below to match your actual site schema
# if they differ):
#   - Employee.grade holds values such as "Contractual", "Jr. Assistant",
#     "Assistant", "Sr. Assistant" (used for the TA/DA slab logic). Any other
#     grade is treated as the "senior" slab (350/450, 175/225).
#   - Employee.branch is used for the Branch filter.
#   - Geolocation Tracking has: employee (Link Employee), timestamp (Datetime),
#     custom_type (Select: S / E), total_distance (Float).
#   - Employee Activity has: employee (Link Employee), request_date (Datetime),
#     custom_ta_da_mode (Select: "Flat TA DA" / "Used Official Vehicle" /
#     "TA DA as per Km"). The FIRST Employee Activity record of the date
#     (by request_date ascending) decides the TA/DA mode for that day.
#   - HR Settings (Single) has custom_bike_rate_per_km (Float).

import frappe
from frappe import _
from frappe.utils import (
	flt,
	cint,
	getdate,
	nowdate,
	get_datetime,
	add_days,
	date_diff,
	formatdate,
)
from datetime import datetime, timedelta

LOW_GRADES = {"Contractual", "Jr. Assistant", "Assistant", "Sr. Assistant"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def validate_filters(filters):
	today = getdate(nowdate())

	if not filters.from_date:
		filters.from_date = today.replace(day=1)
	if not filters.to_date:
		filters.to_date = today

	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)

	# Neither filter is allowed to be a future date
	if from_date > today:
		from_date = today.replace(day=1)
	if to_date > today:
		to_date = today

	if from_date > to_date:
		from_date, to_date = to_date, from_date

	filters.from_date = from_date
	filters.to_date = to_date


def get_columns():
	return [
		{"label": _("Employee Code"), "fieldname": "employee", "fieldtype": "Link",
			"options": "Employee", "width": 160},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data"},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Data", "width": 100},
		{"label": _("Start Time"), "fieldname": "start_time", "fieldtype": "Data"},
		{"label": _("End Time"), "fieldname": "end_time", "fieldtype": "Data"},
		{"label": _("Nos. of Place/ New Visited Points"), "fieldname": "visit_points",
			"fieldtype": "Int"},
		{"label": _("Duration (HH:MM)"), "fieldname": "duration", "fieldtype": "Data"},
		{"label": _("Distance (KM)"), "fieldname": "distance", "fieldtype": "Float",
			"precision": 2},
		{"label": _("Visit Type"), "fieldname": "visit_type", "fieldtype": "Data"},
		{"label": _("TA DA Mode"), "fieldname": "ta_da_mode", "fieldtype": "Data"},
		{"label": _("TA/DA Flat"), "fieldname": "tada_flat", "fieldtype": "Currency"},
		{"label": _("If Plant Vehicle Used"), "fieldname": "plant_vehicle_used",
			"fieldtype": "Currency"},
		{"label": _("Total TA as per Kms"), "fieldname": "total_ta_km",
			"fieldtype": "Currency"},
		{"label": _("Photo Status"), "fieldname": "photo_status", "fieldtype": "Data"},
	]


def get_data(filters):
	employees = get_employees(filters)
	if not employees:
		return []

	bike_rate = flt(frappe.db.get_single_value("HR Settings", "custom_bike_rate_per_km")) or 0
	date_list = get_date_list(filters.from_date, filters.to_date)
	attendance_map = get_attendance_map(filters)

	out = []
	for emp in employees:
		emp_rows = []
		# totals = {"visit_points": 0, "distance": 0.0, "tada_flat": 0.0,
		# 	"plant_vehicle_used": 0.0, "total_ta_km": 0.0}

		for day in date_list:
			row = build_row(emp, day, bike_rate, attendance_map)
			emp_rows.append(row)
			# totals["visit_points"] += cint(row["visit_points"])
			# totals["distance"] += flt(row["distance"])
			# totals["tada_flat"] += flt(row["tada_flat"])
			# totals["plant_vehicle_used"] += flt(row["plant_vehicle_used"])
			# totals["total_ta_km"] += flt(row["total_ta_km"])

		out.extend(emp_rows)

		# out.append({
		# 	"employee": "",
		# 	"employee_name": "",
		# 	"date": _("Total"),
		# 	"start_time": "",
		# 	"end_time": "",
		# 	"visit_points": totals["visit_points"],
		# 	"duration": "",
		# 	"distance": flt(totals["distance"], 2),
		# 	"visit_type": "",
		# 	"ta_da_mode": "",
		# 	"tada_flat": flt(totals["tada_flat"], 2),
		# 	"plant_vehicle_used": flt(totals["plant_vehicle_used"], 2),
		# 	"total_ta_km": flt(totals["total_ta_km"], 2),
		# 	"photo_status": "",
		# 	"is_total_row": 1,
		# })

	return out


def get_employees(filters):
	emp_filters = {"status": "Active"}
	if filters.get("employee"):
		emp_filters["name"] = filters.employee
	if filters.get("branch"):
		emp_filters["branch"] = filters.branch

	return frappe.get_all(
		"Employee",
		filters=emp_filters,
		fields=["name", "employee_name", "grade", "branch"],
		order_by="employee_name asc",
	)


def get_date_list(from_date, to_date):
	days = date_diff(to_date, from_date)
	return [add_days(from_date, i) for i in range(days + 1)]


def get_attendance_map(filters):
	attendance_filters = {
		"attendance_date": ["between", [filters.from_date, filters.to_date]],
		"docstatus": 1,
	}

	if filters.get("employee"):
		attendance_filters["employee"] = filters.employee

	attendance_list = frappe.get_all(
		"Attendance",
		filters=attendance_filters,
		fields=[
			"employee",
			"attendance_date",
			"status",
			"leave_type",
		],
	)

	attendance_map = {}

	for att in attendance_list:
		attendance_map[(att.employee, att.attendance_date)] = att

	return attendance_map


def build_row(emp, day, bike_rate, attendance_map):
	day_start = get_datetime(f"{day} 00:00:00")
	day_end = get_datetime(f"{day} 23:59:59")

	attendance = attendance_map.get((emp.name, day))

	if attendance:

		status = attendance.status

		if status == "Weekly Off":
			display = "Weekly Off"

		elif status == "Holiday":
			display = "Holiday"

		elif status == "Restricted Holiday":

			holiday_list = frappe.db.get_value(
				"Holiday List Assignment",
				{
					"assigned_to": emp.name,
					"from_date": ["<=", day],
				},
				"holiday_list",
				order_by="from_date desc",
			)

			description = None

			if holiday_list:
				description = frappe.db.get_value(
					"Holiday",
					{
						"parent": holiday_list,
						"holiday_date": day,
					},
					"description",
				)

			display = description or "RH"

		elif status == "On Leave":
			display = attendance.leave_type

		else:
			display = None

		if display:
			return {
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"date": formatdate(day, "dd/mm/yyyy"),
				"start_time": display,
				"end_time": display,
				"visit_points": display,
				"duration": display,
				"distance": display,
				"visit_type": display,
				"ta_da_mode": display,
				"tada_flat": display,
				"plant_vehicle_used": display,
				"total_ta_km": display,
				"photo_status": display,
			}

	start_rec = frappe.db.get_value(
		"Geolocation Tracking",
		{
			"employee": emp.name,
			"custom_type": "S",
			"timestamp": ["between", [day_start, day_end]],
		},
		["timestamp"],
		order_by="timestamp asc",
		as_dict=True,
	)

	end_rec = frappe.db.get_value(
		"Geolocation Tracking",
		{
			"employee": emp.name,
			"custom_type": "E",
			"timestamp": ["between", [day_start, day_end]],
		},
		["timestamp", "total_distance"],
		order_by="timestamp desc",
		as_dict=True,
	)

	start_time = start_rec.timestamp.strftime("%H:%M:%S") if start_rec and start_rec.timestamp else ""
	end_time = end_rec.timestamp.strftime("%H:%M:%S") if end_rec and end_rec.timestamp else ""

	distance = flt(end_rec.total_distance) if end_rec and end_rec.total_distance else 0.0

	duration = ""
	if start_rec and start_rec.timestamp and end_rec and end_rec.timestamp:
		diff_seconds = (end_rec.timestamp - start_rec.timestamp).total_seconds()
		if diff_seconds > 0:
			hh = int(diff_seconds // 3600)
			mm = int((diff_seconds % 3600) // 60)
			duration = "{:02d}:{:02d}".format(hh, mm)

	visit_type = "Up Country" if distance > 60 else "Local"

	# Fetch the whole day's Employee Activity list once - used for:
	#   - visit count (Society / New Visited Points)
	#   - TA/DA mode (custom_ta_da_mode on the FIRST record of the date)
	#   - photo status (any record before 07:00 with an attachment)
	day_activities = frappe.get_all(
		"Employee Activity",
		filters={
			"employee": emp.name,
			"request_date": ["between", [day_start, day_end]],
		},
		fields=["name", "request_date", "custom_ta_da_mode"],
		order_by="request_date asc",
	)

	visit_points = len(day_activities)

	cutoff_time = day_start + timedelta(hours=7)

	before_7am_visits = [
			d for d in day_activities
			if d.request_date and get_datetime(d.request_date) < cutoff_time
	]

	eligible_for_tada = (
			visit_points >= 2 and
			len(before_7am_visits) == 1
	)

	tada_flat = 0.0
	plant_vehicle_used = 0.0
	total_ta_km = 0.0
	ta_da_mode = ""

	if day_activities:
		ta_da_mode = day_activities[0].custom_ta_da_mode or ""

	if eligible_for_tada:
		is_low_grade = emp.grade in LOW_GRADES
		ta_mode = ta_da_mode

		if ta_mode == "Flat TA DA":
			if is_low_grade:
				tada_flat = 300 if visit_type == "Local" else 400
			else:
				tada_flat = 350 if visit_type == "Local" else 450

		elif ta_mode == "Used Official Vehicle":
			if is_low_grade:
				plant_vehicle_used = 150 if visit_type == "Local" else 200
			else:
				plant_vehicle_used = 175 if visit_type == "Local" else 225

		elif ta_mode == "TA DA as per Km":
			total_ta_km = flt(distance * bike_rate, 2)

	photo_status = get_photo_status(day_activities, day_start)

	return {
		"employee": emp.name,
		"employee_name": emp.employee_name,
		"date": formatdate(day, "dd/mm/yyyy"),
		"start_time": start_time,
		"end_time": end_time,
		"visit_points": visit_points,
		"duration": duration,
		"distance": flt(distance, 2),
		"visit_type": visit_type,
		"ta_da_mode": ta_da_mode,
		"tada_flat": tada_flat,
		"plant_vehicle_used": plant_vehicle_used,
		"total_ta_km": total_ta_km,
		"photo_status": photo_status,
	}


def get_photo_status(day_activities, day_start):
	"""Uploaded if any Employee Activity before 07:00 AM on that date has an attachment."""
	cutoff = day_start + timedelta(hours=7)

	activities = [
		a for a in day_activities
		if a.request_date and get_datetime(a.request_date) <= cutoff
	]

	for activity in activities:
		has_attachment = frappe.db.exists(
			"File",
			{
				"attached_to_doctype": "Employee Activity",
				"attached_to_name": activity.name,
			},
		)
		if has_attachment:
			return _("Uploaded")

	return _("Not Uploaded")