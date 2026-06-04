frappe.listview_settings["Attendance Request"] = {
	onload: function (list_view) {

		if (list_view.custom_filter_applied) return;

		frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name")
		.then(res => {
			let emp = res.message.name;
			if (!emp) return;

			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Employee",
					filters: { "reports_to": emp },
					pluck: "name",
					limit_page_length: 1000
				},
				callback: function (r) {

					let employee_list = (r.message || []).map(e => 
	          typeof e === "object" ? e.name : e
          );

					// include self
					if (!employee_list.includes(emp)) {
						employee_list.push(emp);
					}

          if (list_view.filter_area) {
            list_view.filter_area.clear();
          }

					list_view.filter_area.add([
						["Attendance Request", "employee", "in", employee_list],
            ["Attendance Request", "workflow_state", "Equals", "Pending"]
					]);

					list_view.custom_filter_applied = true;
				}
			});
		});
		// list view filter code start
		if (list_view.current_month_filter_applied) {
			return;
		}

		let today = frappe.datetime.get_today();
		let start_date = frappe.datetime.month_start(today);
		let end_date = frappe.datetime.month_end(today);

		
		if (list_view.filter_area) {
			list_view.filter_area.add([
				["Attendance Request", "from_date", ">=", start_date],
				["Attendance Request", "from_date", "<=", end_date]
			]);

		}
		list_view.current_month_filter_applied = true;

		setTimeout(() => {
			list_view.refresh();
		}, 500);
	}
};