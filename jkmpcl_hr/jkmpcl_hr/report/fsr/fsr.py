# # FSR - Field Staff TA/DA Report
# #
# # ASSUMPTIONS (adjust field names below to match your actual site schema
# # if they differ):
# #   - Employee.grade holds values such as "Contractual", "Jr. Assistant",
# #     "Assistant", "Sr. Assistant" (used for the TA/DA slab logic). Any other
# #     grade is treated as the "senior" slab (350/450, 175/225).
# #   - Employee.branch is used for the Branch filter.
# #   - Geolocation Tracking has: employee (Link Employee), timestamp (Datetime),
# #     custom_type (Select: S / E), total_distance (Float).
# #   - Employee Activity has: employee (Link Employee), request_date (Datetime),
# #     custom_ta_da_mode (Select: "Flat TA DA" / "Used Official Vehicle" /
# #     "TA DA as per Km"). The FIRST Employee Activity record of the date
# #     (by request_date ascending) decides the TA/DA mode for that day.
# #   - HR Settings (Single) has custom_bike_rate_per_km (Float).

# import json
# import io
# import xlsxwriter
# import frappe
# import re
# from html import unescape
# from frappe import _
# from frappe.utils import (
# 	flt,
# 	cint,
# 	getdate,
# 	nowdate,
# 	get_datetime,
# 	add_days,
# 	date_diff,
# 	formatdate,
# 	strip_html
# )
# from datetime import datetime, timedelta

# LOW_GRADES = {"Contractual", "Jr. Assistant", "Assistant", "Sr. Assistant"}


# def execute(filters=None):
# 	filters = frappe._dict(filters or {})
# 	validate_filters(filters)

# 	columns = get_columns()
# 	data = get_data(filters)

# 	return columns, data


# def validate_filters(filters):
# 	today = getdate(nowdate())

# 	if not filters.from_date:
# 		filters.from_date = today.replace(day=1)
# 	if not filters.to_date:
# 		filters.to_date = today

# 	from_date = getdate(filters.from_date)
# 	to_date = getdate(filters.to_date)

# 	# Neither filter is allowed to be a future date
# 	if from_date > today:
# 		from_date = today.replace(day=1)
# 	if to_date > today:
# 		to_date = today

# 	if from_date > to_date:
# 		from_date, to_date = to_date, from_date

# 	filters.from_date = from_date
# 	filters.to_date = to_date


# def get_columns():
# 	return [
# 		{"label": _("Employee Code"), "fieldname": "employee", "fieldtype": "Link",
# 			"options": "Employee", "width": 160},
# 		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data"},
# 		{"label": _("Date"), "fieldname": "date", "fieldtype": "Data", "width": 100},
# 		{"label": _("Start Time"), "fieldname": "start_time", "fieldtype": "Data"},
# 		{"label": _("End Time"), "fieldname": "end_time", "fieldtype": "Data"},
# 		{"label": _("Nos. of Place/ New Visited Points"), "fieldname": "visit_points",
# 			"fieldtype": "Int"},
# 		{"label": _("Duration (HH:MM)"), "fieldname": "duration", "fieldtype": "Data"},
# 		{"label": _("Distance (KM)"), "fieldname": "distance", "fieldtype": "Float",
# 			"precision": 2},
# 		{"label": _("Visit Type"), "fieldname": "visit_type", "fieldtype": "Data"},
# 		{"label": _("TA DA Mode"), "fieldname": "ta_da_mode", "fieldtype": "Data"},
# 		{"label": _("TA/DA Flat"), "fieldname": "tada_flat", "fieldtype": "Currency"},
# 		{"label": _("If Plant Vehicle Used"), "fieldname": "plant_vehicle_used",
# 			"fieldtype": "Currency"},
# 		{"label": _("Total TA as per Kms"), "fieldname": "total_ta_km",
# 			"fieldtype": "Currency"},
# 		{"label": _("Photo Status"), "fieldname": "photo_status", "fieldtype": "Data"},
# 	]


# def get_data(filters):
# 	employees = get_employees(filters)
# 	if not employees:
# 		return []

# 	bike_rate = flt(frappe.db.get_single_value("HR Settings", "custom_bike_rate_per_km")) or 0
# 	date_list = get_date_list(filters.from_date, filters.to_date)
# 	attendance_map = get_attendance_map(filters)

# 	out = []
# 	for emp in employees:
# 		emp_rows = []
# 		# totals = {"visit_points": 0, "distance": 0.0, "tada_flat": 0.0,
# 		# 	"plant_vehicle_used": 0.0, "total_ta_km": 0.0}

# 		for day in date_list:
# 			row = build_row(emp, day, bike_rate, attendance_map)
# 			emp_rows.append(row)
# 			# totals["visit_points"] += cint(row["visit_points"])
# 			# totals["distance"] += flt(row["distance"])
# 			# totals["tada_flat"] += flt(row["tada_flat"])
# 			# totals["plant_vehicle_used"] += flt(row["plant_vehicle_used"])
# 			# totals["total_ta_km"] += flt(row["total_ta_km"])

# 		out.extend(emp_rows)

# 		# out.append({
# 		# 	"employee": "",
# 		# 	"employee_name": "",
# 		# 	"date": _("Total"),
# 		# 	"start_time": "",
# 		# 	"end_time": "",
# 		# 	"visit_points": totals["visit_points"],
# 		# 	"duration": "",
# 		# 	"distance": flt(totals["distance"], 2),
# 		# 	"visit_type": "",
# 		# 	"ta_da_mode": "",
# 		# 	"tada_flat": flt(totals["tada_flat"], 2),
# 		# 	"plant_vehicle_used": flt(totals["plant_vehicle_used"], 2),
# 		# 	"total_ta_km": flt(totals["total_ta_km"], 2),
# 		# 	"photo_status": "",
# 		# 	"is_total_row": 1,
# 		# })

# 	return out

# def get_user_permitted_branch():
# 	"""
# 	Returns the branch the current user should be restricted to, or None
# 	if the user has full/all-branch access (e.g. System Manager, HR Manager).

# 	Adjust `full_access_roles` to match whichever roles in your system are
# 	meant to see all branches.
# 	"""
# 	user = frappe.session.user

# 	if user == "Administrator":
# 		return None

# 	return frappe.db.get_value("User", user, "custom_branch")


# def get_employees(filters):
# 	emp_filters = {"status": "Active"}

# 	user_branch = get_user_permitted_branch()

# 	if user_branch:
# 		emp_filters["branch"] = user_branch
# 	elif filters.get("branch"):
# 		emp_filters["branch"] = filters.branch

# 	if filters.get("employee"):
# 		emp_filters["name"] = filters.employee

# 	return frappe.get_all(
# 		"Employee",
# 		filters=emp_filters,
# 		fields=["name", "employee_name", "grade", "branch"],
# 		order_by="employee_name asc",
# 	)


# def get_date_list(from_date, to_date):
# 	days = date_diff(to_date, from_date)
# 	return [add_days(from_date, i) for i in range(days + 1)]


# def get_attendance_map(filters):
# 	attendance_filters = {
# 		"attendance_date": ["between", [filters.from_date, filters.to_date]],
# 		"docstatus": 1,
# 	}

# 	if filters.get("employee"):
# 		attendance_filters["employee"] = filters.employee

# 	attendance_list = frappe.get_all(
# 		"Attendance",
# 		filters=attendance_filters,
# 		fields=[
# 			"employee",
# 			"attendance_date",
# 			"status",
# 			"leave_type",
# 		],
# 	)

# 	attendance_map = {}

# 	for att in attendance_list:
# 		attendance_map[(att.employee, att.attendance_date)] = att

# 	return attendance_map


# def build_row(emp, day, bike_rate, attendance_map):
# 	day_start = get_datetime(f"{day} 00:00:00")
# 	day_end = get_datetime(f"{day} 23:59:59")

# 	attendance = attendance_map.get((emp.name, day))

# 	if attendance:

# 		status = attendance.status

# 		if status == "Weekly Off":
# 			display = "Weekly Off"

# 		elif status == "Holiday":
# 			display = "Holiday"

# 		elif status == "Restricted Holiday":

# 			holiday_list = frappe.db.get_value(
# 				"Holiday List Assignment",
# 				{
# 					"assigned_to": emp.name,
# 					"from_date": ["<=", day],
# 				},
# 				"holiday_list",
# 				order_by="from_date desc",
# 			)

# 			description = None

# 			if holiday_list:
# 				description = frappe.db.get_value(
# 					"Holiday",
# 					{
# 						"parent": holiday_list,
# 						"holiday_date": day,
# 					},
# 					"description",
# 				)

# 			display = description or "RH"

# 		elif status == "On Leave":
# 			display = attendance.leave_type

# 		else:
# 			display = None

# 		if display:
# 			return {
# 				"employee": emp.name,
# 				"employee_name": emp.employee_name,
# 				"date": formatdate(day, "dd/mm/yyyy"),
# 				"start_time": display,
# 				"end_time": display,
# 				"visit_points": display,
# 				"duration": display,
# 				"distance": display,
# 				"visit_type": display,
# 				"ta_da_mode": display,
# 				"tada_flat": display,
# 				"plant_vehicle_used": display,
# 				"total_ta_km": display,
# 				"photo_status": display,
# 			}

# 	start_rec = frappe.db.get_value(
# 		"Geolocation Tracking",
# 		{
# 			"employee": emp.name,
# 			"custom_type": "S",
# 			"timestamp": ["between", [day_start, day_end]],
# 		},
# 		["timestamp"],
# 		order_by="timestamp asc",
# 		as_dict=True,
# 	)

# 	end_rec = frappe.db.get_value(
# 		"Geolocation Tracking",
# 		{
# 			"employee": emp.name,
# 			"custom_type": "E",
# 			"timestamp": ["between", [day_start, day_end]],
# 		},
# 		["timestamp", "total_distance"],
# 		order_by="timestamp desc",
# 		as_dict=True,
# 	)

# 	start_time = start_rec.timestamp.strftime("%H:%M:%S") if start_rec and start_rec.timestamp else ""
# 	end_time = end_rec.timestamp.strftime("%H:%M:%S") if end_rec and end_rec.timestamp else ""

# 	distance = flt(end_rec.total_distance) if end_rec and end_rec.total_distance else 0.0

# 	duration = ""
# 	if start_rec and start_rec.timestamp and end_rec and end_rec.timestamp:
# 		diff_seconds = (end_rec.timestamp - start_rec.timestamp).total_seconds()
# 		if diff_seconds > 0:
# 			hh = int(diff_seconds // 3600)
# 			mm = int((diff_seconds % 3600) // 60)
# 			duration = "{:02d}:{:02d}".format(hh, mm)

# 	visit_type = "Up Country" if distance > 60 else "Local"

# 	# Fetch the whole day's Employee Activity list once - used for:
# 	#   - visit count (Society / New Visited Points)
# 	#   - TA/DA mode (custom_ta_da_mode on the FIRST record of the date)
# 	#   - photo status (any record before 07:00 with an attachment)
# 	day_activities = frappe.get_all(
# 		"Employee Activity",
# 		filters={
# 			"employee": emp.name,
# 			"request_date": ["between", [day_start, day_end]],
# 		},
# 		fields=["name", "request_date", "custom_ta_da_mode"],
# 		order_by="request_date asc",
# 	)

# 	visit_points = len(day_activities)

# 	cutoff_time = day_start + timedelta(hours=7)

# 	before_7am_visits = [
# 			d for d in day_activities
# 			if d.request_date and get_datetime(d.request_date) < cutoff_time
# 	]

# 	eligible_for_tada = (
# 			visit_points >= 2 and
# 			len(before_7am_visits) == 1
# 	)

# 	tada_flat = 0.0
# 	plant_vehicle_used = 0.0
# 	total_ta_km = 0.0
# 	ta_da_mode = ""

# 	if day_activities:
# 		ta_da_mode = day_activities[0].custom_ta_da_mode or ""

# 	if eligible_for_tada:
# 		is_low_grade = emp.grade in LOW_GRADES
# 		ta_mode = ta_da_mode

# 		if ta_mode == "Flat TA DA":
# 			if is_low_grade:
# 				tada_flat = 300 if visit_type == "Local" else 400
# 			else:
# 				tada_flat = 350 if visit_type == "Local" else 450

# 		elif ta_mode == "Used Official Vehicle":
# 			if is_low_grade:
# 				plant_vehicle_used = 150 if visit_type == "Local" else 200
# 			else:
# 				plant_vehicle_used = 175 if visit_type == "Local" else 225

# 		elif ta_mode == "TA DA as per Km":
# 			total_ta_km = flt(distance * bike_rate, 2)

# 	photo_status = get_photo_status(day_activities, day_start)

# 	return {
# 		"employee": emp.name,
# 		"employee_name": emp.employee_name,
# 		"date": formatdate(day, "dd/mm/yyyy"),
# 		"start_time": start_time,
# 		"end_time": end_time,
# 		"visit_points": visit_points,
# 		"duration": duration,
# 		"distance": flt(distance, 2),
# 		"visit_type": visit_type,
# 		"ta_da_mode": ta_da_mode,
# 		"tada_flat": tada_flat,
# 		"plant_vehicle_used": plant_vehicle_used,
# 		"total_ta_km": total_ta_km,
# 		"photo_status": photo_status,
# 	}


# def get_photo_status(day_activities, day_start):
# 	"""Uploaded if any Employee Activity before 07:00 AM on that date has an attachment."""
# 	cutoff = day_start + timedelta(hours=7)

# 	activities = [
# 		a for a in day_activities
# 		if a.request_date and get_datetime(a.request_date) <= cutoff
# 	]

# 	for activity in activities:
# 		has_attachment = frappe.db.exists(
# 			"File",
# 			{
# 				"attached_to_doctype": "Employee Activity",
# 				"attached_to_name": activity.name,
# 			},
# 		)
# 		if has_attachment:
# 			return _("Uploaded")

# 	return _("Not Uploaded")


# def clean_excel_value(value):
#     """
#     Convert HTML / Rich Text values into plain text
#     before writing them into Excel.
#     """

#     if not isinstance(value, str):
#         return value

#     if not value:
#         return value

#     # Convert HTML line breaks into actual new lines
#     value = re.sub(
#         r"<br\s*/?>",
#         "\n",
#         value,
#         flags=re.IGNORECASE
#     )

#     # Remove HTML tags
#     value = strip_html(value)

#     # Convert HTML entities
#     value = unescape(value)

#     # Replace non-breaking spaces
#     value = value.replace("\xa0", " ")

#     return value.strip()


# @frappe.whitelist()
# def export_excel_with_header(filters=None):
#     """
#     Export the FSR TA/DA report to Excel with:

#     - Dynamic branch location based on logged-in user
#     - Company header
#     - Applied filters
#     - Report data
#     - Grand total row
#     - HTML/Rich Text converted to plain text

#     This export does not affect the normal report view.
#     """

#     # ---------------------------------------------------------
#     # GET FILTERS
#     # ---------------------------------------------------------

#     if isinstance(filters, str):
#         filters = json.loads(filters)

#     filters = frappe._dict(filters or {})

#     # ---------------------------------------------------------
#     # VALIDATE FILTERS
#     # ---------------------------------------------------------

#     validate_filters(filters)

#     from_date = getdate(filters.from_date)
#     to_date = getdate(filters.to_date)

#     # ---------------------------------------------------------
#     # GET REPORT DATA
#     # ---------------------------------------------------------

#     columns, data = execute(filters)

#     # ---------------------------------------------------------
#     # CREATE EXCEL WORKBOOK
#     # ---------------------------------------------------------

#     output = io.BytesIO()

#     workbook = xlsxwriter.Workbook(
#         output,
#         {
#             "in_memory": True
#         }
#     )

#     worksheet = workbook.add_worksheet("FSR TA DA")

#     # ---------------------------------------------------------
#     # FORMATS
#     # ---------------------------------------------------------

#     company_format = workbook.add_format({
#         "bold": True,
#         "font_size": 14,
#         "align": "center",
#         "valign": "vcenter",
#     })

#     address_format = workbook.add_format({
#         "font_size": 11,
#         "align": "center",
#         "valign": "vcenter",
#     })

#     contact_format = workbook.add_format({
#         "font_size": 10,
#         "align": "center",
#         "valign": "vcenter",
#     })

#     title_format = workbook.add_format({
#         "bold": True,
#         "font_size": 12,
#         "align": "center",
#         "valign": "vcenter",
#     })

#     date_format = workbook.add_format({
#         "bold": True,
#         "font_size": 11,
#         "align": "center",
#         "valign": "vcenter",
#     })

#     filter_format = workbook.add_format({
#         "font_size": 10,
#         "align": "left",
#         "valign": "vcenter",
#         "text_wrap": True,
#     })

#     separator_format = workbook.add_format({
#         "bottom": 1,
#     })

#     column_header_format = workbook.add_format({
#         "bold": True,
#         "border": 1,
#         "align": "center",
#         "valign": "vcenter",
#         "text_wrap": True,
#     })

#     cell_format = workbook.add_format({
#         "border": 1,
#         "valign": "vcenter",
#     })

#     number_format = workbook.add_format({
#         "border": 1,
#         "valign": "vcenter",
#         "num_format": "0.00",
#     })

#     currency_format = workbook.add_format({
#         "border": 1,
#         "valign": "vcenter",
#         "num_format": "#,##0.00",
#     })

#     # ---------------------------------------------------------
#     # TOTAL FORMATS
#     # ---------------------------------------------------------

#     total_format = workbook.add_format({
#         "bold": True,
#         "border": 1,
#         "valign": "vcenter",
#     })

#     total_number_format = workbook.add_format({
#         "bold": True,
#         "border": 1,
#         "valign": "vcenter",
#         "num_format": "0.00",
#     })

#     total_currency_format = workbook.add_format({
#         "bold": True,
#         "border": 1,
#         "valign": "vcenter",
#         "num_format": "#,##0.00",
#     })

#     # ---------------------------------------------------------
#     # CHECK COLUMNS
#     # ---------------------------------------------------------

#     total_columns = len(columns)

#     if total_columns == 0:
#         workbook.close()
#         frappe.throw(_("No columns found for this report."))

#     last_column = total_columns - 1

#     # ---------------------------------------------------------
#     # GET LOGGED-IN USER BRANCH
#     # ---------------------------------------------------------

#     logged_in_user = frappe.session.user

#     user_branch = frappe.db.get_value(
#         "User",
#         logged_in_user,
#         "custom_branch"
#     )

#     # ---------------------------------------------------------
#     # DETERMINE BRANCH LOCATION
#     # ---------------------------------------------------------

#     branch_location = "Milk Plant, Cheshmashahi, Srinagar-190001"

#     if user_branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":
#         branch_location = "Milk Plant, Cheshmashahi, Srinagar-190001"
#     else:
#         branch_location = "Milk Plant, Satwari, Jammu-180004"

#     # if user_branch:
#     #     branch_value = str(user_branch).strip().lower()

#     #     if "jammu" in branch_value:
#     #         branch_location = "Satwari, Jammu-180004"

#     #     elif "srinagar" in branch_value:
#     #         branch_location = "Cheshmashahi, Srinagar-190001"

#     # ---------------------------------------------------------
#     # COMPANY HEADER
#     # ---------------------------------------------------------

#     worksheet.set_row(0, 24)
#     worksheet.set_row(1, 20)
#     worksheet.set_row(2, 20)
#     worksheet.set_row(4, 22)
#     worksheet.set_row(5, 20)

#     worksheet.merge_range(
#         0,
#         0,
#         0,
#         last_column,
#         "JAMMU & KASHMIR MILK PRODUCERS CO-OPERATIVE LIMITED",
#         company_format
#     )

#     # Dynamic branch/location
#     worksheet.merge_range(
#         1,
#         0,
#         1,
#         last_column,
#         branch_location,
#         address_format
#     )

#     worksheet.merge_range(
#         2,
#         0,
#         2,
#         last_column,
#         "Tele/Fax : 0194-2501786, Email: info@jkmpcl.coop",
#         contact_format
#     )

#     # ---------------------------------------------------------
#     # REPORT TITLE
#     # ---------------------------------------------------------

#     worksheet.merge_range(
#         4,
#         0,
#         4,
#         last_column,
#         "TA/DA Bill (for claim on fortnightly/monthly basis)",
#         title_format
#     )

#     worksheet.merge_range(
#         5,
#         0,
#         5,
#         last_column,
#         f"From {formatdate(from_date, 'dd/mm/yyyy')} "
#         f"To {formatdate(to_date, 'dd/mm/yyyy')}",
#         date_format
#     )

#     # ---------------------------------------------------------
#     # APPLIED FILTERS
#     # ---------------------------------------------------------

#     filter_values = []

#     employee = filters.get("employee")
#     branch = filters.get("branch")
#     from_date_filter = filters.get("from_date")
#     to_date_filter = filters.get("to_date")

#     # Employee filter
#     if employee:
#         employee_name = frappe.db.get_value(
#             "Employee",
#             employee,
#             "employee_name"
#         )

#         if employee_name:
#             filter_values.append(
#                 f"Employee: {employee_name} ({employee})"
#             )
#         else:
#             filter_values.append(
#                 f"Employee: {employee}"
#             )

#     # Branch filter
#     if branch:
#         filter_values.append(
#             f"Branch: {branch}"
#         )

#     # From Date filter
#     if from_date_filter:
#         filter_values.append(
#             f"From Date: "
#             f"{formatdate(from_date_filter, 'dd/mm/yyyy')}"
#         )

#     # To Date filter
#     if to_date_filter:
#         filter_values.append(
#             f"To Date: "
#             f"{formatdate(to_date_filter, 'dd/mm/yyyy')}"
#         )

#     # ---------------------------------------------------------
#     # WRITE APPLIED FILTERS
#     # ---------------------------------------------------------

#     worksheet.write(
#         6,
#         0,
#         "Applied Filters:",
#         filter_format
#     )

#     worksheet.merge_range(
#         6,
#         1,
#         6,
#         last_column,
#         " | ".join(filter_values)
#         if filter_values
#         else "All",
#         filter_format
#     )

#     worksheet.set_row(6, 30)

#     # ---------------------------------------------------------
#     # SEPARATOR
#     # ---------------------------------------------------------

#     for col_idx in range(total_columns):
#         worksheet.write_blank(
#             7,
#             col_idx,
#             None,
#             separator_format
#         )

#     # ---------------------------------------------------------
#     # REPORT TABLE START
#     #
#     # Excel row 9 = zero-based row 8
#     # ---------------------------------------------------------

#     start_row = 8

#     # ---------------------------------------------------------
#     # COLUMN HEADERS
#     # ---------------------------------------------------------

#     for col_idx, column in enumerate(columns):

#         if isinstance(column, dict):
#             label = (
#                 column.get("label")
#                 or column.get("fieldname")
#                 or ""
#             )
#         else:
#             label = str(column)

#         worksheet.write(
#             start_row,
#             col_idx,
#             label,
#             column_header_format
#         )

#     # ---------------------------------------------------------
#     # GRAND TOTAL VARIABLES
#     # ---------------------------------------------------------

#     grand_totals = {
#         "visit_points": 0,
#         "distance": 0.0,
#         "tada_flat": 0.0,
#         "plant_vehicle_used": 0.0,
#         "total_ta_km": 0.0,
#     }

#     # ---------------------------------------------------------
#     # WRITE REPORT DATA
#     # ---------------------------------------------------------

#     for row_idx, row in enumerate(data, start=1):

#         excel_row = start_row + row_idx

#         for col_idx, column in enumerate(columns):

#             if isinstance(column, dict):
#                 fieldname = column.get("fieldname")
#                 fieldtype = column.get("fieldtype")
#             else:
#                 fieldname = None
#                 fieldtype = None

#             value = ""

#             # -------------------------------------------------
#             # GET VALUE FROM ROW
#             # -------------------------------------------------

#             if isinstance(row, dict):

#                 if fieldname:
#                     value = row.get(
#                         fieldname,
#                         ""
#                     )

#             elif isinstance(row, (list, tuple)):

#                 if col_idx < len(row):
#                     value = row[col_idx]

#             # -------------------------------------------------
#             # CALCULATE GRAND TOTALS
#             # -------------------------------------------------

#             if isinstance(row, dict):

#                 if fieldname == "visit_points":
#                     grand_totals["visit_points"] += cint(
#                         row.get("visit_points") or 0
#                     )

#                 elif fieldname == "distance":
#                     grand_totals["distance"] += flt(
#                         row.get("distance") or 0
#                     )

#                 elif fieldname == "tada_flat":
#                     grand_totals["tada_flat"] += flt(
#                         row.get("tada_flat") or 0
#                     )

#                 elif fieldname == "plant_vehicle_used":
#                     grand_totals["plant_vehicle_used"] += flt(
#                         row.get("plant_vehicle_used") or 0
#                     )

#                 elif fieldname == "total_ta_km":
#                     grand_totals["total_ta_km"] += flt(
#                         row.get("total_ta_km") or 0
#                     )

#             # -------------------------------------------------
#             # CLEAN HTML / RICH TEXT
#             # -------------------------------------------------

#             value = clean_excel_value(value)

#             if value is None:
#                 value = ""

#             # -------------------------------------------------
#             # SELECT NORMAL CELL FORMAT
#             # -------------------------------------------------

#             if fieldtype == "Currency":

#                 format_to_use = currency_format

#             elif fieldtype == "Float":

#                 format_to_use = number_format

#             elif fieldtype in ("Int", "Check"):

#                 format_to_use = cell_format

#             else:

#                 format_to_use = cell_format

#             # -------------------------------------------------
#             # WRITE NORMAL DATA
#             # -------------------------------------------------

#             worksheet.write(
#                 excel_row,
#                 col_idx,
#                 value,
#                 format_to_use
#             )

#     # ---------------------------------------------------------
#     # GRAND TOTAL ROW
#     # ---------------------------------------------------------

#     total_row = start_row + len(data) + 1

#     for col_idx, column in enumerate(columns):

#         if isinstance(column, dict):
#             fieldname = column.get("fieldname")
#             fieldtype = column.get("fieldtype")
#         else:
#             fieldname = None
#             fieldtype = None

#         # -----------------------------------------------------
#         # TOTAL VALUE
#         # -----------------------------------------------------

#         if col_idx == 0:

#             value = "TOTAL"

#         elif fieldname == "visit_points":

#             value = grand_totals["visit_points"]

#         elif fieldname == "distance":

#             value = round(
#                 grand_totals["distance"],
#                 2
#             )

#         elif fieldname == "tada_flat":

#             value = round(
#                 grand_totals["tada_flat"],
#                 2
#             )

#         elif fieldname == "plant_vehicle_used":

#             value = round(
#                 grand_totals["plant_vehicle_used"],
#                 2
#             )

#         elif fieldname == "total_ta_km":

#             value = round(
#                 grand_totals["total_ta_km"],
#                 2
#             )

#         else:

#             value = ""

#         # -----------------------------------------------------
#         # TOTAL ROW FORMAT
#         # -----------------------------------------------------

#         if fieldtype == "Currency":

#             format_to_use = total_currency_format

#         elif fieldtype == "Float":

#             format_to_use = total_number_format

#         elif fieldtype in ("Int", "Check"):

#             format_to_use = total_format

#         else:

#             format_to_use = total_format

#         # -----------------------------------------------------
#         # WRITE TOTAL CELL
#         # -----------------------------------------------------

#         worksheet.write(
#             total_row,
#             col_idx,
#             value,
#             format_to_use
#         )

#     # ---------------------------------------------------------
#     # TOTAL ROW HEIGHT
#     # ---------------------------------------------------------

#     worksheet.set_row(
#         total_row,
#         22
#     )

#     # ---------------------------------------------------------
#     # COLUMN WIDTHS
#     # ---------------------------------------------------------

#     for col_idx, column in enumerate(columns):

#         width = 15

#         if isinstance(column, dict):

#             width = column.get("width") or 15

#             try:
#                 width = int(width / 7)
#             except (TypeError, ValueError):
#                 width = 15

#             width = max(
#                 10,
#                 min(width, 40)
#             )

#         worksheet.set_column(
#             col_idx,
#             col_idx,
#             width
#         )

#     # ---------------------------------------------------------
#     # FREEZE REPORT HEADER
#     # ---------------------------------------------------------

#     worksheet.freeze_panes(
#         start_row + 1,
#         0
#     )

#     # ---------------------------------------------------------
#     # PRINT SETTINGS
#     # ---------------------------------------------------------

#     worksheet.set_landscape()

#     worksheet.fit_to_pages(
#         1,
#         0
#     )

#     worksheet.set_margins(
#         left=0.25,
#         right=0.25,
#         top=0.50,
#         bottom=0.50
#     )

#     # ---------------------------------------------------------
#     # REPEAT COLUMN HEADER ON EVERY PRINTED PAGE
#     # ---------------------------------------------------------

#     worksheet.repeat_rows(
#         start_row,
#         start_row
#     )

#     # ---------------------------------------------------------
#     # PAGE FOOTER
#     # ---------------------------------------------------------

#     worksheet.set_footer(
#         "&CPage &P of &N"
#     )

#     # ---------------------------------------------------------
#     # PRINT AREA
#     # ---------------------------------------------------------

#     worksheet.print_area(
#         0,
#         0,
#         total_row,
#         last_column
#     )

#     # ---------------------------------------------------------
#     # CLOSE WORKBOOK
#     # ---------------------------------------------------------

#     workbook.close()

#     output.seek(0)

#     # ---------------------------------------------------------
#     # FILE NAME
#     # ---------------------------------------------------------

#     filename = (
#         f"FSR_Report_"
#         f"({formatdate(from_date, 'dd-mm-yyyy')}-"
#         f"{formatdate(to_date, 'dd-mm-yyyy')}).xlsx"
#     )

#     # ---------------------------------------------------------
#     # SEND FILE TO BROWSER
#     # ---------------------------------------------------------

#     frappe.response["filename"] = filename
#     frappe.response["filecontent"] = output.getvalue()
#     frappe.response["type"] = "binary"





























# FSR - Field Staff TA/DA Report
#
# ASSUMPTIONS (adjust field names below to match your actual site schema
# if they differ):
#   - Employee.grade (Link "Employee Grade") is matched against the
#     "Flat TA DA Setting" child table (see below) - no more hardcoded
#     slabs. NOTE: this single table (grade, local_rate, up_country_rate,
#     effective_date) is used to resolve BOTH "Flat TA DA" and "Used
#     Official Vehicle" amounts, since only one grade-rate table exists.
#     If you later want distinct rates per mode, add a second child table
#     (e.g. "Used Official Vehicle Setting") with the same shape and split
#     get_grade_rate() below accordingly.
#   - Employee.department (Link "Department") is matched against the
#     "TA DA Department Wise Time" child table (see below) - no more
#     hardcoded 07:00 AM cutoff.
#   - Employee.branch is used for the Branch filter.
#   - Geolocation Tracking has: employee (Link Employee), timestamp (Datetime),
#     custom_type (Select: S / E), total_distance (Float).
#   - Employee Activity has: employee (Link Employee), request_date (Datetime),
#     custom_ta_da_mode (Select: "Flat TA DA" / "Used Official Vehicle" /
#     "TA DA as per Km"). The FIRST Employee Activity record of the date
#     (by request_date ascending) decides the TA/DA mode for that day.
#   - HR Settings (Single) has:
#       - custom_bike_rate_per_km (Float) - used for "TA DA as per Km".
#       - a Table field (assumed attached to HR Settings; adjust the
#         `parenttype` filters below if you attached it elsewhere) pointing
#         at child doctype "Flat TA DA Setting":
#           grade (Link Employee Grade), local_rate (Data - numeric text),
#           up_country_rate (Data - numeric text), effective_date (Date).
#       - a Table field pointing at child doctype
#         "TA DA Department Wise Time":
#           department (Link Department),
#           time_before_activity_to_be_performed (Time),
#           effective_date (Date).
#     For both tables, the applicable row for a given date is the one with
#     the latest effective_date that is <= the date being evaluated.
#   - Attendance has: employee, attendance_date, status (includes
#     "Weekly Off" / "Holiday" / "Restricted Holiday" / "On Leave"),
#     leave_type.
#   - "Holiday List Assignment" has: assigned_to (Link Employee), from_date,
#     holiday_list (Link Holiday List). Holiday List has child table
#     "holidays" (doctype "Holiday") with holiday_date, description.

import json
import io
import xlsxwriter
import frappe
import re
from html import unescape
from frappe import _
from frappe.utils import (
	flt,
	cint,
	getdate,
	nowdate,
	get_datetime,
	get_time,
	add_days,
	date_diff,
	formatdate,
	strip_html,
)
from datetime import datetime, timedelta, time as dtime


DEFAULT_CUTOFF_TIME = dtime(7, 0)  # fallback if no department config matches

def execute(filters=None):
    filters = frappe._dict(filters or {})

    if not filters.get("from_date"):
        frappe.throw(
            _("From Date is mandatory. Please select From Date.")
        )

    if not filters.get("to_date"):
        frappe.throw(
            _("To Date is mandatory. Please select To Date.")
        )

    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def validate_filters(filters):
    today = getdate(nowdate())

    from_date = getdate(filters.from_date)
    to_date = getdate(filters.to_date)

    # Neither filter is allowed to be a future date
    if from_date > today:
        from_date = today

    if to_date > today:
        to_date = today

    # From Date cannot be greater than To Date
    if from_date > to_date:
        frappe.throw(
            _("From Date cannot be greater than To Date.")
        )

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

	# bike_rate = flt(frappe.db.get_single_value("HR Settings", "custom_bike_rate_per_km")) or 0
	date_list = get_date_list(filters.from_date, filters.to_date)
	attendance_map = get_attendance_map(filters)

	# Per-request caches so the same grade/department config isn't re-queried
	# for every single employee/day combination.
	rate_cache = {}
	cutoff_cache = {}
	bike_rate_cache = {}

	out = []
	for emp in employees:
		emp_rows = []

		for day in date_list:
			row = build_row(emp, day, attendance_map, rate_cache, cutoff_cache, bike_rate_cache)
			emp_rows.append(row)

		out.extend(emp_rows)

	return out


def get_user_permitted_branch():
	"""
	Returns the branch the current user should be restricted to, or None
	if the user has full/all-branch access (e.g. System Manager, HR Manager).
	"""
	user = frappe.session.user

	if user == "Administrator":
		return None

	return frappe.db.get_value("User", user, "custom_branch")


def get_employees(filters):
	emp_filters = {"status": "Active"}

	user_branch = get_user_permitted_branch()

	if user_branch:
		emp_filters["branch"] = user_branch
	elif filters.get("branch"):
		emp_filters["branch"] = filters.branch

	if filters.get("employee"):
		emp_filters["name"] = filters.employee

	return frappe.get_all(
		"Employee",
		filters=emp_filters,
		fields=["name", "employee_name", "grade", "department", "branch"],
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


def get_grade_rate(grade, visit_type, on_date, rate_cache):
	"""
	Looks up "Flat TA DA Setting" (HR Settings child table) for the given
	grade, and returns local_rate or up_country_rate (depending on
	visit_type) from the row whose effective_date is the latest one
	<= on_date. Returns 0 if nothing configured / matches (no hardcoded
	fallback).

	Used for BOTH "Flat TA DA" and "Used Official Vehicle" modes, since
	only one grade-rate table exists - see the note at the top of this file.
	"""
	if not grade:
		return 0.0

	if grade not in rate_cache:
		rate_cache[grade] = frappe.get_all(
			"Flat TA DA Setting",
			filters={
				"grade": grade,
				"parenttype": "HR Settings",
			},
			fields=["grade", "local_rate", "up_country_rate", "effective_date"],
			order_by="effective_date desc",
		)

	on_date = getdate(on_date)
	for row in rate_cache[grade]:
		if row.effective_date and getdate(row.effective_date) <= on_date:
			value = row.local_rate if visit_type == "Local" else row.up_country_rate
			return flt(value)

	return 0.0


def get_bike_rate(on_date, bike_rate_cache):
	"""
	Returns the applicable Bike Rate from the HR Settings
	'Bike Rate' child table.

	The applicable row is the row whose Effective Date is
	the latest date that is <= the date being evaluated.

	Returns 0 if no applicable rate is found.
	"""

	if "rates" not in bike_rate_cache:
		bike_rate_cache["rates"] = frappe.get_all(
			"Bike Rate",
			filters={
				"parenttype": "HR Settings",
			},
			fields=[
				"bike_rate",
				"effective_date",
			],
			order_by="effective_date desc",
		)

	on_date = getdate(on_date)

	for row in bike_rate_cache["rates"]:
		if (
			row.effective_date
			and getdate(row.effective_date) <= on_date
		):
			return flt(row.bike_rate)

	return 0.0


# def get_department_cutoff(department, on_date, cutoff_cache):
# 	"""
# 	Looks up "TA DA Department Wise Time" (HR Settings child table) for the
# 	given department, and returns time_before_activity_to_be_performed from
# 	the row whose effective_date is the latest one <= on_date. Falls back
# 	to DEFAULT_CUTOFF_TIME (07:00) if no department, or nothing configured
# 	for it / matches.
# 	"""
# 	if not department:
# 		return DEFAULT_CUTOFF_TIME

# 	if department not in cutoff_cache:
# 		cutoff_cache[department] = frappe.get_all(
# 			"TA DA Department Wise Time",
# 			filters={
# 				"department": department,
# 				"parenttype": "HR Settings",
# 			},
# 			fields=["time_before_activity_to_be_performed", "effective_date"],
# 			order_by="effective_date desc",
# 		)

# 	on_date = getdate(on_date)
# 	for row in cutoff_cache[department]:
# 		if (
# 			row.effective_date
# 			and getdate(row.effective_date) <= on_date
# 			and row.time_before_activity_to_be_performed
# 		):
# 			return get_time(row.time_before_activity_to_be_performed)

# 	return DEFAULT_CUTOFF_TIME


def get_department_cutoff(department, on_date, cutoff_cache):
	"""
	First checks "TA DA Department Wise Time" for the given department.

	If a matching department row exists with effective_date <= on_date,
	that configured time is used.

	If no matching department configuration exists, falls back to
	HR Settings.custom_general_department_activity_log_time.

	If the HR Settings field is also empty, falls back to the existing
	DEFAULT_CUTOFF_TIME (07:00 AM).
	"""
	if department not in cutoff_cache:
		cutoff_cache[department] = frappe.get_all(
			"TA DA Department Wise Time",
			filters={
				"department": department,
				"parenttype": "HR Settings",
			},
			fields=["time_before_activity_to_be_performed", "effective_date"],
			order_by="effective_date desc",
		)

	on_date = getdate(on_date)

	# ---------------------------------------------------------
	# FIRST PRIORITY:
	# Department Wise TA DA configuration
	# ---------------------------------------------------------
	for row in cutoff_cache[department]:
		if (
			row.effective_date
			and getdate(row.effective_date) <= on_date
			and row.time_before_activity_to_be_performed
		):
			return get_time(row.time_before_activity_to_be_performed)

	# ---------------------------------------------------------
	# SECOND PRIORITY:
	# General cutoff time from HR Settings
	# ---------------------------------------------------------
	general_cutoff = frappe.db.get_single_value(
		"HR Settings",
		"custom_general_department_activity_log_time",
	)

	if general_cutoff:
		return get_time(general_cutoff)

	# ---------------------------------------------------------
	# FINAL FALLBACK:
	# Existing 07:00 AM default
	# ---------------------------------------------------------
	return DEFAULT_CUTOFF_TIME


def build_row(emp, day, attendance_map, rate_cache, cutoff_cache, bike_rate_cache):
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
	#   - photo status (any record before the department cutoff with an
	#     attachment)
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

	# The date used to resolve which config row (grade rate / department
	# cutoff) applies - the first activity's date if there is one, else the
	# report date itself.
	effective_on_date = day_activities[0].request_date if day_activities else day

	cutoff_t = get_department_cutoff(emp.department, effective_on_date, cutoff_cache)
	cutoff_dt = day_start.replace(hour=cutoff_t.hour, minute=cutoff_t.minute, second=cutoff_t.second)

	before_cutoff_visits = [
		d for d in day_activities
		if d.request_date and get_datetime(d.request_date) < cutoff_dt
	]

	eligible_for_tada = (
		visit_points >= 2 and
		len(before_cutoff_visits) == 1
	)

	tada_flat = 0.0
	plant_vehicle_used = 0.0
	total_ta_km = 0.0
	ta_da_mode = ""

	if day_activities:
		ta_da_mode = day_activities[0].custom_ta_da_mode or ""

	if eligible_for_tada:
		ta_mode = ta_da_mode

		if ta_mode == "Flat TA DA":
			tada_flat = get_grade_rate(emp.grade, visit_type, effective_on_date, rate_cache)

		elif ta_mode == "Used Official Vehicle":
			plant_vehicle_used = flt(get_grade_rate(emp.grade, visit_type, effective_on_date, rate_cache) / 2, 2)

		elif ta_mode == "TA DA as per Km":
			bike_rate = get_bike_rate(effective_on_date, bike_rate_cache)
			total_ta_km = flt(distance * bike_rate, 2)

	photo_status = get_photo_status(day_activities, cutoff_dt)

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


def get_photo_status(day_activities, cutoff_dt):
	"""
	Uploaded if any Employee Activity before the (department-configured)
	cutoff time on that date has an attachment.
	"""
	activities = [
		a for a in day_activities
		if a.request_date and get_datetime(a.request_date) <= cutoff_dt
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


def clean_excel_value(value):
	"""
	Convert HTML / Rich Text values into plain text
	before writing them into Excel.
	"""

	if not isinstance(value, str):
		return value

	if not value:
		return value

	# Convert HTML line breaks into actual new lines
	value = re.sub(
		r"<br\s*/?>",
		"\n",
		value,
		flags=re.IGNORECASE,
	)

	# Remove HTML tags
	value = strip_html(value)

	# Convert HTML entities
	value = unescape(value)

	# Replace non-breaking spaces
	value = value.replace("\xa0", " ")

	return value.strip()


@frappe.whitelist()
def export_excel_with_header(filters=None):
	"""
	Export the FSR TA/DA report to Excel with:

	- Dynamic branch location based on logged-in user
	- Company header
	- Applied filters
	- Report data
	- Grand total row
	- HTML/Rich Text converted to plain text

	This export does not affect the normal report view.
	"""

	# ---------------------------------------------------------
	# GET FILTERS
	# ---------------------------------------------------------

	if isinstance(filters, str):
		filters = json.loads(filters)

	filters = frappe._dict(filters or {})

	if not filters.get("from_date"):
		frappe.throw(
			_("From Date is mandatory. Please select From Date.")
		)
			
	if not filters.get("to_date"):
		frappe.throw(
			_("To Date is mandatory. Please select To Date.")
		)

	# ---------------------------------------------------------
	# VALIDATE FILTERS
	# ---------------------------------------------------------

	validate_filters(filters)

	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)

	# ---------------------------------------------------------
	# GET REPORT DATA
	# ---------------------------------------------------------

	columns, data = execute(filters)

	# ---------------------------------------------------------
	# CREATE EXCEL WORKBOOK
	# ---------------------------------------------------------

	output = io.BytesIO()

	workbook = xlsxwriter.Workbook(
		output,
		{
			"in_memory": True,
		},
	)

	worksheet = workbook.add_worksheet("FSR TA DA")

	# ---------------------------------------------------------
	# FORMATS
	# ---------------------------------------------------------

	company_format = workbook.add_format({
		"bold": True,
		"font_size": 14,
		"align": "center",
		"valign": "vcenter",
	})

	address_format = workbook.add_format({
		"font_size": 11,
		"align": "center",
		"valign": "vcenter",
	})

	contact_format = workbook.add_format({
		"font_size": 10,
		"align": "center",
		"valign": "vcenter",
	})

	title_format = workbook.add_format({
		"bold": True,
		"font_size": 12,
		"align": "center",
		"valign": "vcenter",
	})

	date_format = workbook.add_format({
		"bold": True,
		"font_size": 11,
		"align": "center",
		"valign": "vcenter",
	})

	filter_format = workbook.add_format({
		"font_size": 10,
		"align": "left",
		"valign": "vcenter",
		"text_wrap": True,
	})

	separator_format = workbook.add_format({
		"bottom": 1,
	})

	column_header_format = workbook.add_format({
		"bold": True,
		"border": 1,
		"align": "center",
		"valign": "vcenter",
		"text_wrap": True,
	})

	cell_format = workbook.add_format({
		"border": 1,
		"valign": "vcenter",
	})

	number_format = workbook.add_format({
		"border": 1,
		"valign": "vcenter",
		"num_format": "0.00",
	})

	currency_format = workbook.add_format({
		"border": 1,
		"valign": "vcenter",
		"num_format": "#,##0.00",
	})

	# ---------------------------------------------------------
	# TOTAL FORMATS
	# ---------------------------------------------------------

	total_format = workbook.add_format({
		"bold": True,
		"border": 1,
		"valign": "vcenter",
	})

	total_number_format = workbook.add_format({
		"bold": True,
		"border": 1,
		"valign": "vcenter",
		"num_format": "0.00",
	})

	total_currency_format = workbook.add_format({
		"bold": True,
		"border": 1,
		"valign": "vcenter",
		"num_format": "#,##0.00",
	})

	# ---------------------------------------------------------
	# CHECK COLUMNS
	# ---------------------------------------------------------

	total_columns = len(columns)

	if total_columns == 0:
		workbook.close()
		frappe.throw(_("No columns found for this report."))

	last_column = total_columns - 1

	# ---------------------------------------------------------
	# GET LOGGED-IN USER BRANCH
	# ---------------------------------------------------------

	logged_in_user = frappe.session.user

	user_branch = frappe.db.get_value(
		"User",
		logged_in_user,
		"custom_branch",
	)

	# ---------------------------------------------------------
	# DETERMINE BRANCH LOCATION
	# ---------------------------------------------------------

	branch_location = "Milk Plant, Cheshmashahi, Srinagar-190001"

	if user_branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":
		branch_location = "Milk Plant, Cheshmashahi, Srinagar-190001"
	else:
		branch_location = "Milk Plant, Satwari, Jammu-180004"

  	# ---------------------------------------------------------
	# HEADER FORMATS
	# ---------------------------------------------------------

	header_company_format = workbook.add_format({
		"bold": True,
		"font_name": "Courier New",
		"font_size": 14,
		"align": "center",
		"valign": "vcenter",
	})

	header_address_format = workbook.add_format({
		"font_name": "Courier New",
		"font_size": 11,
		"align": "center",
		"valign": "vcenter",
	})

	header_contact_format = workbook.add_format({
		"font_name": "Courier New",
		"font_size": 10,
		"align": "center",
		"valign": "vcenter",
	})

	header_title_format = workbook.add_format({
		"bold": True,
		"font_name": "Courier New",
		"font_size": 11,
		"align": "center",
		"valign": "vcenter",
	})

	header_separator_format = workbook.add_format({
		"font_name": "Courier New",
		"font_size": 10,
		"align": "left",
		"valign": "vcenter",
	})

	# ---------------------------------------------------------
	# COMPANY HEADER
	# ---------------------------------------------------------

	worksheet.set_row(0, 28)
	worksheet.set_row(1, 22)
	worksheet.set_row(2, 22)
	worksheet.set_row(3, 22)
	worksheet.set_row(4, 18)

	worksheet.merge_range(
		0, 0, 0, last_column,
		"JAMMU & KASHMIR MILK PRODUCERS CO-OPERATIVE LIMITED",
		header_company_format,
	)

	# Dynamic branch/location
	worksheet.merge_range(
		1, 0, 1, last_column,
		branch_location,
		header_address_format,
	)

	worksheet.merge_range(
		2, 0, 2, last_column,
		"Tele/Fax : 0194-2501786, Email: info@jkmpcl.coop",
		header_contact_format,
	)

	# ---------------------------------------------------------
	# REPORT TITLE
	# ---------------------------------------------------------

	worksheet.merge_range(
		3,
		0,
		3,
		last_column,
		(
			"TA/DA Bill (for claim on fortnightly/monthly basis)    "
			f"From {formatdate(from_date, 'dd/mm/yyyy')} "
			f"To {formatdate(to_date, 'dd/mm/yyyy')}"
		),
		header_title_format
	)

	separator_text = "-" * 150

	worksheet.merge_range(
		4,
		0,
		4,
		last_column,
		separator_text,
		header_separator_format
	)

	# ---------------------------------------------------------
	# INSERT COMPANY LOGO
	# ---------------------------------------------------------

	logo_path = frappe.get_app_path(
		"jkmpcl_hr",
		"public",
		"comp_logo",
		"JKMPCL.png"
	)

	worksheet.insert_image(
		0,
		0,
		logo_path,
		{
			"x_scale": 0.18,
			"y_scale": 0.18,
			"x_offset": 12,
			"y_offset": 10,
			"object_position": 2,
		}
	)

	# ---------------------------------------------------------
	# APPLIED FILTERS
	# ---------------------------------------------------------

	filter_values = []

	employee = filters.get("employee")
	branch = filters.get("branch")
	from_date_filter = filters.get("from_date")
	to_date_filter = filters.get("to_date")

	if employee:
		employee_name = frappe.db.get_value(
			"Employee",
			employee,
			"employee_name",
		)

		if employee_name:
			filter_values.append(f"Employee: {employee_name} ({employee})")
		else:
			filter_values.append(f"Employee: {employee}")

	if branch:
		filter_values.append(f"Branch: {branch}")

	if from_date_filter:
		filter_values.append(f"From Date: {formatdate(from_date_filter, 'dd/mm/yyyy')}")

	if to_date_filter:
		filter_values.append(f"To Date: {formatdate(to_date_filter, 'dd/mm/yyyy')}")

	# ---------------------------------------------------------
	# WRITE APPLIED FILTERS
	# ---------------------------------------------------------

	worksheet.write(5, 0, "Applied Filters:", filter_format)

	worksheet.merge_range(
		5, 1, 5, last_column,
		" | ".join(filter_values) if filter_values else "All",
		filter_format,
	)

	worksheet.set_row(5, 30)

	# ---------------------------------------------------------
	# SEPARATOR
	# ---------------------------------------------------------

	for col_idx in range(total_columns):
		worksheet.write_blank(6, col_idx, None, separator_format)

	# ---------------------------------------------------------
	# REPORT TABLE START (Excel row 9 = zero-based row 8)
	# ---------------------------------------------------------

	start_row = 7

	# ---------------------------------------------------------
	# COLUMN HEADERS
	# ---------------------------------------------------------

	for col_idx, column in enumerate(columns):
		if isinstance(column, dict):
			label = column.get("label") or column.get("fieldname") or ""
		else:
			label = str(column)

		worksheet.write(start_row, col_idx, label, column_header_format)

	# ---------------------------------------------------------
	# GRAND TOTAL VARIABLES
	# ---------------------------------------------------------

	grand_totals = {
		"visit_points": 0,
		"distance": 0.0,
		"tada_flat": 0.0,
		"plant_vehicle_used": 0.0,
		"total_ta_km": 0.0,
	}

	# ---------------------------------------------------------
	# WRITE REPORT DATA
	# ---------------------------------------------------------

	for row_idx, row in enumerate(data, start=1):

		excel_row = start_row + row_idx

		for col_idx, column in enumerate(columns):

			if isinstance(column, dict):
				fieldname = column.get("fieldname")
				fieldtype = column.get("fieldtype")
			else:
				fieldname = None
				fieldtype = None

			value = ""

			if isinstance(row, dict):
				if fieldname:
					value = row.get(fieldname, "")
			elif isinstance(row, (list, tuple)):
				if col_idx < len(row):
					value = row[col_idx]

			if isinstance(row, dict):
				if fieldname == "visit_points":
					grand_totals["visit_points"] += cint(row.get("visit_points") or 0)
				elif fieldname == "distance":
					grand_totals["distance"] += flt(row.get("distance") or 0)
				elif fieldname == "tada_flat":
					grand_totals["tada_flat"] += flt(row.get("tada_flat") or 0)
				elif fieldname == "plant_vehicle_used":
					grand_totals["plant_vehicle_used"] += flt(row.get("plant_vehicle_used") or 0)
				elif fieldname == "total_ta_km":
					grand_totals["total_ta_km"] += flt(row.get("total_ta_km") or 0)

			value = clean_excel_value(value)

			if value is None:
				value = ""

			if fieldtype == "Currency":
				format_to_use = currency_format
			elif fieldtype == "Float":
				format_to_use = number_format
			elif fieldtype in ("Int", "Check"):
				format_to_use = cell_format
			else:
				format_to_use = cell_format

			worksheet.write(excel_row, col_idx, value, format_to_use)

	# ---------------------------------------------------------
	# GRAND TOTAL ROW
	# ---------------------------------------------------------

	total_row = start_row + len(data) + 1

	for col_idx, column in enumerate(columns):

		if isinstance(column, dict):
			fieldname = column.get("fieldname")
			fieldtype = column.get("fieldtype")
		else:
			fieldname = None
			fieldtype = None

		if col_idx == 0:
			value = "TOTAL"
		elif fieldname == "visit_points":
			value = grand_totals["visit_points"]
		elif fieldname == "distance":
			value = round(grand_totals["distance"], 2)
		elif fieldname == "tada_flat":
			value = round(grand_totals["tada_flat"], 2)
		elif fieldname == "plant_vehicle_used":
			value = round(grand_totals["plant_vehicle_used"], 2)
		elif fieldname == "total_ta_km":
			value = round(grand_totals["total_ta_km"], 2)
		else:
			value = ""

		if fieldtype == "Currency":
			format_to_use = total_currency_format
		elif fieldtype == "Float":
			format_to_use = total_number_format
		elif fieldtype in ("Int", "Check"):
			format_to_use = total_format
		else:
			format_to_use = total_format

		worksheet.write(total_row, col_idx, value, format_to_use)

	worksheet.set_row(total_row, 22)

	# ---------------------------------------------------------
	# COLUMN WIDTHS
	# ---------------------------------------------------------

	for col_idx, column in enumerate(columns):

		width = 15

		if isinstance(column, dict):

			width = column.get("width") or 15

			try:
				width = int(width / 7)
			except (TypeError, ValueError):
				width = 15

			width = max(10, min(width, 40))

		# -----------------------------------------------------
		# Do not overwrite logo column widths
		# -----------------------------------------------------

		if col_idx == 0:
			width = 12

		elif col_idx == 1:
			width = 12

		worksheet.set_column(
			col_idx,
			col_idx,
			width
		)

	# ---------------------------------------------------------
	# FREEZE / PRINT SETTINGS
	# ---------------------------------------------------------

	# worksheet.freeze_panes(start_row + 1, 0)
	worksheet.print_area(
		0,
		0,
		total_row,
		last_column
	)

	worksheet.set_landscape()
	worksheet.fit_to_pages(1, 0)
	worksheet.set_margins(left=0.25, right=0.25, top=0.50, bottom=0.50)
	worksheet.repeat_rows(start_row, start_row)
	worksheet.set_footer("&CPage &P of &N")
	worksheet.print_area(0, 0, total_row, last_column)

	workbook.close()
	output.seek(0)

	filename = (
		f"FSR_Report_"
		f"({formatdate(from_date, 'dd-mm-yyyy')}-"
		f"{formatdate(to_date, 'dd-mm-yyyy')}).xlsx"
	)

	frappe.response["filename"] = filename
	frappe.response["filecontent"] = output.getvalue()
	frappe.response["type"] = "binary"