__version__ = "0.0.1"


from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation
from jkmpcl_hr.overrides.leave_allocation import custom_validate_allocation_overlap

LeaveAllocation.validate_allocation_overlap = custom_validate_allocation_overlap
