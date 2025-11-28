frappe.ui.form.on("Employee", {
    department: async function (frm) {
        if (!frm.is_new()) return;

        const child_tables = [
            "custom_reporting_manager",
            "custom_review_manager",
            "custom_hr_manager"
        ];

        // clear all child tables
        child_tables.forEach(tbl => frm.clear_table(tbl));
        if (!frm.doc.department) {
            child_tables.forEach(tbl => frm.refresh_field(tbl));
            return;
        }

        // reference date: use date_of_joining if provided else today's date
        const ref_date = frappe.datetime.get_today();
        const refTime = new Date(ref_date).getTime();

        // fetch data for all three tables at once
        const all_data = await frappe.xcall('jkmpcl_hr.py.api.get_reporting_managers', {
            department: frm.doc.department
        }).catch(() => ({}));

        // populate each child table from the result
        for (const parentfield of child_tables) {
            const rows = all_data[parentfield] || [];

            if (!rows.length) {
                frm.refresh_field(parentfield);
                continue;
            }

            // keep entries with effective_from, sort ascending
            const sorted = rows
                .filter(r => r.effective_from)
                .map(r => ({
                    employee: r.employee,
                    role: r.role,
                    user: r.user,
                    effective_from: r.effective_from
                }))
                .sort((a, b) => new Date(a.effective_from) - new Date(b.effective_from));

            // find last index with effective_from <= ref_date
            let currentIndex = -1;
            for (let i = 0; i < sorted.length; i++) {
                if (new Date(sorted[i].effective_from).getTime() <= refTime) {
                    currentIndex = i;
                } else {
                    break;
                }
            }

            const startIndex = currentIndex >= 0 ? currentIndex : 0;

            for (let i = startIndex; i < sorted.length; i++) {
                const r = sorted[i];
                const child = frm.add_child(parentfield);
                child.effective_from = r.effective_from;
                child.role = r.role;
                child.user = r.user;
                child.employee = r.employee;
            }

            frm.refresh_field(parentfield);
        }
    }
});
