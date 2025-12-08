
frappe.ui.form.on("Shift Request", {
	setup: function (frm) {
        console.log("Hello")
        const current_user = frappe.session.user
          // * FETCHING CURRENT USER'S EMPLOYEE ID ADN SETTING IT IN THE employee FIELD IF THE employee FIELD HAS NO VALUE
         if (!frm.doc.employee){
            frappe.db.get_value("Employee", {"user_id": current_user}, "name").then(r =>{
                if(r.message.name){

                    emp_id = r.message.name
                    as_on_date = frm.doc.from_date?frm.doc.from_date:frappe.datetime.get_today()
                    frm.set_value("employee", emp_id)
                    frm.refresh_field("employee")
          
                    get_emp_reporting_manager_user(frm)
                   
                }
            })
        }
        
	},

    refresh:function(frm){
        console.log("REFERESH", frm.doc.branch)
        const current_user = frappe.session.user
      

        // * HIDING sbumit BUTTON AND MAKING status FIELD read only IF THE CURRENT USER IS NOT THE APPROVER AND IF THE CURRENT USER IS APPROVER THEN DISPLAYING THE submit BUTTON AND MAKING status FIELD EDITABLE
        // $('.primary-action').prop('hidden', true);
        $('button[data-label="Submit"]').hide();


        frm.set_df_property("status", "read_only", 1);

        if (frm.doc.approver && current_user === frm.doc.approver){
            $('button[data-label="Submit"]').show();
            
            frm.set_df_property("status", "read_only", 0);
        }
        else{
            if(frm.doc.employee){
                 frappe.call({
                    method: "jkmpcl_hr.py.utils.get_emp_reporting_manager",
                    args:{
                            emp_id: frm.doc.employee,
                            as_on_date: frm.doc.from_date?frm.doc.from_date:frappe.datetime.get_today()
                    },  
                    callback: function(res){
                        if(res.message ){
                            if (res.message === current_user){
                                // $('.primary-action').prop('disabled', false);
                                // $('.primary-action').prop('hidden', false);
                                $('button[data-label="Submit"]').show();

                                frm.set_df_property("status", "read_only", 0);                    
                            }       
                        }
                    }
                })
            }
        }


        // * APPLYNNG FILTER TO THE shift_type FIELD
        // if (frm.doc.custom_branch){
            apply_filter_in_shift_type(frm)
        // }
        


    },
    from_date: function(frm){
        get_emp_reporting_manager_user(frm)
        if(frm.doc.from_date){
            apply_filter_in_shift_type(frm)

            frappe.call({
                method: "jkmpcl_hr.py.shift_request.validate_shift_hours",
                args:{
                    doc: frm.doc
                }
            })
        }
    },

    to_date: function(frm){
        if(frm.doc.to_date){
            frappe.call({
                method: "jkmpcl_hr.py.shift_request.validate_shift_hours",
                args:{
                    doc: frm.doc
                }
            })
        }
    }
});


// * FUNCTION TO GET THE APPROVER OF THE EMPLOYEE
function get_emp_reporting_manager_user(frm){
    frappe.call({
        method: "jkmpcl_hr.py.utils.get_emp_reporting_manager",
        args:{
                emp_id: frm.doc.employee,
                as_on_date: frm.doc.from_date?frm.doc.from_date:frappe.datetime.get_today()
        },  
        callback: function(res){
            if(res.message){
                frm.set_value("approver", res.message)
                frm.refresh_field("approver")
            }
        }
    })
}


// * FUNCTION TO APPLY FILTER ON shift_type FIELD
function apply_filter_in_shift_type(frm){
    frm.set_query("shift_type", function () {
        return {
            query: "jkmpcl_hr.py.api.determine_shift_types",
            filters: {
                branch: frm.doc.custom_branch,
                as_on_date: frm.doc.from_date || frappe.datetime.get_today()
            }
        };
    });
}