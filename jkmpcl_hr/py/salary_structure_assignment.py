import frappe
from frappe import _

def calculate_leave_encashment_per_day(doc, method):
    """Calculate and set leave encashment per day on validate"""
    
    if not doc.salary_structure:
        doc.leave_encashment_amount_per_day = 0
        return
    
    if not doc.base:
        doc.leave_encashment_amount_per_day = 0
        return
    
    try:
        # Get salary structure
        structure = frappe.get_doc("Salary Structure", doc.salary_structure)
        
        # Get employee for designation
        employee = frappe.get_doc("Employee", doc.employee)
        
        # Find Basic formula
        basic_formula = None
        for earning in structure.earnings:
            if earning.salary_component == "Basic":
                basic_formula = earning.formula
                break
        
        # Calculate Basic
        B = 0
        if basic_formula:
            context = {
                "base": doc.base,
                "designation": employee.designation
            }
            try:
                B = eval(basic_formula, {}, context)
            except Exception as e:
                frappe.log_error(f"Error calculating Basic: {str(e)}")
                B = 0
        
        # Calculate all components
        total = 0
        for earning in structure.earnings:
            if earning.formula:
                context = {
                    "base": doc.base,
                    "designation": employee.designation,
                    "B": B,
                    "b": B
                }
                try:
                    amount = eval(earning.formula, {}, context)
                    total += amount
                except Exception as e:
                    frappe.log_error(f"Error evaluating {earning.salary_component}: {str(e)}")
        
        # Calculate per day (÷30)
        per_day = total / 30 if total else 0
        
        # Set the field
        doc.leave_encashment_amount_per_day = per_day
        
        frappe.msgprint(
            _(f"✅ Leave Encashment Per Day calculated: {per_day:.2f}"),
            alert=True
        )
        
    except Exception as e:
        frappe.log_error(f"Error in leave encashment calculation: {str(e)}")
        doc.leave_encashment_amount_per_day = 0