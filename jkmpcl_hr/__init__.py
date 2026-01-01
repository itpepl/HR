__version__ = "0.0.1"


# ========================================================= 
# If leave type is Comp Off then skip overlap validation
# =========================================================

from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation
from jkmpcl_hr.overrides.leave_allocation import custom_validate_allocation_overlap

LeaveAllocation.validate_allocation_overlap = custom_validate_allocation_overlap


# =========================================================
# if leave type is Medical Emergency Leave then skip balance check
# =========================================================

from hrms.hr.doctype.leave_application.leave_application import LeaveApplication
from jkmpcl_hr.overrides.leave_application_override import custom_validate_balance_leaves

LeaveApplication.validate_balance_leaves = custom_validate_balance_leaves