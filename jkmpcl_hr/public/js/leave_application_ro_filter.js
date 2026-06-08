// frappe.listview_settings["Leave Application"] = {
// 	onload: function (list_view) {

// 		if (list_view.custom_filter_applied) return;

// 		frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name")
// 		.then(res => {
// 			let emp = res.message.name;
// 			if (!emp) return;

// 			frappe.call({
// 				method: "frappe.client.get_list",
// 				args: {
// 					doctype: "Employee",
// 					filters: { "reports_to": emp },
// 					pluck: "name",
// 					limit_page_length: 1000
// 				},
// 				callback: function (r) {

// 					let employee_list = (r.message || []).map(e => 
// 	          typeof e === "object" ? e.name : e
//           );

// 					// include self
// 					if (!employee_list.includes(emp)) {
// 						employee_list.push(emp);
// 					}

//           if (list_view.filter_area) {
//             list_view.filter_area.clear();
//           }

// 					list_view.filter_area.add([
// 						["Leave Application", "employee", "in", employee_list],
//             ["Leave Application", "workflow_state", "Equals", "Pending"]
// 					]);

// 					list_view.custom_filter_applied = true;
// 				}
// 			});
// 		});


// 		if (list_view.current_month_filter_applied) {
// 			return;
// 		}

// 		let today = frappe.datetime.get_today();
// 		let start_date = frappe.datetime.month_start(today);
// 		let end_date = frappe.datetime.month_end(today);

// 		// Leave overlaps current month
// 		list_view.filter_area.add([
// 			["Leave Application", "from_date", "<=", end_date],
// 			["Leave Application", "to_date", ">=", start_date]
// 		]);

// 		list_view.current_month_filter_applied = true;
// 		list_view.refresh();
// 	}
// };



frappe.listview_settings["Leave Application"] = {
	onload(list_view) {

		if (list_view.custom_filter_applied) return;

		const today = frappe.datetime.get_today();
		const start_date = frappe.datetime.month_start(today);
		const end_date = frappe.datetime.month_end(today);

		// Always apply current month filter
		list_view.filter_area.add([
			["Leave Application", "from_date", "<=", end_date]
		]);

		list_view.filter_area.add([
			["Leave Application", "to_date", ">=", start_date]
		]);

		frappe.db.get_value(
			"Employee",
			{ user_id: frappe.session.user },
			"name"
		).then((res) => {

			const emp = res.message?.name;

			// Administrator or user without Employee mapping
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

					// Employee filter
					list_view.filter_area.add([
						["Leave Application", "employee", "in", employee_list]
					]);

					// Pending workflow filter
					list_view.filter_area.add([
						["Leave Application", "workflow_state", "=", "Pending"]
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