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

import json
import io
import xlsxwriter
import frappe
import re
from html import unescape
from frappe import _
from frappe.utils import getdate, formatdate, add_days, date_diff, get_datetime, flt, cstr, strip_html


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

def get_user_permitted_branch():
	"""
	Returns the branch the current user should be restricted to, or None
	if the user has full/all-branch access (e.g. System Manager, HR Manager).

	Adjust `full_access_roles` to match whichever roles in your system are
	meant to see all branches.
	"""
	user = frappe.session.user

	if user == "Administrator":
		return None

	return frappe.db.get_value("User", user, "custom_branch")


def get_employees(filters):
	conditions = {}

	if filters.get("employee"):
		conditions["name"] = filters.get("employee")

	user_branch = get_user_permitted_branch()

	if user_branch:
		conditions["branch"] = user_branch
	elif filters.get("branch"):
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


def clean_excel_value(value):
    """
    Convert HTML / Rich Text values into plain text before writing to Excel.
    (Not used for the 'photos' column - see extract_photo_links below.)
    """
    if not isinstance(value, str):
        return value

    if not value:
        return value

    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = strip_html(value)
    value = unescape(value)
    value = value.replace("\xa0", " ")

    return value.strip()


def get_photo_export_status(value):
    """
    The 'photos' column stores <a href="..."> View Image </a> tags when a
    photo was attached, or an empty string when none was uploaded.
    For the Excel export, show a simple status instead of raw links.
    """
    if isinstance(value, str) and "href=" in value:
        return _("Uploaded")

    return ""


@frappe.whitelist()
def export_excel_with_header(filters=None):
    """
    Export the DSR (Geo Tracking / Activity Log) report to Excel with:

    - Dynamic branch location based on logged-in user
    - Company header
    - Applied filters
    - Report data (Sub Total / Grand Total rows bolded)
    - HTML/Rich Text converted to plain text; photo links extracted as URLs

    This export does not affect the normal report view.
    """

    # ---------------------------------------------------------
    # GET / VALIDATE FILTERS
    # ---------------------------------------------------------

    if isinstance(filters, str):
        filters = json.loads(filters)

    filters = frappe._dict(filters or {})

    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))

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
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet("DSR Report")

    # ---------------------------------------------------------
    # FORMATS
    # ---------------------------------------------------------

    company_format = workbook.add_format({
        "bold": True, "font_size": 14, "align": "center", "valign": "vcenter",
    })
    address_format = workbook.add_format({
        "font_size": 11, "align": "center", "valign": "vcenter",
    })
    contact_format = workbook.add_format({
        "font_size": 10, "align": "center", "valign": "vcenter",
    })
    title_format = workbook.add_format({
        "bold": True, "font_size": 12, "align": "center", "valign": "vcenter",
    })
    date_format = workbook.add_format({
        "bold": True, "font_size": 11, "align": "center", "valign": "vcenter",
    })
    filter_format = workbook.add_format({
        "font_size": 10, "align": "left", "valign": "vcenter", "text_wrap": True,
    })
    separator_format = workbook.add_format({"bottom": 1})
    column_header_format = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True,
    })
    cell_format = workbook.add_format({"border": 1, "valign": "vcenter", "text_wrap": True})
    number_format = workbook.add_format({
        "border": 1, "valign": "vcenter", "num_format": "0.00",
    })
    total_format = workbook.add_format({"bold": True, "border": 1, "valign": "vcenter"})
    total_number_format = workbook.add_format({
        "bold": True, "border": 1, "valign": "vcenter", "num_format": "0.00",
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
    # DYNAMIC BRANCH LOCATION (SAME LOGIC AS FSR EXPORT)
    # ---------------------------------------------------------

    logged_in_user = frappe.session.user
    user_branch = frappe.db.get_value("User", logged_in_user, "custom_branch")

    branch_location = "Milk Plant, Cheshmashahi, Srinagar-190001"

    if user_branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":
        branch_location = "Milk Plant, Cheshmashahi, Srinagar-190001"
    else:
        branch_location = "Milk Plant, Satwari, Jammu-180004"

    # ---------------------------------------------------------
    # COMPANY HEADER
    # ---------------------------------------------------------

    worksheet.set_row(0, 24)
    worksheet.set_row(1, 20)
    worksheet.set_row(2, 20)
    worksheet.set_row(4, 22)
    worksheet.set_row(5, 20)

    worksheet.merge_range(
        0, 0, 0, last_column,
        "JAMMU & KASHMIR MILK PRODUCERS CO-OPERATIVE LIMITED",
        company_format
    )
    worksheet.merge_range(1, 0, 1, last_column, branch_location, address_format)
    worksheet.merge_range(
        2, 0, 2, last_column,
        "Tele/Fax : 0194-2501786, Email: info@jkmpcl.coop",
        contact_format
    )

    # ---------------------------------------------------------
    # REPORT TITLE
    # ---------------------------------------------------------

    worksheet.merge_range(
        4, 0, 4, last_column,
        "Daily Movement Report (Geo-Tracking & Activity Log)",
        title_format
    )
    worksheet.merge_range(
        5, 0, 5, last_column,
        f"From {formatdate(from_date, 'dd/mm/yyyy')} To {formatdate(to_date, 'dd/mm/yyyy')}",
        date_format
    )

    # ---------------------------------------------------------
    # APPLIED FILTERS
    # ---------------------------------------------------------

    filter_values = []

    employee = filters.get("employee")
    branch = filters.get("branch")

    if employee:
        employee_name = frappe.db.get_value("Employee", employee, "employee_name")
        filter_values.append(
            f"Employee: {employee_name} ({employee})" if employee_name else f"Employee: {employee}"
        )

    if branch:
        filter_values.append(f"Branch: {branch}")

    filter_values.append(f"From Date: {formatdate(from_date, 'dd/mm/yyyy')}")
    filter_values.append(f"To Date: {formatdate(to_date, 'dd/mm/yyyy')}")

    worksheet.write(6, 0, "Applied Filters:", filter_format)
    worksheet.merge_range(
        6, 1, 6, last_column,
        " | ".join(filter_values) if filter_values else "All",
        filter_format
    )
    worksheet.set_row(6, 30)

    # ---------------------------------------------------------
    # SEPARATOR
    # ---------------------------------------------------------

    for col_idx in range(total_columns):
        worksheet.write_blank(7, col_idx, None, separator_format)

    # ---------------------------------------------------------
    # REPORT TABLE START
    # ---------------------------------------------------------

    start_row = 8

    for col_idx, column in enumerate(columns):
        label = column.get("label") or column.get("fieldname") or ""
        worksheet.write(start_row, col_idx, label, column_header_format)

    # ---------------------------------------------------------
    # WRITE REPORT DATA
    # (Sub Total / Grand Total rows already exist in `data` - bold them)
    # ---------------------------------------------------------

    for row_idx, row in enumerate(data, start=1):
        excel_row = start_row + row_idx
        is_total_row = bool(row.get("is_total_row"))

        for col_idx, column in enumerate(columns):
            fieldname = column.get("fieldname")
            fieldtype = column.get("fieldtype")

            value = row.get(fieldname, "") if fieldname else ""

            if fieldname == "photos":
                value = get_photo_export_status(value)
            else:
                value = clean_excel_value(value)

            if value is None:
                value = ""

            if fieldtype == "Float":
                format_to_use = total_number_format if is_total_row else number_format
            else:
                format_to_use = total_format if is_total_row else cell_format

            worksheet.write(excel_row, col_idx, value, format_to_use)

        if is_total_row:
            worksheet.set_row(excel_row, 18)

    # ---------------------------------------------------------
    # COLUMN WIDTHS
    # ---------------------------------------------------------

    for col_idx, column in enumerate(columns):
        width = column.get("width") or 15
        try:
            width = int(width / 7)
        except (TypeError, ValueError):
            width = 15
        width = max(10, min(width, 40))
        worksheet.set_column(col_idx, col_idx, width)

    # ---------------------------------------------------------
    # FREEZE / PRINT SETTINGS
    # ---------------------------------------------------------

    worksheet.freeze_panes(start_row + 1, 0)
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 0)
    worksheet.set_margins(left=0.25, right=0.25, top=0.50, bottom=0.50)
    worksheet.repeat_rows(start_row, start_row)
    worksheet.set_footer("&CPage &P of &N")
    worksheet.print_area(0, 0, start_row + len(data), last_column)

    # ---------------------------------------------------------
    # CLOSE + SEND
    # ---------------------------------------------------------

    workbook.close()
    output.seek(0)

    filename = (
        f"DSR_Report_"
        f"({formatdate(from_date, 'dd-mm-yyyy')}-"
        f"{formatdate(to_date, 'dd-mm-yyyy')}).xlsx"
    )

    frappe.response["filename"] = filename
    frappe.response["filecontent"] = output.getvalue()
    frappe.response["type"] = "binary"