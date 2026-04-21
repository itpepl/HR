app_name = "jkmpcl_hr"
app_title = "JKMPCL HR"
app_publisher = "SanskarTechnolab"
app_description = "Custom app for hrms customization"
app_email = "ayush@sanskartechnolab.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "jkmpcl_hr",
# 		"logo": "/assets/jkmpcl_hr/logo.png",
# 		"title": "JKMPCL HR",
# 		"route": "/jkmpcl_hr",
# 		"has_permission": "jkmpcl_hr.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/jkmpcl_hr/css/jkmpcl_hr.css"
# app_include_js = "/assets/jkmpcl_hr/js/jkmpcl_hr.js"

# include js, css files in header of web template
# web_include_css = "/assets/jkmpcl_hr/css/jkmpcl_hr.css"
# web_include_js = "/assets/jkmpcl_hr/js/jkmpcl_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "jkmpcl_hr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
                "Employee" : "public/js/employee.js",
                "Department" : "public/js/department.js",
                "Attendance Request": "public/js/attendance_request.js",
                "Shift Request": "public/js/shift_request.js",
                "HR Settings":"public/js/hr_settings.js",
                "Leave Application":"public/js/leave_application.js",
                "Leave Allocation": "public/js/leave_allocation.js"
            }
# doctype_list_js = {"doctype" : "public/js/attendance_request_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
doctype_list_js = {
    "Attendance": "public/js/attendance_list.js"
}
# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "jkmpcl_hr/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "jkmpcl_hr.utils.jinja_methods",
# 	"filters": "jkmpcl_hr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "jkmpcl_hr.install.before_install"
# after_install = "jkmpcl_hr.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "jkmpcl_hr.uninstall.before_uninstall"
# after_uninstall = "jkmpcl_hr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "jkmpcl_hr.utils.before_app_install"
# after_app_install = "jkmpcl_hr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "jkmpcl_hr.utils.before_app_uninstall"
# after_app_uninstall = "jkmpcl_hr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "jkmpcl_hr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Override doctype
override_doctype_class = {
    "Attendance Request": "jkmpcl_hr.overrides.attendance_request.AttendanceRequest",
    "Shift Request":"jkmpcl_hr.overrides.shift_request_override.CustomShiftRequest",
    "Leave Allocation": "jkmpcl_hr.overrides.leave_allocation.CustomLeaveAllocation",
    "Attendance": "jkmpcl_hr.overrides.attendance.Attendance",
    "Salary Slip": "jkmpcl_hr.overrides.salary_slip_override.CustomSalarySlip",
    "Leave Application": "jkmpcl_hr.overrides.leave_application_override.CustomLeaveApplication"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Department": {
        "on_update": "jkmpcl_hr.py.department.on_update"
    },
    "Shift Request": {
        "validate": "jkmpcl_hr.py.shift_request.validate",
        "on_submit": "jkmpcl_hr.py.shift_request.on_submit"
    },
    "Employee": {
        "after_insert": "jkmpcl_hr.py.employee.after_insert",
        "on_update": "jkmpcl_hr.py.employee.on_update",
        "validate": "jkmpcl_hr.py.employee.validate"
    },
    "Leave Application": {
        "validate": [
           "jkmpcl_hr.py.leave_application.validate",
           "jkmpcl_hr.py.api.block_suspended_employee",
        ],
        "on_submit" : [
            "jkmpcl_hr.py.leave_application.on_submit",
            "jkmpcl_hr.py.scheduler_method.on_leave_application_approved",
        ],
        "before_submit":"jkmpcl_hr.py.leave_application.before_submit",
        "on_update":"jkmpcl_hr.py.leave_application.on_update",
        "on_update_after_submit": "jkmpcl_hr.py.scheduler_method.on_leave_application_approved",
    },
    "Holiday List": {
        "validate": "jkmpcl_hr.py.holiday_list.validate_weekly_off"
    },
    "Employee Transfer": {
        "on_submit":"jkmpcl_hr.py.employee_transfer.on_submit"
    },

    "Attendance Request": {
        "validate": "jkmpcl_hr.py.api.block_suspended_employee"
    },
    "Off-Day Work Request": {
        "validate": "jkmpcl_hr.py.api.block_suspended_employee"
    },
    "Shift Assignment": {
        "validate": "jkmpcl_hr.py.api.block_suspended_employee"
    },
    "Holiday List Assignment": {
        "validate": "jkmpcl_hr.py.api.block_suspended_employee"
    }

# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron":{
        "0 0 1 4 *": [
            "jkmpcl_hr.py.scheduler_method.create_shift_assignments",
            "jkmpcl_hr.py.scheduler_method.allocate_leaves_to_confirmed_employee"
        ],
         "0 9 * * *": [
            "jkmpcl_hr.py.scheduler_method.run_daily_attendance"
        ],
        "0 10 * * *": [
            "jkmpcl_hr.py.scheduler_method.process_comp_off_scheduler"
        ],
        "0 2 5 * *": [
            "jkmpcl_hr.py.pl_accrual.process_pl_after_payroll"
        ],
        "0 0 1 * *": [
            "jkmpcl_hr.py.scheduler_method.allocate_cl_to_probation_and_contract_employees"
        ],
        "0 0 * * *":[
            "jkmpcl_hr.py.scheduler_method.allocate_sl_to_probation_and_contract_employees",
            "jkmpcl_hr.py.scheduler_method.set_approvers_in_employee"
        ]
        
    }
# 	"all": [
# 		"jkmpcl_hr.tasks.all"
# 	],
# 	"daily": [
# 		"jkmpcl_hr.tasks.daily"
# 	],
# 	"hourly": [
# 		"jkmpcl_hr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"jkmpcl_hr.tasks.weekly"
# 	],
	
}

# Testing
# -------

# before_tests = "jkmpcl_hr.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "jkmpcl_hr.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	# "frappe.desk.doctype.event.event.get_events": "jkmpcl_hr.event.get_events"
    "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on": "jkmpcl_hr.overrides.leave_application_override.custom_get_leave_balance_on",
    "hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days": "jkmpcl_hr.overrides.leave_application_override.custom_get_number_of_leave_days"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "jkmpcl_hr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["jkmpcl_hr.utils.before_request"]
# after_request = ["jkmpcl_hr.utils.after_request"]

# Job Events
# ----------
# before_job = ["jkmpcl_hr.utils.before_job"]
# after_job = ["jkmpcl_hr.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"jkmpcl_hr.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

