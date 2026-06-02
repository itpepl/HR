frappe.listview_settings["Employee Checkin"] = {
	onload(list_view) {

		if (list_view.current_month_filter_applied) {
			return;
		}

		const today = frappe.datetime.get_today();
		const start_date = frappe.datetime.month_start(today) + " 00:00:00";
		const end_date = frappe.datetime.month_end(today) + " 23:59:59";

		list_view.filter_area.add([
			["Employee Checkin", "time", ">=", start_date],
			["Employee Checkin", "time", "<=", end_date]
		]);

		list_view.current_month_filter_applied = true;

		list_view.refresh();
	}
};