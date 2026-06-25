frappe.ui.form.off("Leave Application", "make_dashboard")

frappe.ui.form.on("Leave Application", {
    onload(frm) {        
        toggle_comp_off_fields(frm, false);
        set_leave_type_query_extended(frm);
        toggle_maternity_fields(frm)
    },

    employee(frm) {
        toggle_comp_off_fields(frm, true);
        fetch_reporting_manager(frm);
        set_leave_type_query_extended(frm);
        if(frm.doc.leave_type) {
            set_ml_leave_dates(frm)            
        }
    },
    leave_type(frm) {
        
        frm.set_value("from_date", null);
        frm.set_value("to_date", null);
        frm.set_value("half_day_date", null);

        toggle_comp_off_fields(frm, true);
        toggle_maternity_fields(frm);
        validate_for_maternity_leave(frm)

        if (frm.doc.employee) {
            set_ml_leave_dates(frm)
        }

        frm.set_df_property("custom_proof_document", "reqd", 0);
        frm.set_df_property("description", "reqd", 0);

        if (!frm.doc.leave_type) return;
        frappe.call({
            method: "jkmpcl_hr.py.leave_application.get_leave_type",
            args: {
                leave_type: frm.doc.leave_type
            },
            callback(r) {
                if (!r.message) return;

                const leave_type = r.message.custom_leave_type;
                if (leave_type === "Medical Emergency Leave") {
                    frm.set_df_property("custom_proof_document", "reqd", 1);
                    frm.set_df_property("description", "reqd", 1);
                }
                console.log("sadasdas", leave_type)
                if (leave_type === "Leave Without Pay") {
                    frm.set_df_property("custom_proof_document", "reqd", 1);                    
                }

                if (leave_type === "Sick Leave" && frm.doc.total_leave_days > 2) {
                    frm.set_df_property("custom_proof_document", "reqd", 1);                    
                }
            }
        });
    },

    custom_maternity_leave_type(frm) {
        set_ml_leave_dates(frm)
    },

    custom_no_of_surviving_children(frm) {
        validate_for_maternity_leave(frm)
    },

    custom_adopting_child_age(frm) {
        validate_for_maternity_leave(frm)  
    },

    from_date(frm) {
        toggle_comp_off_fields(frm, true);
        set_leave_type_query_extended(frm);
        set_ml_leave_dates(frm);
    },
    to_date(frm) {
        toggle_comp_off_fields(frm, true);
        set_leave_type_query_extended(frm);
    },

    total_leave_days(frm) {
        if (frm.doc.leave_type === "Sick Leave" && frm.doc.total_leave_days > 2) {
            frm.set_df_property("custom_proof_document", "reqd", 1);                    
        }
    },

    make_dashboard: function (frm) {
		let leave_details;
		let lwps;
	
		if (frm.doc.employee) {
			frappe.call({
				method: "jkmpcl_hr.py.leave_application.custom_get_leave_details",
				async: false,
				args: {
					employee: frm.doc.employee,
					date: frm.doc.from_date || frm.doc.posting_date,
				},
				callback: function (r) {
					if (!r.exc && r.message["leave_allocation"]) {
						leave_details = r.message["leave_allocation"];
					}
					lwps = r.message["lwps"];
				},
			});
	
			$("div").remove(".form-dashboard-section.custom");
	
			// Dynamically build the dashboard HTML
			let html_str = "";
			if (leave_details && Object.keys(leave_details).length > 0) {
				html_str += '<table class="table table-bordered small">';
				html_str += '<thead><tr>';
				html_str += '<th style="width: 14%">Leave Type</th>';
				html_str += '<th style="width: 14%" class="text-right">Total Allocated Leaves</th>';
				html_str += '<th style="width: 14%" class="text-right">Expired Leaves</th>';
				html_str += '<th style="width: 14%" class="text-right">Used Leaves</th>';
				html_str += '<th style="width: 14%" class="text-right">Penalized Leaves</th>';
				html_str += '<th style="width: 14%" class="text-right">Leaves Pending Approval</th>';
				html_str += '<th style="width: 14%" class="text-right">Available Leaves</th>';
				html_str += '</tr></thead><tbody>';
	
				Object.entries(leave_details).forEach(([key, value]) => {
					const color = cint(value["remaining_leaves"]) > 0 ? "green" : "red";
					html_str += '<tr>';
					html_str += `<td>${key}</td>`;
					html_str += `<td class="text-right">${value["total_leaves"] ?? ""}</td>`;
					html_str += `<td class="text-right">${value["expired_leaves"] ?? ""}</td>`;
					html_str += `<td class="text-right">${value["leaves_taken"] ?? ""}</td>`;
					html_str += `<td class="text-right">${value["penalized_leaves"] ?? ""}</td>`;
					html_str += `<td class="text-right">${value["leaves_pending_approval"] ?? ""}</td>`;
					html_str += `<td class="text-right" style="color:${color}">${value["remaining_leaves"] ?? ""}</td>`;
					html_str += '</tr>';
				});
				html_str += '</tbody></table>';
			} else {
				html_str = '<p style="margin-top: 30px;">No leaves have been allocated.</p>';
			}
	
			frm.dashboard.add_section(html_str, __("Allocated Leaves"));
			frm.dashboard.show();
	
			let allowed_leave_types = leave_details ? Object.keys(leave_details) : [];
			allowed_leave_types = allowed_leave_types.concat(lwps);
			frm.set_query("leave_type", function () {
				return {
					filters: [["leave_type_name", "in", allowed_leave_types]],
				};
			});
		}
	},
    // # off day and leave allocation cleanup code start
    refresh: function(frm) {
            console.log("=== Leave Application form loaded ===");
            
            // Override the _cancel_all method
            frm._cancel_all = function(r, btn, callback, on_error) {
                const me = this;
                
                console.log("=== Starting _cancel_all override ===");
                console.log("Linked Docs:", r.message.docs);
                
                let links = r.message.docs;
                
                // Filter out Off-Day Work Request and Leave Allocation from cancellation
                let docs_to_cancel = links.filter(link => 
                    link.doctype !== "Off-Day Work Request" && 
                    link.doctype !== "Leave Allocation"
                );
                
                console.log("Docs to cancel:", docs_to_cancel);
                console.log("Docs to clean only:", links.filter(link => 
                    link.doctype === "Off-Day Work Request" || 
                    link.doctype === "Leave Allocation"
                ));
                
                // Build the list of documents to show in confirmation
                const doctypes = Array.from(new Set(links.map((link) => link.doctype)));
                
                let links_text = "";
                me.ignore_doctypes_on_cancel_all = me.ignore_doctypes_on_cancel_all || [];
                
                for (let doctype of doctypes) {
                    if (!me.ignore_doctypes_on_cancel_all.includes(doctype)) {
                        let docnames = links
                            .filter((link) => link.doctype == doctype)
                            .map((link) => frappe.utils.get_form_link(link.doctype, link.name, true))
                            .join(", ");
                        links_text += `<li><strong>${__(doctype)}</strong>: ${docnames}</li>`;
                    }
                }
                links_text = `<ul>${links_text}</ul>`;
                
                let confirm_message = __("{0} {1} is linked with the following submitted documents: {2}", [
                    __(me.doc.doctype).bold(),
                    me.doc.name,
                    links_text,
                ]);
                
                let can_cancel = docs_to_cancel.every((link) => frappe.model.can_cancel(link.doctype));
                console.log("Can cancel docs:", can_cancel);
                
                if (can_cancel) {
                    confirm_message += __(" Do you want to cancel this document? Note: Off-Day Work Request and its linked Leave Allocation will only be cleaned (references removed) but not canceled.");
                } else {
                    confirm_message += __(" You do not have permissions to cancel this document.");
                }
                
                let d = new frappe.ui.Dialog({
                    title: __("Cancel Documents"),
                    fields: [
                        {
                            fieldtype: "HTML",
                            options: `<p class="frappe-confirm-message">${confirm_message}</p>`,
                        },
                    ],
                }, () => me.handle_save_fail(btn, on_error));
                
                if (can_cancel) {
                    d.set_primary_action(__("Confirm Cancel"), () => {
                        d.hide();
                        
                        console.log("=== Calling server cleanup_and_cancel ===");
                        
                        // Call server method
                        frappe.call({
                            method: "jkmpcl_hr.py.leave_application.cleanup_and_cancel",
                            args: {
                                docs: links,
                                doctype: me.doc.doctype,
                                docname: me.doc.name,
                                ignore_doctypes_on_cancel_all: me.ignore_doctypes_on_cancel_all || [],
                            },
                            freeze: true,
                            freeze_message: __("Cleaning up references and canceling..."),
                            callback: (resp) => {
                                console.log("Server response:", resp);
                                if (!resp.exc && resp.message && resp.message.success) {
                                    console.log("Cleanup and cancellation completed successfully");
                                    frappe.msgprint({
                                        title: __("Success"),
                                        indicator: "green",
                                        message: __("Document canceled successfully. All references have been cleaned.")
                                    });
                                    me.reload_doc();
                                    // Call the actual cancel method
                                    me._cancel(btn, callback, on_error, true);
                                } else {
                                    console.error("Error in cleanup and cancellation:", resp);
                                    frappe.msgprint({
                                        title: __("Error"),
                                        indicator: "red",
                                        message: __("Error in cleanup and cancellation. Please cancel linked document.")
                                    });
                                    me.handle_save_fail(btn, on_error);
                                }
                            },
                            error: function(error) {
                                console.error("Error calling server method:", error);
                                frappe.msgprint({
                                    title: __("Error"),
                                    indicator: "red",
                                    message: __("Error calling server method. Please check Error Log for details.")
                                });
                                me.handle_save_fail(btn, on_error);
                            }
                        });
                    });
                }
                d.show();
            };
            
            // Override _cancel method to handle the actual cancellation
            frm._cancel = function(btn, callback, on_error, skip_confirm) {
                const me = this;
                const cancel_doc = () => {
                    frappe.validated = true;
                    me.script_manager.trigger("before_cancel").then(() => {
                        if (!frappe.validated) {
                            return me.handle_save_fail(btn, on_error);
                        }
                        
                        var after_cancel = function (r) {
                            if (r.exc) {
                                me.handle_save_fail(btn, on_error);
                            } else {
                                frappe.utils.play_sound("cancel");
                                me.refresh();
                                callback && callback();
                                me.script_manager.trigger("after_cancel");
                            }
                        };
                        frappe.ui.form.save(me, "cancel", after_cancel, btn);
                    });
                };
                
                if (skip_confirm) {
                    cancel_doc();
                } else {
                    frappe.confirm(
                        __("Permanently Cancel {0}?", [this.docname]),
                        cancel_doc,
                        me.handle_save_fail(btn, on_error)
                    );
                }
            };
        }
// off day and leave allocation cleanup code end
});

function fetch_reporting_manager(frm) {
    
    frappe.call({
        method: "jkmpcl_hr.py.utils.get_emp_reporting_manager",
        args: {
            emp_id: frm.doc.employee
        },
        callback(r) {
            if (!r.message) return;

            frm.set_value("leave_approver", r.message);
        }
    });
}

function toggle_comp_off_fields(frm, validate = false) {
    frm.set_df_property("custom_off_day_work_request", "hidden", 1);
    frm.set_df_property("custom_off_day_date", "hidden", 1);

    if (!frm.doc.leave_type) return;

    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;

            const is_comp_off = r.message.is_compensatory;

            if (!is_comp_off) {
                frm.set_df_property("custom_off_day_work_request", "hidden", 1);
                frm.set_df_property("custom_off_day_date", "hidden", 1);

                if (frm.doc.custom_off_day_work_request) {
                    frm.set_value("custom_off_day_work_request", null);
                }

                if (frm.doc.custom_off_day_date) {
                    frm.set_value("custom_off_day_date", null);
                }
                
                frm.refresh_fields();
                return;
            }

            frm.set_df_property("custom_off_day_work_request", "hidden", 0);
            frm.set_df_property("custom_off_day_date", "hidden", 0);

            if (!validate) return;

            fetch_valid_comp_off(frm, r.message.name);
        }
    })
}

function toggle_maternity_fields(frm) {


    frm.set_df_property("custom_maternity_leave_type", "hidden", 1)
    frm.set_df_property("custom_no_of_surviving_children", "hidden", 1)
    frm.set_df_property("custom_adopting_child_age", "hidden", 1)   

    frm.set_df_property("custom_maternity_leave_type", "reqd", 0);
    frm.set_df_property("custom_no_of_surviving_children", "reqd", 0);
    frm.set_df_property("custom_adopting_child_age", "reqd", 0);
    

    frm.set_df_property("to_date", "read_only", 0);
    
    if (!frm.doc.leave_type) return;
    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;

            const leave_type = r.message.custom_leave_type;
            if (leave_type === "Maternity Leave" || leave_type === "Special Maternity Leave") {
                frm.set_df_property("custom_maternity_leave_type", "hidden", 0);
                frm.set_df_property("custom_no_of_surviving_children", "hidden", 0)
                frm.set_df_property("custom_maternity_leave_type", "reqd", 1);                    
                frm.set_df_property("custom_no_of_surviving_children", "reqd", 1);
                frm.set_df_property("to_date", "read_only", 1);
                frm.set_df_property("custom_proof_document", "reqd", 1);

            }

            if (leave_type === "Child Adoption Leave") {
                frm.set_df_property("custom_adopting_child_age", "hidden", 0)
                frm.set_df_property("custom_no_of_surviving_children", "hidden", 0)

                frm.set_df_property("custom_no_of_surviving_children", "reqd", 1);
                frm.set_df_property("custom_adopting_child_age", "reqd", 1);
                frm.set_df_property("description", "reqd", 1);
                frm.set_df_property("custom_proof_document", "reqd", 1);


                frm.set_df_property("to_date", "read_only", 1);
            }

        }
    });    

}

function fetch_valid_comp_off(frm, leave_type_name) {

    if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date || !frm.doc.leave_type) return;

    if (frm.doc.from_date !== frm.doc.to_date) {
        frappe.throw("For Compensatory Off, From Date and To Date must be the same.");
    }

    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_valid_comp_off",
        args: {
            employee: frm.doc.employee,
            leave_date: frm.doc.from_date,
            leave_type_name: leave_type_name
        },
        callback(r) {
            if (!r.message) {
                frm.set_value("custom_off_day_work_request", null);
                frm.set_value("custom_off_day_date", null);

                // frappe.throw({
                //     title: __("No Valid Comp-Off"),
                //     message: __("No valid Compensatory Off found for the selected date."),
                //     indicator: "red"
                // });
                return;
            }
            const comp_off_record_name = r.message.name;
            const comp_off_date = r.message.date;

            frm.set_value("custom_off_day_work_request", comp_off_record_name);
            frm.set_value("custom_off_day_date", comp_off_date);
        }
    });
}


async function set_leave_type_query_extended(frm) {
    console.log("Setting extended leave type query...");
    let leave_details = {};
    let lwps = [];

    // if (!frm.doc.employee) return;
    if (!frm.doc.employee) {
        frm.set_query("leave_type", function () {
            return {
                filters: {
                    "custom_leave_type": ["not in", ["Maternity Leave", "Child Adoption Leave", "Special Maternity Leave"]]
                }
            };
        });
        return; 
    }
    
    // Call default ERPNext method
    const r = await frappe.call({
        method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
        args: {
            employee: frm.doc.employee,
            date: frm.doc.from_date || frm.doc.posting_date
        }
    });

    if (r.exc || !r.message) return;


    leave_details = r.message.leave_allocation || {};
    lwps = r.message.lwps || [];

    // Default allowed leave types (Allocated + LWP)
    let allowed_leave_types = Object.keys(leave_details).concat(lwps);

    // Fetch OPEN leave types from Python (permission-safe)
    const open_leave_res = await frappe.call({
            method: "jkmpcl_hr.py.leave_application.get_open_leave_types",
            args: {
                employee: frm.doc.employee || null,
            }
        });

    
    const open_leave_types = open_leave_res.message || [];

    // Append + remove duplicates
    allowed_leave_types = [...new Set(
        allowed_leave_types.concat(open_leave_types)
    )];

    // Apply final query
    frm.set_query("leave_type", function () {
        return {
            filters: [["leave_type_name", "in", allowed_leave_types]]
        };
    });
}


function set_ml_leave_dates(frm) {

    if (!frm.doc.leave_type) return;
    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;

            const leave_type = r.message.custom_leave_type;
            if (leave_type !== "Child Adoption Leave" && leave_type !== "Maternity Leave" && leave_type !== "Special Maternity Leave") {
                // frm.set_value("to_date", null);
                // frm.set_value("from_date", null);        
                return;
            }
            
            let from_date = frm.doc.from_date ? frappe.datetime.str_to_obj(frm.doc.from_date) : frappe.datetime.get_today();
            if (!frm.doc.from_date) {
                frm.set_value("from_date", frappe.datetime.obj_to_str(from_date));
            }

            frappe.call({
                method: "jkmpcl_hr.py.leave_application.get_days_for_ml",
                args: {
                    employee: frm.doc.employee,
                    leave_type: leave_type,
                    maternity_leave_type: frm.doc.custom_maternity_leave_type,
                    from_date: frm.doc.from_date
                },
                async callback(r) {
                    if (!r.message) return;
                    let to_date = from_date;
                    const leave_days = r.message - 1;
                    console.log("Days for ML:", leave_days);
                    to_date = frappe.datetime.add_days(from_date, leave_days);
                    frm.set_value("to_date", frappe.datetime.obj_to_str(to_date));

                }
            });

            // let to_date = from_date;
            // if ((frm.doc.custom_maternity_leave_type === "Miscarriage" || frm.doc.custom_maternity_leave_type === "Abortion") && leave_type !== "Child Adoption Leave") {
            //     console.log("This is getting called")
            //     to_date = frappe.datetime.add_days(from_date, 41);
            // }
            // else if (frm.doc.custom_maternity_leave_type === "Normal" || leave_type === "Child Adoption Leave") {
            //     to_date = frappe.datetime.add_days(from_date, 89);
            // }
            
        
            // frm.set_value("to_date", frappe.datetime.obj_to_str(to_date));
        }
    });    
}


function validate_for_maternity_leave(frm) {
    frappe.call({
        method: "jkmpcl_hr.py.leave_application.get_leave_type",
        args: {
            leave_type: frm.doc.leave_type
        },
        callback(r) {
            if (!r.message) return;
            const leave_type = r.message.custom_leave_type;
            if (leave_type !== "Child Adoption Leave" && leave_type !== "Maternity Leave" && leave_type !== "Special Maternity Leave") {   
                return;
            }

            if (frm.doc.custom_no_of_surviving_children > 2) {
                frappe.throw("You are not eligible for " + leave_type + ". Please Choose another Leave Type.");
            }

            if (leave_type==="Child Adoption Leave" && frm.doc.custom_adopting_child_age > 1) {
                frappe.throw("You are not eligible for Child Adoption Leave. Please Choose another Leave Type.");
            }
        }
    });
}