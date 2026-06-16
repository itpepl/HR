# import frappe
# from frappe import _
# from frappe.utils import flt


# def execute(filters=None):
#     columns = get_columns(filters)
#     data = get_data(filters)

#     return columns, data

# def get_columns(filters):

#     leave_type = filters.get("leave_type")

#     columns = [
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
#     	{
#             "label": "Branch",
#             "fieldname": "branch",
#             "fieldtype": "Link",
#             "options":"Branch",
#             "width": 180
#         }
#     ]

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
#     as_on_date = filters.as_on_date

#     conditions = ""

#     if filters.get("branch"):
#         conditions += " and branch = %(branch)s"

#     if filters.get("employment_type") and filters.employment_type != "All":
#         conditions += " and employment_type = %(employment_type)s"

#     if filters.get("employee"):
#         conditions += " and name = %(employee)s"

#     employees = frappe.db.sql(f"""
#         SELECT
#             name,
#             employee_name,
#             designation,
#             branch,
#             employment_type
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
#             "branch":emp.branch,
#             "indent": 1
#         }

#         # ==================================================
#         # CASUAL LEAVE (CL)
#         # ==================================================
		
#         row["cl_credited"] = get_fy_start_credit(
#             emp.name,
#             "Casual Leave",
#             fy_start
#         )

#         row["cl_accrued"] = max(
#             get_positive_transactions(
#                 emp.name,
#                 "Casual Leave",
#                 fy_start,
#                 as_on_date
#             ) - row["cl_credited"],
#             0
#         )

#         row["cl_availed"] = get_leave_availed(
#             emp.name,
#             "Casual Leave",
#             fy_start,
#             as_on_date
#         )

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

#         row["sl_credited"] = get_fy_start_credit(
#             emp.name,
#             "Sick Leave",
#             fy_start
#         )

#         row["sl_accrued"] = max(
#             get_positive_transactions(
#                 emp.name,
#                 "Sick Leave",
#                 fy_start,
#                 as_on_date
#             ) - row["sl_credited"],
#             0
#         )

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

#         row["sl_transfer_to_pl"] = max(
#             row["sl_total_available"] - 28,
#             0
#         )

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

#         row["pl_transfer_from_sl"] = row["sl_transfer_to_pl"]

#         row["pl_accrued"] = get_positive_transactions(
#             emp.name,
#             "Privilege Leave",
#             fy_start,
#             as_on_date
#         )

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

#         row["pl_encashment"] = max(
#             row["pl_total_available"] - 120,
#             0
#         )

#         row["pl_closing"] = (
#             row["pl_total_available"]
#             - row["pl_encashment"]
#         )

#         data.append(row)

#     return data

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
#         AND from_date BETWEEN %s AND %s
#     """, (
#         employee,
#         leave_type,
#         from_date,
#         to_date
#     ))

#     return flt(result[0][0] or 0)

# def get_fy_start_credit(employee, leave_type, fy_start):

#     result = frappe.db.sql("""
#         SELECT COALESCE(SUM(leaves),0)
#         FROM `tabLeave Ledger Entry`
#         WHERE employee=%s
#         AND leave_type=%s
#         AND from_date=%s
#         AND leaves > 0
#     """, (
#         employee,
#         leave_type,
#         fy_start
#     ))

#     return flt(result[0][0] or 0)

# def get_balance(employee, leave_type, as_on_date):

#     balance = frappe.db.sql("""
#         SELECT COALESCE(SUM(leaves),0)
#         FROM `tabLeave Ledger Entry`
#         WHERE employee=%s
#         AND leave_type=%s
#         AND from_date <= %s
#     """, (
#         employee,
#         leave_type,
#         as_on_date
#     ))[0][0]

#     return flt(balance)

# def get_leave_allocation(employee, leave_type, from_date, to_date):

#     result = frappe.db.sql("""
#         SELECT COALESCE(SUM(leaves), 0)
#         FROM `tabLeave Ledger Entry`
#         WHERE employee = %s
#         AND leave_type = %s
#         AND transaction_type = 'Leave Allocation'
#         AND from_date BETWEEN %s AND %s
#     """, (
#         employee,
#         leave_type,
#         from_date,
#         to_date
#     ))

#     return flt(result[0][0] or 0)

# def get_cl_accrued(employee, leave_type, from_date, to_date):

#     result = frappe.db.sql("""
#         SELECT COALESCE(SUM(leaves), 0)
#         FROM `tabLeave Ledger Entry`
#         WHERE employee = %s
#         AND leave_type = %s
#         AND transaction_type = 'Leave Allocation'
#         AND from_date BETWEEN %s AND %s
#     """, (
#         employee,
#         leave_type,
#         from_date,
#         to_date
#     ))

#     return flt(result[0][0] or 0)

import frappe
from frappe import _
from frappe.utils import flt
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
                "label": "CL Lapsed (FY End)",
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
    fy_start = fy.year_start_date
    as_on_date = filters.as_on_date
    
    conditions = ""
    
    if filters.get("branch"):
        conditions += " and branch = %(branch)s"
    
    if filters.get("employment_type") and filters.employment_type != "All":
        conditions += " and employment_type = %(employment_type)s"
    
    if filters.get("employee"):
        conditions += " and name = %(employee)s"
    
    # Add department filter if needed
    if filters.get("department"):
        conditions += " and department = %(department)s"
    
    # Add designation filter if needed
    if filters.get("designation"):
        conditions += " and designation = %(designation)s"
    
    # Add grade filter if needed
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
            grade
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
        
        row["cl_credited"] = get_fy_start_credit(
            emp.name,
            "Casual Leave",
            fy_start
        )
        
        row["cl_accrued"] = max(
            get_positive_transactions(
                emp.name,
                "Casual Leave",
                fy_start,
                as_on_date
            ) - row["cl_credited"],
            0
        )
        
        row["cl_availed"] = get_leave_availed(
            emp.name,
            "Casual Leave",
            fy_start,
            as_on_date
        )
        
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
        
        row["sl_credited"] = get_fy_start_credit(
            emp.name,
            "Sick Leave",
            fy_start
        )
        
        row["sl_accrued"] = max(
            get_positive_transactions(
                emp.name,
                "Sick Leave",
                fy_start,
                as_on_date
            ) - row["sl_credited"],
            0
        )
        
        row["sl_availed"] = get_leave_availed(
            emp.name,
            "Sick Leave",
            fy_start,
            as_on_date
        )
        
        row["sl_total_available"] = (
            row["sl_opening"]
            + row["sl_credited"]
            + row["sl_accrued"]
            - row["sl_availed"]
        )
        
        row["sl_transfer_to_pl"] = max(
            row["sl_total_available"] - 28,
            0
        )
        
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
        
        row["pl_transfer_from_sl"] = row["sl_transfer_to_pl"]
        
        row["pl_accrued"] = get_positive_transactions(
            emp.name,
            "Privilege Leave",
            fy_start,
            as_on_date
        )
        
        row["pl_availed"] = get_leave_availed(
            emp.name,
            "Privilege Leave",
            fy_start,
            as_on_date
        )
        
        row["pl_total_available"] = (
            row["pl_opening"]
            + row["pl_transfer_from_sl"]
            + row["pl_accrued"]
            - row["pl_availed"]
        )
        
        row["pl_encashment"] = max(
            row["pl_total_available"] - 120,
            0
        )
        
        row["pl_closing"] = (
            row["pl_total_available"]
            - row["pl_encashment"]
        )
        
        data.append(row)
    
    return data


def group_data(data, filters):
    group_by_field = filters.get("group_by").lower().replace(" ", "_")
    grouped_data = []
    
    groups = defaultdict(list)
    for row in data:
        group_value = row.get(group_by_field, "")
        if not group_value:
            group_value = "Unassigned"
        groups[group_value].append(row)
    
    serial_no = 1
    
    if not data:
        return grouped_data
    
    # Get all column names
    all_columns = list(data[0].keys())
    if "#" not in all_columns:
        all_columns.insert(0, "#")
    
    # Remove the group_by field column from display
    if group_by_field in all_columns:
        all_columns.remove(group_by_field)
    
    for group_name, group_rows in sorted(groups.items()):
        for idx, row in enumerate(group_rows):
            row_copy = {}
            for col in all_columns:
                if col == "#":
                    if idx == 0:
                        row_copy[col] = f"<b>{group_name}</b>"
                    else:
                        row_copy[col] = serial_no
                else:
                    # Clean zero values
                    value = row.get(col, "")
                    if value == 0 or value == 0.0 or value == "0" or value == "0.000" or value == "0.00":
                        row_copy[col] = ""
                    else:
                        row_copy[col] = value
            grouped_data.append(row_copy)
            serial_no += 1
        
        grouped_data.append({})
    
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
        AND from_date BETWEEN %s AND %s
    """, (
        employee,
        leave_type,
        from_date,
        to_date
    ))
    
    return flt(result[0][0] or 0)

def get_fy_start_credit(employee, leave_type, fy_start):
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(leaves),0)
        FROM `tabLeave Ledger Entry`
        WHERE employee=%s
        AND leave_type=%s
        AND from_date=%s
        AND leaves > 0
    """, (
        employee,
        leave_type,
        fy_start
    ))
    
    return flt(result[0][0] or 0)