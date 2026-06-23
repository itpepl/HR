frappe.listview_settings["Tour Request"] = {
	onload(list_view) {

		if (list_view.custom_filter_applied) {
			return;
		}

		const today = frappe.datetime.get_today();
		const start_date = frappe.datetime.month_start(today);
		const end_date = frappe.datetime.month_end(today);

		// Always apply current month filter for travel_request_date
		list_view.filter_area.add([
			["Tour Request", "travel_request_date", "between", [start_date, end_date]]
		]);

		frappe.db.get_value(
			"Employee",
			{ user_id: frappe.session.user },
			"name"
		).then((res) => {

			const emp = res.message?.name;

			// Administrator or user without Employee record
			if (!emp) {
				list_view.custom_filter_applied = true;
				list_view.refresh();
				return;
			}

			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Employee",
					filters: {
						reports_to: emp
					},
					fields: ["name"],
					limit_page_length: 1000
				},
				callback(r) {

					let employee_list = (r.message || []).map(d => d.name);

					if (!employee_list.includes(emp)) {
						employee_list.push(emp);
					}

					// Filter by employee (self and subordinates)
					list_view.filter_area.add([
						["Tour Request", "employee", "in", employee_list]
					]);

					// Filter by workflow_state = "Pending"
					list_view.filter_area.add([
						["Tour Request", "workflow_state", "=", "Pending"]
					]);

					list_view.custom_filter_applied = true;

					setTimeout(() => {
						list_view.refresh();
					}, 300);
				}
			});
		});
	}
};