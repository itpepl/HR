frappe.listview_settings["Off-Day Work Request"] = {
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
						["Off-Day Work Request", "employee", "in", employee_list],
            ["Off-Day Work Request", "workflow_state", "Equals", "Pending"]
					]);

					list_view.custom_filter_applied = true;
				}
			});
		});
		if (list_view.current_month_filter_applied) {
            return;
        }

			const today = frappe.datetime.get_today();
			const start_date = frappe.datetime.month_start(today);
			const end_date = frappe.datetime.month_end(today);

			list_view.filter_area.add([
				["Off-Day Work Request", "date", ">=", start_date],
				["Off-Day Work Request", "date", "<=", end_date]
			]);

			list_view.current_month_filter_applied = true;
			list_view.refresh();
		}
};