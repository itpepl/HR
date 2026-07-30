// FSR - Field Staff / TA-DA Report
frappe.query_reports["FSR"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": "120px"
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": "120px"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1,
			"width": "80px"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "80px"
		}
	],

	onload: function(report) {
		set_default_dates(report);
	},

	refresh: function(report) {
		set_default_dates(report);
	},

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.is_total_row) {
			value = "<b>" + value + "</b>";
		}
		if (data && data.is_group_header) {
			value = "<b>" + value + "</b>";
		}
		return value;
	}
};

function set_default_dates(report) {
	const today = frappe.datetime.get_today();
	const month_start = frappe.datetime.month_start();

	const from = report.get_filter("from_date");
	const to = report.get_filter("to_date");

	from.df.max_date = today;
	to.df.max_date = today;

	if (!from.get_value()) {
		from.set_value(month_start);
	}

	if (!to.get_value()) {
		to.set_value(today);
	}

	from.refresh();
	to.refresh();
}