import frappe
from frappe import _

# ============================================================
# MAIN VALIDATE FUNCTION - DOCEVENT FOR LEAVE ENCASHMENT
# ============================================================

def validate_leave_encashment(doc, method):
    """
    Validate event for Leave Encashment
    This function is called when Leave Encashment is saved
    """
    
    # Skip if no employee
    if not doc.employee:
        return
    
    try:
        # Get employee details
        employee = frappe.get_doc("Employee", doc.employee)
        relieving_date = employee.get("relieving_date")
        is_relieving = bool(relieving_date)
        
        # Get leave balance
        leave_balance = get_leave_balance(doc.employee, doc.leave_type)
        
        # Calculate encashment based on employee status
        if is_relieving:
            # RELIEVING EMPLOYEE: All leaves encashed (no limit)
            actual_encashable_days = leave_balance
            encashment_days = leave_balance
            max_carry_forward = 0
        else:
            # ACTIVE EMPLOYEE: Apply max carry forward limit
            max_carry_forward = frappe.db.get_value(
                "Leave Type", 
                doc.leave_type, 
                "maximum_carry_forwarded_leaves"
            ) 
            
            if leave_balance > max_carry_forward:
                actual_encashable_days = leave_balance - max_carry_forward
                encashment_days = actual_encashable_days
            else:
                actual_encashable_days = 0
                encashment_days = 0
        
        # Set fields in document
        doc.leave_balance = leave_balance
        doc.actual_encashable_days = actual_encashable_days
        doc.encashment_days = encashment_days
        
        # Calculate amount if encashment_days > 0
        if encashment_days > 0:
            per_day_rate = get_per_day_rate(doc.employee)
            doc.per_day_rate = per_day_rate
            doc.encashment_amount = encashment_days * per_day_rate
        else:
            doc.encashment_amount = 0
        
    except Exception as e:
        frappe.log_error(f"Leave Encashment validation error: {str(e)}", "Leave Encashment")
        frappe.throw(_(f"Error in leave encashment calculation: {str(e)}"))


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_leave_balance(employee_id, leave_type):
    """Get Privilege Leave balance for employee"""
    
    leave_type = leave_type
    
    allocations = frappe.get_all("Leave Allocation",
        filters={
            "employee": employee_id,
            "leave_type": leave_type,
            "docstatus": 1
        },
        fields=["leave_balance"],
        order_by="to_date desc",
        limit=1
    )
    
    return allocations[0].leave_balance if allocations else 0


def get_per_day_rate(employee_id):
    """Get leave encashment per day rate from Salary Structure Assignment"""
    
    # Try to get from assignment first
    assignments = frappe.get_all("Salary Structure Assignment",
        filters={
            "employee": employee_id,
            "docstatus": 1
        },
        fields=["name", "salary_structure", "base", "leave_encashment_amount_per_day"],
        order_by="from_date desc",
        limit=1
    )
    
    if not assignments:
        return 0
    
    # If per day rate is already set, use it
    if assignments[0].get("leave_encashment_amount_per_day"):
        return assignments[0].leave_encashment_amount_per_day
    


def calculate_per_day_from_structure(assignment, employee_id):
    """Calculate per day rate from salary structure"""
    
    try:
        structure = frappe.get_doc("Salary Structure", assignment.salary_structure)
        employee = frappe.get_doc("Employee", employee_id)
        base = assignment.base
        
        # Find Basic formula
        basic_formula = None
        for earning in structure.earnings:
            if earning.salary_component == "Basic":
                basic_formula = earning.formula
                break
        
        # Calculate Basic (B)
        B = 0
        if basic_formula:
            context = {
                "base": base,
                "designation": employee.designation
            }
            try:
                B = eval(basic_formula, {}, context)
            except:
                B = 0
        
        # Calculate all components
        total = 0
        for earning in structure.earnings:
            if earning.formula:
                context = {
                    "base": base,
                    "designation": employee.designation,
                    "B": B,
                    "b": B
                }
                try:
                    amount = eval(earning.formula, {}, context)
                    total += amount
                except:
                    pass
        
        # Calculate per day (÷30)
        per_day = total / 30 if total else 0
        
        # Update assignment for future use
        if per_day:
            frappe.db.set_value(
                "Salary Structure Assignment", 
                assignment.name,
                "leave_encashment_amount_per_day", 
                per_day
            )
        
        return per_day
        
    except Exception as e:
        frappe.log_error(f"Error calculating per day rate: {str(e)}", "Leave Encashment")
        return 0



# ============================================================
# ADDITIONAL HELPER FUNCTIONS (Optional)
# ============================================================

# @frappe.whitelist()
# def get_encashment_details(employee_id):
#     """API to get leave encashment details for an employee"""
    
#     employee = frappe.get_doc("Employee", employee_id)
    
#     # Get leave balance
#     leave_balance = get_leave_balance(employee_id, "Privilege Leave")
#     is_relieving = bool(employee.get("relieving_date"))
    
#     if is_relieving:
#         encashment_days = leave_balance
#         max_carry = "N/A (Relieving)"
#     else:
#         max_carry = frappe.db.get_value("Leave Type", "Privilege Leave", "max_leave_allowed") or 120
#         encashment_days = max(0, leave_balance - max_carry)
    
#     # Get per day rate
#     per_day = get_per_day_rate(employee_id)
    
#     return {
#         "employee": employee.employee_name,
#         "employee_id": employee_id,
#         "leave_balance": leave_balance,
#         "max_carry_forward": max_carry,
#         "encashment_days": encashment_days,
#         "per_day_rate": per_day,
#         "encashment_amount": encashment_days * per_day,
#         "is_relieving": is_relieving,
#         "relieving_date": employee.get("relieving_date")
#     }


# @frappe.whitelist()
# def process_all_employees_encashment():
#     """Bulk process leave encashment for all employees"""
    
#     employees = frappe.get_all("Employee",
#         filters={"status": "Active"},
#         fields=["name", "employee_name"]
#     )
    
#     results = {
#         "total": len(employees),
#         "processed": 0,
#         "updated": 0,
#         "errors": []
#     }
    
#     for emp in employees:
#         try:
#             # Check if encashment record exists
#             existing = frappe.get_all("Leave Encashment",
#                 filters={
#                     "employee": emp.name,
#                     "docstatus": ["!=", 2]
#                 },
#                 fields=["name"],
#                 order_by="creation desc",
#                 limit=1
#             )
            
#             if existing:
#                 doc = frappe.get_doc("Leave Encashment", existing[0].name)
#                 # Trigger validate
#                 validate_leave_encashment(doc, None)
#                 doc.save()
#             else:
#                 # Create new record
#                 doc = frappe.get_doc({
#                     "doctype": "Leave Encashment",
#                     "employee": emp.name,
#                     "employee_name": emp.employee_name,
#                     "leave_type": "Privilege Leave",
#                     "fiscal_year_end": "2026-03-31"
#                 })
#                 # Trigger validate
#                 validate_leave_encashment(doc, None)
#                 doc.insert()
            
#             results["updated"] += 1
#             results["processed"] += 1
            
#         except Exception as e:
#             results["errors"].append({
#                 "employee": emp.name,
#                 "error": str(e)
#             })
    
#     frappe.db.commit()
    
#     return results