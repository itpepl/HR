frappe.listview_settings["Shift Request"] = {
	onload(list_view) {

		if (list_view.current_month_filter_applied) {
			return;
		}

		const today = frappe.datetime.get_today();
		const start_date = frappe.datetime.month_start(today);
		const end_date = frappe.datetime.month_end(today);

		list_view.filter_area.add([
			["Shift Request", "from_date", "<=", end_date],
			["Shift Request", "to_date", ">=", start_date]
		]);

		list_view.current_month_filter_applied = true;

		list_view.refresh();
	}
};