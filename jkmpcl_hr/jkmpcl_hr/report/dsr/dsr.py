# # For license information, please see license.txt

# import frappe
# from frappe import _
# from frappe.utils import getdate, add_days, date_diff, get_datetime, flt, cstr


# def execute(filters=None):
# 	filters = frappe._dict(filters or {})

# 	if not filters.get("from_date") or not filters.get("to_date"):
# 		frappe.throw(_("Please select From Date and To Date"))

# 	columns = get_columns()
# 	data = get_data(filters)

# 	return columns, data


# def get_columns():
# 	return [
# 		{"fieldname": "employee", "label": _("Employee ID"), "fieldtype": "Link", "options": "Employee"},
# 		{"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data"},
# 		{"fieldname": "datetime", "label": _("Date/Time"), "fieldtype": "Data"},
# 		{"fieldname": "event_type", "label": _("Event Type"), "fieldtype": "Data"},
# 		{"fieldname": "km_calculation", "label": _("KM Calculation"), "fieldtype": "Float", "precision": 2},
# 		{"fieldname": "address", "label": _("Address"), "fieldtype": "Data"},
# 		{"fieldname": "subject", "label": _("Subject"), "fieldtype": "Data"},
# 		{"fieldname": "message", "label": _("Message"), "fieldtype": "Data"},
# 		{"fieldname": "photos", "label": _("Photos"), "fieldtype": "HTML"},
# 	]


# def get_data(filters):
# 	data = []

# 	employees = get_employees(filters)
# 	if not employees:
# 		return data

# 	date_list = get_date_list(filters.get("from_date"), filters.get("to_date"))

# 	for emp in employees:
# 		emp_rows = []
# 		emp_has_data = False

# 		for date in date_list:
# 			geo_records = get_geo_records(emp.name, date)
# 			activities = get_employee_activities(emp.name, date)

# 			start_record = get_start_record(geo_records)
# 			end_record = get_end_record(geo_records)

# 			# Nothing at all for this employee on this date -> skip the date entirely
# 			if not start_record and not activities and not end_record:
# 				continue

# 			emp_has_data = True
# 			day_total = 0.0

# 			# ---- Start Row (custom_type = S) ----
# 			if start_record:
# 				emp_rows.append({
# 					"employee": emp.name,
# 					"employee_name": emp.employee_name,
# 					"datetime": format_datetime_value(start_record.timestamp),
# 					"event_type": start_record.custom_type,
# 					"km_calculation": flt(start_record.total_distance),
# 					"address": start_record.address,
# 					"subject": "",
# 					"message": "",
# 					"photos": ""
# 				})
# 				day_total += flt(start_record.total_distance)

# 			# ---- Activity Rows (event_type always "FN") ----
# 			for activity in activities:
# 				matched_geo = get_matching_geo_record(emp.name, date, activity.request_date)
# 				km_value = flt(matched_geo.total_distance) if matched_geo else 0.0

# 				emp_rows.append({
# 					"employee": emp.name,
# 					"employee_name": emp.employee_name,
# 					"datetime": format_datetime_value(activity.request_date),
# 					"event_type": "FN",
# 					"km_calculation": km_value,
# 					"address": activity.custom_location,
# 					"subject": activity.purpose,
# 					"message": activity.activity_details,
# 					"photos": get_photo_html(activity.name)
# 				})
# 				day_total += km_value

# 			# ---- End Row (custom_type = E) ----
# 			if end_record:
# 				emp_rows.append({
# 					"employee": emp.name,
# 					"employee_name": emp.employee_name,
# 					"datetime": format_datetime_value(end_record.timestamp),
# 					"event_type": end_record.custom_type,
# 					"km_calculation": flt(end_record.total_distance),
# 					"address": end_record.address,
# 					"subject": "",
# 					"message": "",
# 					"photos": ""
# 				})
# 				day_total += flt(end_record.total_distance)

# 			# ---- TOTAL row for the date ----
# 			emp_rows.append({
# 				"employee": "",
# 				"employee_name": "",
# 				"datetime": "",
# 				"event_type": _("TOTAL"),
# 				"km_calculation": flt(day_total),
# 				"address": "",
# 				"subject": "",
# 				"message": "",
# 				"photos": "",
# 				"is_total_row": 1
# 			})

# 		if emp_has_data:
# 			data.extend(emp_rows)

# 	return data


# def get_employees(filters):
# 	conditions = {}

# 	if filters.get("employee"):
# 		conditions["name"] = filters.get("employee")

# 	if filters.get("branch"):
# 		conditions["branch"] = filters.get("branch")

# 	# conditions["custom_attendance_source"] = ["!=", "Biometric"]

# 	return frappe.get_all(
# 		"Employee",
# 		filters=conditions,
# 		fields=["name", "employee_name"],
# 		order_by="employee_name asc"
# 	)


# def get_date_list(from_date, to_date):
# 	from_date = getdate(from_date)
# 	to_date = getdate(to_date)

# 	days = date_diff(to_date, from_date)
# 	return [add_days(from_date, i) for i in range(days + 1)]


# def get_geo_records(employee, date):
# 	"""All Geolocation Tracking rows for the employee on the given date, ascending by time."""
# 	return frappe.get_all(
# 		"Geolocation Tracking",
# 		filters={
# 			"employee": employee,
# 			"timestamp": ["between", ["{0} 00:00:00".format(date), "{0} 23:59:59".format(date)]]
# 		},
# 		fields=["name", "timestamp", "custom_type", "total_distance", "address"],
# 		order_by="timestamp asc"
# 	)


# def get_start_record(geo_records):
# 	"""First record of the day whose custom_type is S."""
# 	for record in geo_records:
# 		if record.custom_type == "S":
# 			return record
# 	return None


# def get_end_record(geo_records):
# 	"""Last record of the day whose custom_type is E."""
# 	end_record = None
# 	for record in geo_records:
# 		if record.custom_type == "E":
# 			end_record = record
# 	return end_record


# def get_employee_activities(employee, date):
# 	"""All Employee Activity rows for the employee on the given date, ascending by request_date."""
# 	return frappe.get_all(
# 		"Employee Activity",
# 		filters={
# 			"employee": employee,
# 			"request_date": ["between", ["{0} 00:00:00".format(date), "{0} 23:59:59".format(date)]]
# 		},
# 		fields=["name", "request_date", "purpose", "activity_details", "custom_location"],
# 		order_by="request_date asc"
# 	)


# def get_matching_geo_record(employee, date, request_date):
# 	"""
# 	Geolocation Tracking row for the same day whose timestamp is the closest one
# 	at or before the activity's request_date - used to pick total_distance for
# 	an Employee Activity row.
# 	"""
# 	records = frappe.get_all(
# 		"Geolocation Tracking",
# 		filters={
# 			"employee": employee,
# 			"timestamp": ["between", ["{0} 00:00:00".format(date), cstr(request_date)]]
# 		},
# 		fields=["name", "timestamp", "total_distance"],
# 		order_by="timestamp desc",
# 		limit_page_length=1
# 	)
# 	return records[0] if records else None


# def get_photo_html(activity_name):
# 	"""Build a 'View Image' link/button for every file attached to the Employee Activity row."""
# 	files = frappe.get_all(
# 		"File",
# 		filters={
# 			"attached_to_doctype": "Employee Activity",
# 			"attached_to_name": activity_name
# 		},
# 		fields=["file_url", "file_name"]
# 	)

# 	if not files:
# 		return ""

# 	links = []
# 	for i, f in enumerate(files, start=1):
# 		label = _("View Image") if len(files) == 1 else _("View Image {0}").format(i)
# 		links.append(
# 			'<a class="btn btn-xs btn-default" href="{0}" target="_blank">{1}</a>'.format(
# 				frappe.utils.escape_html(f.file_url), label
# 			)
# 		)

# 	return " ".join(links)


# def format_datetime_value(value):
# 	if not value:
# 		return ""
# 	return cstr(get_datetime(value))







# Copyright (c) 2026, SanskarTechnolab and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, date_diff, get_datetime, flt, cstr


def execute(filters=None):
	filters = frappe._dict(filters or {})

	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("Please select From Date and To Date"))

	columns = get_columns()
	data = get_data(filters)

	grand_total = sum(
		flt(row.get("km_calculation", 0)) for row in data if not row.get("is_total_row")
	)

	data.append({
		"employee": "",
		"employee_name": "",
		"datetime": "",
		"event_type": _("Grand Total"),
		"km_calculation": grand_total,
		"address": "",
		"subject": "",
		"message": "",
		"photos": "",
		"is_total_row": 1
	})

	return columns, data


def get_columns():
	return [
		{"fieldname": "employee", "label": _("Employee ID"), "fieldtype": "Link", "options": "Employee", "width": 160},
		{"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data"},
		{"fieldname": "datetime", "label": _("Date/Time"), "fieldtype": "Data"},
		{"fieldname": "event_type", "label": _("Event Type"), "fieldtype": "Data"},
		{"fieldname": "km_calculation", "label": _("KM Calculation"), "fieldtype": "Float", "precision": 2},
		{"fieldname": "address", "label": _("Address"), "fieldtype": "Data", "width": 300},
		{"fieldname": "subject", "label": _("Subject"), "fieldtype": "Data"},
		{"fieldname": "message", "label": _("Message"), "fieldtype": "Data"},
		{"fieldname": "photos", "label": _("Photos"), "fieldtype": "HTML", "width": 120},
	]


def get_data(filters):
	data = []

	employees = get_employees(filters)
	if not employees:
		return data

	date_list = get_date_list(filters.get("from_date"), filters.get("to_date"))

	for emp in employees:
		emp_rows = []
		emp_has_data = False

		for date in date_list:
			geo_records = get_geo_records(emp.name, date)
			activities = get_employee_activities(emp.name, date)

			start_record = get_start_record(geo_records)
			end_record = get_end_record(geo_records)

			# Nothing at all for this employee on this date -> skip the date entirely
			if not start_record and not activities and not end_record:
				continue

			emp_has_data = True
			day_total = 0.0

			# ---- Start Row (custom_type = S) ----
			if start_record:
				emp_rows.append({
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"datetime": format_datetime_value(start_record.timestamp),
					"event_type": start_record.custom_type,
					"km_calculation": flt(start_record.total_distance),
					"address": start_record.address,
					"subject": "",
					"message": "",
					"photos": ""
				})

				day_total += flt(start_record.total_distance)

			# ---- Activity Rows (event_type always "FN") ----
			previous_activity_km = 0.0
			
			for activity in activities:
				matched_geo = get_matching_geo_record(emp.name, date, activity.request_date)
				km_value = flt(matched_geo.total_distance) if matched_geo else 0.0

				if previous_activity_km > 0:
					km_value -= previous_activity_km
									
				emp_rows.append({
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"datetime": format_datetime_value(activity.request_date),
					"event_type": "FN",
					"km_calculation": km_value,
					"address": activity.custom_location,
					"subject": activity.purpose,
					"message": activity.activity_details,
					"photos": get_photo_html(activity.name)
				})
				
				day_total += km_value
				previous_activity_km += km_value

			# ---- End Row (custom_type = E) ----
			if end_record:
				end_km = flt(end_record.total_distance) - flt(previous_activity_km)
				emp_rows.append({
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"datetime": format_datetime_value(end_record.timestamp),
					"event_type": end_record.custom_type,
					"km_calculation": end_km,
					"address": end_record.address,
					"subject": "",
					"message": "",
					"photos": ""
				})
				day_total += flt(end_km)

			emp_rows.append({
				"employee": "",
				"employee_name": "",
				"datetime": "",
				"event_type": _("Sub Total"),
				"km_calculation": flt(day_total, 2),
				"address": "",
				"subject": "",
				"message": "",
				"photos": "",
				"is_total_row": 1
			})

		if emp_has_data:
			data.extend(emp_rows)

	return data


def get_employees(filters):
	conditions = {}

	if filters.get("employee"):
		conditions["name"] = filters.get("employee")

	if filters.get("branch"):
		conditions["branch"] = filters.get("branch")

	conditions["custom_attendance_source"] = ["!=", "Biometric"]

	return frappe.get_all(
		"Employee",
		filters=conditions,
		fields=["name", "employee_name"],
		order_by="employee_name asc"
	)


def get_date_list(from_date, to_date):
	from_date = getdate(from_date)
	to_date = getdate(to_date)

	days = date_diff(to_date, from_date)
	return [add_days(from_date, i) for i in range(days + 1)]


def get_geo_records(employee, date):
	"""All Geolocation Tracking rows for the employee on the given date, ascending by time."""
	return frappe.get_all(
		"Geolocation Tracking",
		filters={
			"employee": employee,
			"timestamp": ["between", ["{0} 00:00:00".format(date), "{0} 23:59:59".format(date)]]
		},
		fields=["name", "timestamp", "custom_type", "total_distance", "address"],
		order_by="timestamp asc"
	)


def get_start_record(geo_records):
	"""First record of the day whose custom_type is S."""
	for record in geo_records:
		if record.custom_type == "S":
			return record
	return None


def get_end_record(geo_records):
	"""Last record of the day whose custom_type is E."""
	end_record = None
	for record in geo_records:
		if record.custom_type == "E":
			end_record = record
	return end_record


def get_employee_activities(employee, date):
	"""All Employee Activity rows for the employee on the given date, ascending by request_date."""
	return frappe.get_all(
		"Employee Activity",
		filters={
			"employee": employee,
			"request_date": ["between", ["{0} 00:00:00".format(date), "{0} 23:59:59".format(date)]]
		},
		fields=["name", "request_date", "purpose", "activity_details", "custom_location"],
		order_by="request_date asc"
	)


def get_matching_geo_record(employee, date, request_date):
	"""
	Geolocation Tracking row for the same day whose timestamp is the closest one
	at or before the activity's request_date - used to pick total_distance for
	an Employee Activity row.
	"""
	records = frappe.get_all(
		"Geolocation Tracking",
		filters={
			"employee": employee,
			"timestamp": [">=", cstr(request_date)],
			"custom_type": ["not in", ["S", "E"]]
		},
		fields=["name", "timestamp", "total_distance"],
		order_by="timestamp asc",
		limit_page_length=1
	)
	return records[0] if records else None


def get_photo_html(activity_name):
	"""Build a 'View Image' link/button for every file attached to the Employee Activity row."""
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Employee Activity",
			"attached_to_name": activity_name
		},
		fields=["file_url", "file_name"]
	)

	if not files:
		return ""

	links = []
	for i, f in enumerate(files, start=1):
		label = _("View Image") if len(files) == 1 else _("View Image {0}").format(i)
		links.append(
			'<a class="btn btn-xs btn-default" href="{0}" target="_blank">{1}</a>'.format(
				frappe.utils.escape_html(f.file_url), label
			)
		)

	return " ".join(links)


def format_datetime_value(value):
	if not value:
		return ""
	return cstr(get_datetime(value))