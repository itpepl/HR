# import frappe
# from frappe import _
# from frappe.utils import flt, getdate
# from collections import defaultdict

# def execute(filters=None):
#     # Validate that as_on_date is within the fiscal year
#     validate_filters(filters)
    
#     columns = get_columns(filters)
#     data = get_data(filters)
    
#     # Apply grouping if group_by filter is set
#     if filters.get("group_by") and filters.group_by != "":
#         data = group_data(data, filters)
    
#     return columns, data

# def validate_filters(filters):
#     """Validate that the as_on_date is within the selected fiscal year"""
#     if not filters.get("fiscal_year"):
#         frappe.throw(_("Please select a Fiscal Year"))
    
#     if not filters.get("as_on_date"):
#         frappe.throw(_("Please select an As On Date"))
    
#     # Get fiscal year details
#     fy = frappe.get_doc("Fiscal Year", filters.fiscal_year)
#     fy_start = getdate(fy.year_start_date)
#     fy_end = getdate(fy.year_end_date)
#     as_on_date = getdate(filters.as_on_date)
    
#     # Check if as_on_date is within the fiscal year
#     if as_on_date < fy_start or as_on_date > fy_end:
#         frappe.throw(
#             _("As On Date {0} is outside the Fiscal Year {1} ({2} to {3}). Please select a date within the fiscal year.").format(
#                 frappe.utils.format_date(as_on_date),
#                 filters.fiscal_year,
#                 frappe.utils.format_date(fy_start),
#                 frappe.utils.format_date(fy_end)
#             )
#         )

# def get_columns(filters):
#     leave_type = filters.get("leave_type")
    
#     columns = [
#         {
#             "label": "Employee Id",
#             "fieldname": "employee",
#             "fieldtype": "Data",
#             "width": 200
#         },
#         {
#             "label": "Employee Name",
#             "fieldname": "employee_name",
#             "fieldtype": "Data",
#             "width": 200
#         },
#         {
#             "label": "Employment Type",
#             "fieldname": "employment_type",
#             "fieldtype": "Data",
#             "width": 130
#         },
#         {
#             "label": "Designation",
#             "fieldname": "designation",
#             "fieldtype": "Data",
#             "width": 180
#         },
#         {
#             "label": "Branch",
#             "fieldname": "branch",
#             "fieldtype": "Link",
#             "options": "Branch",
#             "width": 180
#         }
#     ]
    
#     # Add grouping column if needed
#     if filters.get("group_by") and filters.group_by != "":
#         group_field = filters.group_by.lower().replace(" ", "_")
#         if group_field == "grade":
#             columns.insert(0, {
#                 "label": filters.group_by,
#                 "fieldname": group_field,
#                 "fieldtype": "Data",
#                 "width": 150
#             })
#         else:
#             columns.insert(0, {
#                 "label": filters.group_by,
#                 "fieldname": group_field,
#                 "fieldtype": "Link",
#                 "options": filters.group_by,
#                 "width": 150
#             })
    
#     # CL Columns
#     if leave_type in [None, "", "Casual Leave"]:
#         columns.extend([
#             {
#                 "label": "CL Credited (FY Start)",
#                 "fieldname": "cl_credited",
#                 "fieldtype": "Float",
#                 "width": 140
#             },
#             {
#                 "label": "CL Accrued (During FY)",
#                 "fieldname": "cl_accrued",
#                 "fieldtype": "Float",
#                 "width": 140
#             },
#             {
#                 "label": "CL Availed (During FY)",
#                 "fieldname": "cl_availed",
#                 "fieldtype": "Float",
#                 "width": 140
#             },
#             {
#                 "label": "CL Lapsed (FY End)",
#                 "fieldname": "cl_lapsed",
#                 "fieldtype": "Float",
#                 "width": 140
#             }
#         ])
    
#     # SL Columns
#     if leave_type in [None, "", "Sick Leave"]:
#         columns.extend([
#             {
#                 "label": "SL Opening Balance",
#                 "fieldname": "sl_opening",
#                 "fieldtype": "Float",
#                 "width": 140
#             },
#             {
#                 "label": "SL Credited",
#                 "fieldname": "sl_credited",
#                 "fieldtype": "Float",
#                 "width": 140
#             },
#             {
#                 "label": "SL Accrued",
#                 "fieldname": "sl_accrued",
#                 "fieldtype": "Float",
#                 "width": 140
#             },
#             {
#                 "label": "SL Availed",
#                 "fieldname": "sl_availed",
#                 "fieldtype": "Float",
#                 "width": 140
#             },
#             {
#                 "label": "SL Total Available",
#                 "fieldname": "sl_total_available",
#                 "fieldtype": "Float",
#                 "width": 150
#             },
#             {
#                 "label": "SL Transfer to PL",
#                 "fieldname": "sl_transfer_to_pl",
#                 "fieldtype": "Float",
#                 "width": 150
#             },
#             {
#                 "label": "SL Closing Balance",
#                 "fieldname": "sl_closing",
#                 "fieldtype": "Float",
#                 "width": 150
#             }
#         ])
    
#     # PL Columns
#     if leave_type in [None, "", "Privilege Leave"]:
#         columns.extend([
#             {
#                 "label": "PL Opening Balance",
#                 "fieldname": "pl_opening",
#                 "fieldtype": "Float",
#                 "width": 150
#             },
#             {
#                 "label": "PL Transfer from SL",
#                 "fieldname": "pl_transfer_from_sl",
#                 "fieldtype": "Float",
#                 "width": 150
#             },
#             {
#                 "label": "PL Accrued",
#                 "fieldname": "pl_accrued",
#                 "fieldtype": "Float",
#                 "width": 120
#             },
#             {
#                 "label": "PL Availed",
#                 "fieldname": "pl_availed",
#                 "fieldtype": "Float",
#                 "width": 120
#             },
#             {
#                 "label": "PL Total Available",
#                 "fieldname": "pl_total_available",
#                 "fieldtype": "Float",
#                 "width": 150
#             },
#             {
#                 "label": "PL Eligible for Encashment",
#                 "fieldname": "pl_encashment",
#                 "fieldtype": "Float",
#                 "width": 180
#             },
#             {
#                 "label": "PL Closing Balance",
#                 "fieldname": "pl_closing",
#                 "fieldtype": "Float",
#                 "width": 150
#             }
#         ])
    
#     return columns

# def get_data(filters):
#     fy = frappe.get_doc("Fiscal Year", filters.fiscal_year)
#     fy_start = fy.year_start_date
#     as_on_date = getdate(filters.as_on_date)
#     fy_end = getdate(fy.year_end_date)
    
#     conditions = ""
    
#     if filters.get("branch"):
#         conditions += " and branch = %(branch)s"
    
#     if filters.get("employment_type") and filters.employment_type != "All":
#         conditions += " and employment_type = %(employment_type)s"
    
#     if filters.get("employee"):
#         conditions += " and name = %(employee)s"
    
#     if filters.get("department"):
#         conditions += " and department = %(department)s"
    
#     if filters.get("designation"):
#         conditions += " and designation = %(designation)s"
    
#     if filters.get("grade"):
#         conditions += " and grade = %(grade)s"
    
#     employees = frappe.db.sql(f"""
#         SELECT
#             name,
#             employee_name,
#             designation,
#             branch,
#             employment_type,
#             department,
#             grade,
#             date_of_joining,
#             final_confirmation_date
#         FROM `tabEmployee`
#         WHERE status='Active'
#         {conditions}
#         ORDER BY employee_name
#     """, filters, as_dict=1)
    
#     data = []
    
#     for emp in employees:
#         row = {
#             "employee": emp.name,
#             "employee_name": emp.employee_name,
#             "employment_type": emp.employment_type,
#             "designation": emp.designation,
#             "branch": emp.branch,
#             "department": emp.department,
#             "grade": emp.grade,
#             "indent": 1
#         }
        
#         # ==================================================
#         # CASUAL LEAVE (CL)
#         # ==================================================
        
#         # Get all leave allocation transactions for CL during FY
#         cl_transactions = get_leave_transactions(
#             emp.name,
#             "Casual Leave",
#             fy_start,
#             as_on_date
#         )
        
#         cl_credited = 0
#         cl_accrued = 0
        
#         # Check if employee is confirmed and has a confirmation date
#         if emp.employment_type == "Confirmed" and emp.final_confirmation_date:
#             # For confirmed employees, check each transaction date
#             for transaction in cl_transactions:
#                 if transaction.from_date >= emp.final_confirmation_date:
#                     # If allocation is on or after confirmation date, show in Credited
#                     cl_credited += transaction.leaves
#                 else:
#                     # If allocation is before confirmation date, show in Accrued
#                     cl_accrued += transaction.leaves
#         else:
#             # For Probation/Contractual or employees without confirmation date: All allocations go to Accrued
#             for transaction in cl_transactions:
#                 cl_accrued += transaction.leaves
        
#         row["cl_credited"] = cl_credited
#         row["cl_accrued"] = cl_accrued
        
#         # Leave availed is tracked for ALL employees
#         row["cl_availed"] = get_leave_availed(
#             emp.name,
#             "Casual Leave",
#             fy_start,
#             as_on_date
#         )
        
#         # CL Lapsed - Always calculate (no FY end condition)
#         row["cl_lapsed"] = max(
#             row["cl_credited"]
#             + row["cl_accrued"]
#             - row["cl_availed"],
#             0
#         )
        
#         # ==================================================
#         # SICK LEAVE (SL)
#         # ==================================================
        
#         row["sl_opening"] = get_opening_balance(
#             emp.name,
#             "Sick Leave",
#             fy_start
#         )
        
#         # Get all leave allocation transactions for SL during FY
#         sl_transactions = get_leave_transactions(
#             emp.name,
#             "Sick Leave",
#             fy_start,
#             as_on_date
#         )
        
#         sl_credited = 0
#         sl_accrued = 0
        
#         # Check if employee is confirmed and has a confirmation date
#         if emp.employment_type == "Confirmed" and emp.final_confirmation_date:
#             # For confirmed employees, check each transaction date
#             for transaction in sl_transactions:
#                 if transaction.from_date >= emp.final_confirmation_date:
#                     sl_credited += transaction.leaves
#                 else:
#                     sl_accrued += transaction.leaves
#         else:
#             # For Probation/Contractual: All allocations go to Accrued
#             for transaction in sl_transactions:
#                 sl_accrued += transaction.leaves
        
#         row["sl_credited"] = sl_credited
#         row["sl_accrued"] = sl_accrued
        
#         row["sl_availed"] = get_leave_availed(
#             emp.name,
#             "Sick Leave",
#             fy_start,
#             as_on_date
#         )
        
#         row["sl_total_available"] = (
#             row["sl_opening"]
#             + row["sl_credited"]
#             + row["sl_accrued"]
#             - row["sl_availed"]
#         )
        
#         # SL Transfer to PL - Always calculate (no FY end condition)
#         if emp.employment_type == "Confirmed":
#             row["sl_transfer_to_pl"] = max(
#                 row["sl_total_available"] - 28,
#                 0
#             )
#         else:
#             row["sl_transfer_to_pl"] = 0
        
#         row["sl_closing"] = (
#             row["sl_total_available"]
#             - row["sl_transfer_to_pl"]
#         )
        
#         # ==================================================
#         # PRIVILEGE LEAVE (PL)
#         # ==================================================
        
#         row["pl_opening"] = get_opening_balance(
#             emp.name,
#             "Privilege Leave",
#             fy_start
#         )
        
#         # PL Transfer from SL - Always show (no FY end condition)
#         row["pl_transfer_from_sl"] = row["sl_transfer_to_pl"]
        
#         # PL Accrued - only for Confirmed employees with confirmation date
#         if emp.employment_type == "Confirmed" and emp.final_confirmation_date:
#             pl_transactions = get_leave_transactions(
#                 emp.name,
#                 "Privilege Leave",
#                 fy_start,
#                 as_on_date
#             )
#             pl_accrued = 0
#             for transaction in pl_transactions:
#                 # Only consider PL allocations on or after confirmation date
#                 if transaction.from_date >= emp.final_confirmation_date:
#                     pl_accrued += transaction.leaves
#             row["pl_accrued"] = pl_accrued
#         else:
#             row["pl_accrued"] = 0
        
#         row["pl_availed"] = get_leave_availed(
#             emp.name,
#             "Privilege Leave",
#             fy_start,
#             as_on_date
#         )
        
#         row["pl_total_available"] = (
#             row["pl_opening"]
#             + row["pl_transfer_from_sl"]
#             + row["pl_accrued"]
#             - row["pl_availed"]
#         )
        
#         # PL Encashment - Always calculate (no FY end condition)
#         if emp.employment_type == "Confirmed":
#             row["pl_encashment"] = max(
#                 row["pl_total_available"] - 120,
#                 0
#             )
#         else:
#             row["pl_encashment"] = 0
        
#         row["pl_closing"] = (
#             row["pl_total_available"]
#             - row["pl_encashment"]
#         )
        
#         data.append(row)
    
#     return data

# def get_leave_transactions(employee, leave_type, from_date, to_date):
#     """Get all leave allocation transactions with their dates"""
#     result = frappe.db.sql("""
#         SELECT 
#             from_date,
#             leaves
#         FROM `tabLeave Ledger Entry`
#         WHERE employee=%s
#         AND leave_type=%s
#         AND transaction_type='Leave Allocation'
#         AND leaves > 0
#         AND from_date >= %s AND from_date <= %s
#         ORDER BY from_date
#     """, (
#         employee,
#         leave_type,
#         from_date,
#         to_date
#     ), as_dict=1)
    
#     return result

# def group_data(data, filters):
#     group_by_field = filters.get("group_by").lower().replace(" ", "_")
#     grouped_data = []
    
#     # If no data, return empty list
#     if not data:
#         return grouped_data
    
#     # Group the data
#     groups = defaultdict(list)
#     for row in data:
#         group_value = row.get(group_by_field, "")
#         if not group_value:
#             group_value = "Unassigned"
#         groups[group_value].append(row)
    
#     # Get all column names from the first row
#     all_columns = list(data[0].keys())
    
#     # Remove 'indent' column if it exists
#     if "indent" in all_columns:
#         all_columns.remove("indent")
    
#     # Create serial number counter
#     serial_no = 1
    
#     # Process each group
#     for group_name, group_rows in sorted(groups.items()):
#         # Add rows for this group
#         for idx, row in enumerate(group_rows):
#             row_copy = {}
#             for col in all_columns:
#                 if col == "#":
#                     row_copy[col] = serial_no
#                 elif col == group_by_field:
#                     # Show group name only in the first row of each group
#                     if idx == 0:
#                         row_copy[col] = f"<b>{group_name}</b>"
#                     else:
#                         row_copy[col] = ""
#                 else:
#                     value = row.get(col, "")
#                     # Clean zero values - show empty string for zeros
#                     if isinstance(value, (int, float)) and value == 0:
#                         row_copy[col] = ""
#                     elif value == "0" or value == "0.000" or value == "0.00":
#                         row_copy[col] = ""
#                     else:
#                         row_copy[col] = value
#             grouped_data.append(row_copy)
#             serial_no += 1
        
#         # Add a blank row after each group for separation
#         blank_row = {}
#         for col in all_columns:
#             blank_row[col] = ""
#         grouped_data.append(blank_row)
    
#     return grouped_data

# def get_opening_balance(employee, leave_type, fy_start):
#     result = frappe.db.sql("""
#         SELECT COALESCE(SUM(leaves),0)
#         FROM `tabLeave Ledger Entry`
#         WHERE employee=%s
#         AND leave_type=%s
#         AND from_date < %s
#     """, (
#         employee,
#         leave_type,
#         fy_start
#     ))
    
#     return flt(result[0][0] or 0)

# def get_leave_availed(employee, leave_type, from_date, to_date):
#     result = frappe.db.sql("""
#         SELECT ABS(COALESCE(SUM(leaves),0))
#         FROM `tabLeave Ledger Entry`
#         WHERE employee = %s
#         AND leave_type = %s
#         AND (
#             transaction_type = 'Leave Application'
#             OR (
#                 transaction_type = 'Leave Allocation'
#                 AND leaves < 0
#             )
#         )
#         AND from_date BETWEEN %s AND %s
#     """, (
#         employee,
#         leave_type,
#         from_date,
#         to_date
#     ))
    
#     return flt(result[0][0] or 0)

# def get_positive_transactions(employee, leave_type, from_date, to_date):
#     result = frappe.db.sql("""
#         SELECT COALESCE(SUM(leaves),0)
#         FROM `tabLeave Ledger Entry`
#         WHERE employee=%s
#         AND leave_type=%s
#         AND transaction_type='Leave Allocation'
#         AND leaves > 0
#         AND from_date >= %s AND from_date <= %s
#     """, (
#         employee,
#         leave_type,
#         from_date,
#         to_date
#     ))
    
#     return flt(result[0][0] or 0)


import frappe
from frappe import _
from frappe.utils import flt, getdate
from collections import defaultdict

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    
    # Apply grouping if group_by filter is set
    if filters.get("group_by") and filters.group_by != "":
        data = group_data(data, filters)
    
    return columns, data

def get_columns(filters):
    leave_type = filters.get("leave_type")
    
    columns = [
        {
            "label": "Employee Id",
            "fieldname": "employee",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Employment Type",
            "fieldname": "employment_type",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": "Designation",
            "fieldname": "designation",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Branch",
            "fieldname": "branch",
            "fieldtype": "Link",
            "options": "Branch",
            "width": 180
        }
    ]
    
    # Add grouping column if needed
    if filters.get("group_by") and filters.group_by != "":
        group_field = filters.group_by.lower().replace(" ", "_")
        if group_field == "grade":
            columns.insert(0, {
                "label": filters.group_by,
                "fieldname": group_field,
                "fieldtype": "Data",
                "width": 150
            })
        else:
            columns.insert(0, {
                "label": filters.group_by,
                "fieldname": group_field,
                "fieldtype": "Link",
                "options": filters.group_by,
                "width": 150
            })
    
    # CL Columns
    if leave_type in [None, "", "Casual Leave"]:
        columns.extend([
            {
                "label": "CL Credited (FY Start)",
                "fieldname": "cl_credited",
                "fieldtype": "Float",
                "width": 140
            },
            {
                "label": "CL Accrued (During FY)",
                "fieldname": "cl_accrued",
                "fieldtype": "Float",
                "width": 140
            },
            {
                "label": "CL Availed (During FY)",
                "fieldname": "cl_availed",
                "fieldtype": "Float",
                "width": 140
            },
            {
                "label": "CL lapsed on/Will be 31st mar",
                "fieldname": "cl_lapsed",
                "fieldtype": "Float",
                "width": 140
            }
        ])
    
    # SL Columns
    if leave_type in [None, "", "Sick Leave"]:
        columns.extend([
            {
                "label": "SL Opening Balance",
                "fieldname": "sl_opening",
                "fieldtype": "Float",
                "width": 140
            },
            {
                "label": "SL Credited",
                "fieldname": "sl_credited",
                "fieldtype": "Float",
                "width": 140
            },
            {
                "label": "SL Accrued",
                "fieldname": "sl_accrued",
                "fieldtype": "Float",
                "width": 140
            },
            {
                "label": "SL Availed",
                "fieldname": "sl_availed",
                "fieldtype": "Float",
                "width": 140
            },
            {
                "label": "SL Total Available",
                "fieldname": "sl_total_available",
                "fieldtype": "Float",
                "width": 150
            },
            {
                "label": "SL Transfer to PL",
                "fieldname": "sl_transfer_to_pl",
                "fieldtype": "Float",
                "width": 150
            },
            {
                "label": "SL Closing Balance",
                "fieldname": "sl_closing",
                "fieldtype": "Float",
                "width": 150
            }
        ])
    
    # PL Columns
    if leave_type in [None, "", "Privilege Leave"]:
        columns.extend([
            {
                "label": "PL Opening Balance",
                "fieldname": "pl_opening",
                "fieldtype": "Float",
                "width": 150
            },
            {
                "label": "PL Transfer from SL",
                "fieldname": "pl_transfer_from_sl",
                "fieldtype": "Float",
                "width": 150
            },
            {
                "label": "PL Accrued",
                "fieldname": "pl_accrued",
                "fieldtype": "Float",
                "width": 120
            },
            {
                "label": "PL Availed",
                "fieldname": "pl_availed",
                "fieldtype": "Float",
                "width": 120
            },
            {
                "label": "PL Total Available",
                "fieldname": "pl_total_available",
                "fieldtype": "Float",
                "width": 150
            },
            {
                "label": "PL Eligible for Encashment",
                "fieldname": "pl_encashment",
                "fieldtype": "Float",
                "width": 180
            },
            {
                "label": "PL Closing Balance",
                "fieldname": "pl_closing",
                "fieldtype": "Float",
                "width": 150
            }
        ])
    
    return columns

def get_data(filters):
    fy = frappe.get_doc("Fiscal Year", filters.fiscal_year)
    fy_start = getdate(fy.year_start_date)  # 01-04-XXXX
    fy_end = getdate(fy.year_end_date)      # 31-03-XXXX
    
    conditions = ""
    
    if filters.get("branch"):
        conditions += " and branch = %(branch)s"
    
    if filters.get("employment_type") and filters.employment_type != "All":
        conditions += " and employment_type = %(employment_type)s"
    
    if filters.get("employee"):
        conditions += " and name = %(employee)s"
    
    if filters.get("department"):
        conditions += " and department = %(department)s"
    
    if filters.get("designation"):
        conditions += " and designation = %(designation)s"
    
    if filters.get("grade"):
        conditions += " and grade = %(grade)s"
    
    employees = frappe.db.sql(f"""
        SELECT
            name,
            employee_name,
            designation,
            branch,
            employment_type,
            department,
            grade,
            date_of_joining,
            final_confirmation_date
        FROM `tabEmployee`
        WHERE status='Active'
        {conditions}
        ORDER BY employee_name
    """, filters, as_dict=1)
    
    data = []
    
    for emp in employees:
        row = {
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "employment_type": emp.employment_type,
            "designation": emp.designation,
            "branch": emp.branch,
            "department": emp.department,
            "grade": emp.grade,
            "indent": 1
        }
        
        # ==================================================
        # CASUAL LEAVE (CL)
        # ==================================================
        
        # Get all leave allocation transactions for CL during FY
        cl_transactions = get_leave_transactions(
            emp.name,
            "Casual Leave",
            fy_start,
            fy_end
        )
        
        cl_credited = 0
        cl_accrued = 0
        
        # Check if employee is confirmed and has a confirmation date
        if emp.employment_type == "Confirmed" and emp.final_confirmation_date:
            # For confirmed employees, check each transaction date
            for transaction in cl_transactions:
                if transaction.from_date >= emp.final_confirmation_date:
                    # If allocation is on or after confirmation date, show in Credited
                    cl_credited += transaction.leaves
                else:
                    # If allocation is before confirmation date, show in Accrued
                    cl_accrued += transaction.leaves
        else:
            # For Probation/Contractual or employees without confirmation date: All allocations go to Accrued
            for transaction in cl_transactions:
                cl_accrued += transaction.leaves
        
        row["cl_credited"] = cl_credited
        row["cl_accrued"] = cl_accrued
        
        # Leave availed is tracked for ALL employees
        row["cl_availed"] = get_leave_availed(
            emp.name,
            "Casual Leave",
            fy_start,
            fy_end
        )
        
        # CL Lapsed - Always calculate
        row["cl_lapsed"] = max(
            row["cl_credited"]
            + row["cl_accrued"]
            - row["cl_availed"],
            0
        )
        
        # ==================================================
        # SICK LEAVE (SL)
        # ==================================================
        
        row["sl_opening"] = get_opening_balance(
            emp.name,
            "Sick Leave",
            fy_start
        )
        
        # Get all leave allocation transactions for SL during FY
        sl_transactions = get_leave_transactions(
            emp.name,
            "Sick Leave",
            fy_start,
            fy_end
        )
        
        sl_credited = 0
        sl_accrued = 0
        
        # Check if employee is confirmed and has a confirmation date
        if emp.employment_type == "Confirmed" and emp.final_confirmation_date:
            # For confirmed employees, check each transaction date
            for transaction in sl_transactions:
                if transaction.from_date >= emp.final_confirmation_date:
                    sl_credited += transaction.leaves
                else:
                    sl_accrued += transaction.leaves
        else:
            # For Probation/Contractual: All allocations go to Accrued
            for transaction in sl_transactions:
                sl_accrued += transaction.leaves
        
        row["sl_credited"] = sl_credited
        row["sl_accrued"] = sl_accrued
        
        row["sl_availed"] = get_leave_availed(
            emp.name,
            "Sick Leave",
            fy_start,
            fy_end
        )
        
        row["sl_total_available"] = (
            row["sl_opening"]
            + row["sl_credited"]
            + row["sl_accrued"]
            - row["sl_availed"]
        )
        
        # SL Transfer to PL - Always calculate
        if emp.employment_type == "Confirmed":
            row["sl_transfer_to_pl"] = max(
                row["sl_total_available"] - 28,
                0
            )
        else:
            row["sl_transfer_to_pl"] = 0
        
        row["sl_closing"] = (
            row["sl_total_available"]
            - row["sl_transfer_to_pl"]
        )
        
        # ==================================================
        # PRIVILEGE LEAVE (PL)
        # ==================================================
        
        row["pl_opening"] = get_opening_balance(
            emp.name,
            "Privilege Leave",
            fy_start
        )
        
        # PL Transfer from SL - Always show
        row["pl_transfer_from_sl"] = row["sl_transfer_to_pl"]
        
        # PL Accrued - only for Confirmed employees with confirmation date
        if emp.employment_type == "Confirmed" and emp.final_confirmation_date:
            pl_transactions = get_leave_transactions(
                emp.name,
                "Privilege Leave",
                fy_start,
                fy_end
            )
            pl_accrued = 0
            for transaction in pl_transactions:
                # Only consider PL allocations on or after confirmation date
                if transaction.from_date >= emp.final_confirmation_date:
                    pl_accrued += transaction.leaves
            row["pl_accrued"] = pl_accrued
        else:
            row["pl_accrued"] = 0
        
        row["pl_availed"] = get_leave_availed(
            emp.name,
            "Privilege Leave",
            fy_start,
            fy_end
        )
        
        row["pl_total_available"] = (
            row["pl_opening"]
            + row["pl_transfer_from_sl"]
            + row["pl_accrued"]
            - row["pl_availed"]
        )
        
        # PL Encashment - Always calculate
        if emp.employment_type == "Confirmed":
            row["pl_encashment"] = max(
                row["pl_total_available"] - 120,
                0
            )
        else:
            row["pl_encashment"] = 0
        
        row["pl_closing"] = (
            row["pl_total_available"]
            - row["pl_encashment"]
        )
        
        data.append(row)
    
    return data

def get_leave_transactions(employee, leave_type, from_date, to_date):
    """Get all leave allocation transactions with their dates"""
    result = frappe.db.sql("""
        SELECT 
            from_date,
            leaves
        FROM `tabLeave Ledger Entry`
        WHERE employee=%s
        AND leave_type=%s
        AND transaction_type='Leave Allocation'
        AND leaves > 0
        AND from_date >= %s AND from_date <= %s
        ORDER BY from_date
    """, (
        employee,
        leave_type,
        from_date,
        to_date
    ), as_dict=1)
    
    return result

def group_data(data, filters):
    group_by_field = filters.get("group_by").lower().replace(" ", "_")
    grouped_data = []
    
    # If no data, return empty list
    if not data:
        return grouped_data
    
    # Group the data
    groups = defaultdict(list)
    for row in data:
        group_value = row.get(group_by_field, "")
        if not group_value:
            group_value = "Unassigned"
        groups[group_value].append(row)
    
    # Get all column names from the first row
    all_columns = list(data[0].keys())
    
    # Remove 'indent' column if it exists
    if "indent" in all_columns:
        all_columns.remove("indent")
    
    # Create serial number counter
    serial_no = 1
    
    # Process each group
    for group_name, group_rows in sorted(groups.items()):
        # Add rows for this group
        for idx, row in enumerate(group_rows):
            row_copy = {}
            for col in all_columns:
                if col == "#":
                    row_copy[col] = serial_no
                elif col == group_by_field:
                    # Show group name only in the first row of each group
                    if idx == 0:
                        row_copy[col] = f"<b>{group_name}</b>"
                    else:
                        row_copy[col] = ""
                else:
                    value = row.get(col, "")
                    # Clean zero values - show empty string for zeros
                    if isinstance(value, (int, float)) and value == 0:
                        row_copy[col] = ""
                    elif value == "0" or value == "0.000" or value == "0.00":
                        row_copy[col] = ""
                    else:
                        row_copy[col] = value
            grouped_data.append(row_copy)
            serial_no += 1
        
        # Add a blank row after each group for separation
        blank_row = {}
        for col in all_columns:
            blank_row[col] = ""
        grouped_data.append(blank_row)
    
    return grouped_data

def get_opening_balance(employee, leave_type, fy_start):
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(leaves),0)
        FROM `tabLeave Ledger Entry`
        WHERE employee=%s
        AND leave_type=%s
        AND from_date < %s
    """, (
        employee,
        leave_type,
        fy_start
    ))
    
    return flt(result[0][0] or 0)

def get_leave_availed(employee, leave_type, from_date, to_date):
    result = frappe.db.sql("""
        SELECT ABS(COALESCE(SUM(leaves),0))
        FROM `tabLeave Ledger Entry`
        WHERE employee = %s
        AND leave_type = %s
        AND (
            transaction_type = 'Leave Application'
            OR (
                transaction_type = 'Leave Allocation'
                AND leaves < 0
            )
        )
        AND from_date BETWEEN %s AND %s
    """, (
        employee,
        leave_type,
        from_date,
        to_date
    ))
    
    return flt(result[0][0] or 0)

def get_positive_transactions(employee, leave_type, from_date, to_date):
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(leaves),0)
        FROM `tabLeave Ledger Entry`
        WHERE employee=%s
        AND leave_type=%s
        AND transaction_type='Leave Allocation'
        AND leaves > 0
        AND from_date >= %s AND from_date <= %s
    """, (
        employee,
        leave_type,
        from_date,
        to_date
    ))
    
    return flt(result[0][0] or 0)