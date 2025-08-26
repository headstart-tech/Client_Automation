tags_metadata = [{
    "name": "all_routes",
    "route_details": {
        "": {
            "description": "Retrieve the default apis",
            "name": "Default",
            "prefix": "",
            "routes": {"/": {"description": "Reed root", "type": "Public"}},
        },
        "admin": {
            "description": "Admin-related operations",
            "name": "Admin",
            "prefix": "admin",
            "routes": {
                "/add_comment_for_document/": {
                    "description": "Add comment for a document.",
                    "type": "Private",
                },
                "/add_leads_using_or_csv/": {
                    "description": "Add leads using csv file",
                    "type": "Private",
                },
                "/add_student/": {
                    "description": "Add a student data.",
                    "type": "Private",
                },
                "/all_applications/": {
                    "description": "Get all application details.",
                    "type": "Private",
                },
                "/all_applications_by_email/": {
                    "description": "Get all student application details by email.",
                    "type": "Private",
                },
                "/all_leads/": {
                    "description": "Get all students details.",
                    "type": "Private",
                },
                "/all_paid_applications/": {
                    "description": "Get all paid application details.",
                    "type": "Private",
                },
                "/application_funnel/{college_id}": {
                    "description": "Get the application funnel data by college id.",
                    "type": "Private",
                },
                "/applications_based_on_type/": {
                    "description": "Get list of applications based on type for admin.",
                    "type": "Private",
                },
                "/college_name": {
                    "description": "Returns the data of college associated with user.",
                    "type": "Private",
                },
                "/delete_comment/": {
                    "description": "Delete comment of a document.",
                    "type": "Private",
                },
                "/delete_student_by_email_id": {
                    "description": "Delete student data based on email ids.",
                    "type": "Private",
                },
                "/download_application_funnel_data/{college_id}": {
                    "description": "Download application funnel data based on college id.",
                    "type": "Private",
                },
                "/download_applications_data/": {
                    "description": "Download application data by ids, based on filter",
                    "type": "Private",
                },
                "/download_data/{college_id}": {
                    "description": "Download the unique data of Student's Admission status in form of csv file by "
                                   "college id.",
                    "type": "Private",
                },
                "/download_documents/{student_id}/": {
                    "description": "Download All Student Documents based on student id.",
                    "type": "Private",
                },
                "/download_form_stage_wise_segregation_data/{college_id}": {
                    "description": "Downloads student's admission detail/status according to college_id in csv format.",
                    "type": "Private",
                },
                "/download_form_wise_status_data/{college_id}": {
                    "description": "Downloads the csv file which stores the status of student's admission detail by Ids.",
                    "type": "Private",
                },
                "/download_lead_application_graph_data/{college_id}": {
                    "description": "Download the lead application graph data in csv format based on college id.",
                    "type": "Private",
                },
                "/download_lead_funnel_application_data/{college_id}": {
                    "description": "Downloads the unique code of get data in csv format of route 'declaration' by "
                                   "excluding unnecessary fields like 'payment_init_but_not_paid', 'payment_not_initiated',"
                                   " 'total_unpaid_application' based on college id.",
                    "type": "Private",
                },
                "/download_leads/": {
                    "description": "Download leads data by ids or based on filter.",
                    "type": "Private",
                },
                "/download_source_wise_details": {
                    "description": "Downloads the source wise details in form of csv file based on college_id.",
                    "type": "Private",
                },
                "/download_top_performing_channel_data/{college_id}": {
                    "description": "Download the data of top performing channels in csv format by college id.",
                    "type": "Private",
                },
                "/edit_comment/": {
                    "description": "Update comment of a document.",
                    "type": "Private",
                },
                "/filter/": {
                    "description": "Get all filters of user.",
                    "type": "Private",
                },
                "/filter/add/": {
                    "description": "Add/Save filter in the collection named users.",
                    "type": "Private",
                },
                "/filter/delete_by_name/": {
                    "description": "Delete filter by name.",
                    "type": "Private",
                },
                "/form_stage_wise/{college_id}": {
                    "description": "Perform form stage wise segregation based on college id.",
                    "type": "Private",
                },
                "/form_wise_record/{college_id}": {
                    "description": "Return the data of Student's Application form by college id.",
                    "type": "Private",
                },
                "/get_by_id/{student_id}/": {
                    "description": "Get student information using id.",
                    "type": "Private",
                },
                "/get_by_name/{student_name}/": {
                    "description": "Get student information using name.",
                    "type": "Private",
                },
                "/get_document_comments/": {
                    "description": "Get a document comments.",
                    "type": "Private",
                },
                "/get_external_links_of_student_documents/": {
                    "description": "Get external links of student documents.",
                    "type": "Private",
                },
                "/get_lead_detail_by_number": {
                    "description": "Get lead detail based on mobile number.",
                    "type": "Private",
                },
                "/get_source_name/": {
                    "description": "Get the list of unique utm sources.",
                    "type": "Private",
                },
                "/get_user_audit_details/": {
                    "description": "Get a list of user audit details.",
                    "type": "Private",
                },
                "/get_user_permission": {
                    "description": "Returns the permissions and menus of user according to role_type.",
                    "type": "Private",
                },
                "/get_usernames_by_pattern": {
                    "description": "Get the List of application details of username based on matched string of username.",
                    "type": "Private",
                },
                "/grant_extra_limits_to_ip_address/": {
                    "description": "Grant extra API limits to a given IP address.",
                    "type": "Private",
                },
                "/invalidate_cache/": {
                    "description": "Invalidated cache",
                    "type": "Public",
                },
                "/key_indicator/": {
                    "description": "Get key indicators information",
                    "type": "Private",
                },
                "/lead_application/{college_id}": {
                    "description": "Fetch lead applications based on college id.",
                    "type": "Private",
                },
                "/lead_funnel/{college_id}": {
                    "description": "Get lead funnel data based on college id",
                    "type": "Private",
                },
                "/login/": {"description": "Admin login.", "type": "Public"},
                "/post_application_stages_info/": {
                    "description": "Get post application stages info based on application id.",
                    "type": "Private",
                },
                "/remove_all/": {
                    "description": "Remove all students data.",
                    "type": "Private",
                },
                "/remove_by_id/{student_id}/": {
                    "description": "Remove student using id.",
                    "type": "Private",
                },
                "/remove_extra_limits_from_ip_address/": {
                    "description": "Remove extra API limits from a given IP address.",
                    "type": "Private",
                },
                "/remove_students_by_source_name/": {
                    "description": "Fetch list of removed student based on source name",
                    "type": "Private",
                },
                "/school_names/": {
                    "description": "Get school names.",
                    "type": "Private",
                },
                "/score_board/{college_id}": {
                    "description": "Returns the data of Admission status based on route 'score_board' and "
                                   "college_id and date_range.",
                    "type": "Private",
                },
                "/search_leads/": {
                    "description": "Get leads details by search pattern.",
                    "type": "Private",
                },
                "/search_students/": {
                    "description": "Search students details based on college id.",
                    "type": "Private",
                },
                "/send_student_document_to_board/": {
                    "description": "Send student document to respective board through mail for verification.",
                    "type": "Private",
                },
                "/source_wise_detail": {
                    "description": "Fetch source wise details.",
                    "type": "Private",
                },
                "/student_documents/": {
                    "description": "Get student uploaded document details.",
                    "type": "Private",
                },
                "/student_queries/": {
                    "description": "Get student queries information.",
                    "type": "Private",
                },
                "/student_queries_based_on_counselor/": {
                    "description": "Get the counselor wise student queries summary info.",
                    "type": "Private",
                },
                "/student_total_queries/": {
                    "description": "Get student queries total information.",
                    "type": "Private",
                },
                "/student_total_queries_header/": {
                    "description": "Get student total queries header information.",
                    "type": "Private",
                },
                "/top_performing_channel/{college_id}": {
                    "description": "Get the top performing channels data by college id.",
                    "type": "Private",
                },
                "/update_status_of_document/": {
                    "description": "Update status of an existing document.",
                    "type": "Private",
                },
                "/upload_colleges/": {
                    "description": "Upload colleges csv file to S3 then add csv data into database.",
                    "type": "Private",
                },
                "/upload_courses/": {
                    "description": "Upload courses csv file to S3 then add csv data into database.",
                    "type": "Private",
                },
                "/upload_files/": {
                    "description": "Upload files on amazon bucket.",
                    "type": "Public",
                },
                "/upload_single_file/": {
                    "description": "Upload file in amazon s3 bucket then add file data.",
                    "type": "Private",
                },
                "/upload_student_data/": {
                    "description": "Upload student data csv file to S3 then add csv data into database.",
                    "type": "Private",
                },
                "/upload_user_audit_details/": {
                    "description": "Upload user audit details into the database.",
                    "type": "Private",
                },
                "/users_by_college_id": {
                    "description": "Get list of users based on college id.",
                    "type": "Private",
                },
            },
        },
        "advance_filter": {
            "description": "Operations related to advance filter",
            "name": "Advance Filter",
            "prefix": "advance_filter",
            "routes": {
                "/categories_or_fields/": {
                    "description": "Get all advance filter categories.",
                    "type": "Private",
                }
            },
        },
        "application_wrapper": {
            "description": "Retrieve the application counts",
            "name": "Application",
            "prefix": "application_wrapper",
            "routes": {
                "/application_data_count": {
                    "description": "Get the lead data based on counts.",
                    "type": "Private",
                },
                "/today_application_count": {
                    "description": "Get the count of the application data.",
                    "type": "Private",
                },
            },
        },
        "automation": {
            "description": "Operations related to automation management",
            "name": "Automation",
            "prefix": "automation",
            "routes": {
                "/download_job_data/": {
                    "description": "Download automation job data by id and based on filter.",
                    "type": "Private",
                },
                "/download_job_details/": {
                    "description": "Download automation rule jobs details data by ids and based on filter.",
                    "type": "Private",
                },
                "/job_delivery_details_by_id/": {
                    "description": "Get automation job delivery details by id.",
                    "type": "Private",
                },
                "/job_details_by_id/": {
                    "description": "Get automation job details by id.",
                    "type": "Private",
                },
                "/rule_details/": {
                    "description": "Get automation rule details by id.",
                    "type": "Private",
                },
                "_beta/": {
                    "description": "Get all automations from collection named automation.",
                    "type": "Private",
                },
                "_beta/check_automation_name_exists_or_not/": {
                    "description": "Check automation name exist or not.",
                    "type": "Public",
                },
                "_beta/create/": {
                    "description": "Create automation and store it in the collection named automation.",
                    "type": "Private",
                },
                "_beta/get_by_name/": {
                    "description": "Get automation details by name.",
                    "type": "Private",
                },
                "_beta/update_status/": {
                    "description": "Change status of automation.",
                    "type": "Private",
                },
            },
        },
        "call_activities": {
            "description": "Operations related to call activity",
            "name": "Call Activity",
            "prefix": "call_activities",
            "routes": {
                "/add/": {
                    "description": "Store call activity data.",
                    "type": "Private",
                },
                "/counselor_leads_details/": {
                    "description": "Get counselor leads details like name and mobile number.",
                    "type": "Private",
                },
                "/counselor_wise_data/": {
                    "description": "Get the counselor-wise call activity data count.",
                    "type": "Private",
                },
                "/counselor_wise_inbound_report": {
                    "description": "Get all counselor wise inbound call activity details.",
                    "type": "Private",
                },
                "/counselor_wise_outbound_report": {
                    "description": "Get all counselor wise outbound call activity details.",
                    "type": "Private",
                },
                "/history/": {
                    "description": "Get counselor call history.",
                    "type": "Private",
                },
                "/one_glance_view": {
                    "description": "Fetch all call and total duration.",
                    "type": "Private",
                },
            },
        },
        "campaign": {
            "description": "Operations related to campaign",
            "name": "Campaign",
            "prefix": "campaign",
            "routes": {
                "/campaign_header": {
                    "description": "Fetch the campaign header for the given campaign details.",
                    "type": "Private",
                },
                "/check_rule_name_exist_or_not/": {
                    "description": "Check if the campaign rule name exist or not.",
                    "type": "Public",
                },
                "/create_rule/": {
                    "description": "Create campaign rule.",
                    "type": "Private",
                },
                "/download_source_details": {
                    "description": "API for getting the download link of both the data set which is Source wise "
                                   "details and utm source.",
                    "type": "Private",
                },
                "/get_by_rule_name/": {
                    "description": "Get campaign rule details by name.",
                    "type": "Private",
                },
                "/get_campaign_details": {
                    "description": "API for getting all campaign list with insight details related to any source name and "
                                   "medium name.",
                    "type": "Private",
                },
                "/get_medium_details": {
                    "description": "API for getting all mediums list with insight details related to any source name.",
                    "type": "Private",
                },
                "/get_rules/": {
                    "description": "Get list of all campaign rules.",
                    "type": "Private",
                },
                "/get_utm_campaign": {
                    "description": "Update UTM details in campaign.",
                    "type": "Private",
                },
                "/source_details": {
                    "description": "API for getting the count of leads according to source with different segregation's.",
                    "type": "Private",
                },
                "/source_wise_overlap": {
                    "description": "Fetch the source wise overlap details.",
                    "type": "Private",
                },
                "/update_status_of_rule/": {
                    "description": "Change status of campaign rule.",
                    "type": "Private",
                },
                "/utm_details": {
                    "description": "Get the utm counts wise campaign, median and keywords",
                    "type": "Private",
                },
                "_beta/": {
                    "description": "Fetch all campaign names.",
                    "type": "Private",
                },
                "_beta/check_rule_name_exist_or_not/": {
                    "description": "Check if the campaign rule name exist or not.",
                    "type": "Public",
                },
                "_beta/create/": {"description": "Create campaign.", "type": "Private"},
                "_beta/create_rule/": {
                    "description": "Create campaign rule.",
                    "type": "Private",
                },
                "_beta/get_by_rule_name/": {
                    "description": "Get campaign rule details by name.",
                    "type": "Private",
                },
                "_beta/get_rules/": {
                    "description": "Get list of all campaign rules.",
                    "type": "Private",
                },
                "_beta/update_status_of_rule/": {
                    "description": "Change status of campaign rule.",
                    "type": "Private",
                },
                "_manager/": {
                    "description": "Get source based campaign data.",
                    "type": "Private",
                },
                "_manager/source_performance_details/": {
                    "description": "Get source performance details.",
                    "type": "Private",
                },
                "_manager/source_wise_details/": {
                    "description": "Get source wise details.",
                    "type": "Private",
                },
            },
        },
        "check": {
            "description": "Retrieve the database connection",
            "name": "Check Database Connection",
            "prefix": "check",
            "routes": {
                "/check_connections": {
                    "description": "Check the database connection.",
                    "type": "Public",
                }
            },
        },
        "client_automation": {
            "description": "Functionality Relates with Client Automation",
            "name": "Client Automation",
            "prefix": "client_automation",
            "routes": {
                "/add_college": {
                    "description": "Creation of College",
                    "type": "Private"
                },
                "/{college_id}/add_course": {
                    "description": "Addition of Course Detail in College",
                },
                "/save_signup_form/{college_id}": {
                    "description": "Save Signup Form Details",
                    "type": "Private"
                },
                "/update_activation_status_of_college": {
                    "description": "Update Activation Status of College",
                    "type": "Private"
                },
                "/update_status_of_college/": {
                    "description": "Update Status of Colleges(Pending/Approved/Declined)",
                    "type": "Private"
                },
            }
        },
        "approval": {
            "description": "Operations related to the approval module",
            "name": "Approval",
            "prefix": "approval",
            "routes": {
                "/create_request": {
                    "description": "Create a new approval request.",
                    "type": "Private",
                    "method": "POST"
                },
                "/get_requests": {
                    "description": "Retrieve approval requests sent by a client or college.",
                    "type": "Private",
                    "method": "GET"
                },
                "/get_request_need_approval": {
                    "description": "Retrieve approval requests that require approval.",
                    "type": "Private",
                    "method": "GET"
                },
                "/approve_request/{approver_id}": {
                    "description": "Approve an approval request.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/reject_request/{approver_id}": {
                    "description": "Reject an approval request.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/delete_request/{approver_id}": {
                    "description": "Delete an approval request.",
                    "type": "Private",
                    "method": "DELETE"
                }
            }
        },
        "super_account_manager": {
            "description": "Operations related to super account manager management",
            "name": "Super Account Manager",
            "prefix": "super_account_manager",
            "routes": {
                "/create": {
                    "description": "Create a new super account manager.",
                    "type": "Private",
                    "method": "POST"
                },
                "/get/{super_account_manager_id}": {
                    "description": "Retrieve super account manager details by ID.",
                    "type": "Private",
                    "method": "GET"
                },
                "/get_all": {
                    "description": "Retrieve all super account managers.",
                    "type": "Private",
                    "method": "GET"
                },
                "/update/{super_account_manager_id}": {
                    "description": "Update the details of a super account manager.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/activate/{super_account_manager_id}": {
                    "description": "Activate a super account manager.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/deactivate/{super_account_manager_id}": {
                    "description": "Deactivate a super account manager.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/assign-account-managers/{super_account_manager_id}": {
                    "description": "Assign account managers to a super account manager.",
                    "type": "Private",
                    "method": "PUT"
                }
            }
        },
        "account_manager": {
            "description": "Operations related to account manager management",
            "name": "Account Manager",
            "prefix": "account_manager",
            "routes": {
                "/create": {
                    "description": "Create a new account manager.",
                    "type": "Private",
                    "method": "POST"
                },
                "/get/{account_manager_id}": {
                    "description": "Get details of an account manager by ID.",
                    "type": "Private",
                    "method": "GET"
                },
                "/get_all": {
                    "description": "Retrieve all account managers.",
                    "type": "Private",
                    "method": "GET"
                },
                "/update/{account_manager_id}": {
                    "description": "Update account manager details.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/change_super_account_manager/{account_manager_id}": {
                    "description": "Change the associated super account manager for a given account manager.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/add_clients/{account_manager_id}": {
                    "description": "Add client(s) to an account manager.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/remove_client/{account_manager_id}": {
                    "description": "Remove a client from an account manager.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/activate/{account_manager_id}": {
                    "description": "Activate an account manager.",
                    "type": "Private",
                    "method": "PUT"
                },
                "/deactivate/{account_manager_id}": {
                    "description": "Deactivate an account manager.",
                    "type": "Private",
                    "method": "PUT"
                }
            }
        },
        "client": {
            "description": "Operations related to client management",
            "name": "Client",
            "prefix": "client",
            "routes": {
                "/create/": {
                    "description": "Create new client.",
                    "type": "Private"
                },
                "/{client_id}/configuration/add": {
                    "description": "Add client configuration",
                    "type": "Private",
                },
                "/{client_id}/configuration/get": {
                    "description": "Add client configuration",
                    "type": "Private",
                    "method": "POST"
                },
                "/all": {
                    "description": "Get all clients.",
                    "type": "Private"
                },
                "/{client_id}/": {
                    "description": "Get client details by id.",
                    "type": "Private"
                },
                "/{client_id}/update": {
                    "description": "Update client details.",
                    "type": "Private"
                },
                "/{client_id}/delete": {
                    "description": "Delete client Data.",
                    "type": "Private"
                }
            }
        },
        "college": {
            "description": "College-related operations",
            "name": "College",
            "prefix": "college",
            "routes": {
                "/communication_info/": {
                    "description": "Get communication info of college.",
                    "type": "Private",
                },
                "/communication_performance_dashboard/": {
                    "description": "Get the communication performance dashboard data.",
                    "type": "Private",
                },
                "/component_charges/": {
                    "description": "Add or update component charges.",
                    "type": "Public",
                },
                "/create/": {"description": "Create new college.", "type": "Private"},
                "/estimation_bill/": {
                    "description": "Get estimation bill of college.",
                    "type": "Private",
                },
                "/existing_fields/": {
                    "description": "Get existing fields names with key_names.",
                    "type": "Public",
                },
                "/extra_filter_fields/": {
                    "description": "Get extra filter fields based on college id / domain url.",
                    "type": "Public",
                },
                "/features/": {
                    "description": "Fetch college features.",
                    "type": "Private",
                },
                "/features/delete/": {
                    "description": "Delete features for a college by college id.",
                    "type": "Private",
                },
                "/features/update/": {
                    "description": "Add or update features.",
                    "type": "Private",
                },
                "/get_by_id_or_name/": {
                    "description": "Get College Details by id or name.",
                    "type": "Private",
                },
                "s/get_by_status/": {
                    "description": "Get college based on status.",
                    "type": "Private",
                },
                "/get_component_charges/": {
                    "description": "Get component charges.",
                    "type": "Public",
                },
                "/get_course_details/": {
                    "description": "Get course details.",
                    "type": "Public",
                },
                "/get_form_details/": {
                    "description": "Get form field details.",
                    "type": "Public",
                },
                "/lead_tags/": {
                    "description": "Get lead tags based on college id.",
                    "type": "Private",
                },
                "/list_college/": {
                    "description": "Get list of colleges.",
                    "type": "Private",
                },
                "/season_list/": {
                    "description": "Get college season list by id or name.",
                    "type": "Private",
                },
                "/signup_form_extra_fields/": {
                    "description": "Get signup form extra fields.",
                    "type": "Public",
                },
                "/university_names": {
                    "description": "Get the university name or diploma name",
                    "type": "Public",
                },
                "/update_status/": {
                    "description": "Update college status.",
                    "type": "Private",
                },
                "/get_utm_campaign/": {
                    "description": "Get the utm campaign list for college.",
                    "type": "Private",
                },
                "/utm_medium_by_source_names/": {
                    "description": "Get utm medium list by source names.",
                    "type": "Private",
                },
                "/additional_details": {
                    "description": "Add general additional details.",
                    "type": "Private",
                },
                "/season_details": {
                    "description": "Add season details.",
                    "type": "Private",
                },
                "/default_screen_by_client": {
                    "description": "Get the Default Screen for College Set by Client for Initial Selection.",
                    "type": "Private",
                },
                "/{college_id}/urls": {
                    "description": "Get Student Dashboard & Admin Dashboard URLs.",
                    "type": "Private",
                },
                "/{college_id}/set_urls": {
                    "description": "Set Student Dashboard & Admin Dashboard URLs will be Used by TeamCity.",
                    "type": "Private",
                },
                "/application_tabs/{college_id}": {
                    "description": "Fetch application form tabs or a specific stage for a given college and course.",
                    "type": "Private",
                }
            },
        },
        "communication": {
            "description": "Operations related to communication "
                           "in communication summary module",
            "name": "Communication Summary",
            "prefix": "communication",
            "routes": {
                "/counsellor_wise_followup_details": {
                    "description": "API for getting counsellor wise followup data.",
                    "type": "Private",
                },
                "/header_summary": {
                    "description": "Communication summary Header data API with date range and change indicator filter",
                    "type": "Private",
                },
            },
        },
        "counselor": {
            "description": "Operations related to counselors",
            "name": "Counselor Admin",
            "prefix": "counselor",
            "routes": {
                "/absent": {
                    "description": "Get the detail of absent counselors.",
                    "type": "Private",
                },
                "/all_counselor_list": {
                    "description": "Get the list of college_counselors.",
                    "type": "Private",
                },
                "/assign_course": {
                    "description": "Add course_tag to college counselor.",
                    "type": "Private",
                },
                "/change_status": {
                    "description": "Change counselor's active status to True or False.",
                    "type": "Private",
                },
                "/college_counselor_list/": {
                    "description": "Get the list of counselor.",
                    "type": "Private",
                },
                "/counsellor_performance_report": {
                    "description": "Get counselor performance report.",
                    "type": "Private",
                },
                "/counselor_performance": {
                    "description": "Get the counselor wise performance report data.",
                    "type": "Private",
                },
                "/counselor_performance_download": {
                    "description": "Download the counselor wise performance report data.",
                    "type": "Private",
                },
                "/counselor_productivity_report/": {
                    "description": "Get counselor productivity report.",
                    "type": "Private",
                },
                "/counselor_wise_lead": {
                    "description": "Get total_lead, total_paid and counselor_name.",
                    "type": "Private",
                },
                "/counselor_wise_lead_stage": {
                    "description": "Get lead_stage shown by counselor name.",
                    "type": "Private",
                },
                "/download_counselor_performance_report": {
                    "description": "Downloads the counselor performance report based on college_id in form of csv file.",
                    "type": "Private",
                },
                "/download_counselors_productivity_report/": {
                    "description": "Download counselors productivity report.",
                    "type": "Private",
                },
                "/followup_details_summary/": {
                    "description": "Get the follow-up details summary information.",
                    "type": "Private",
                },
                "/followup_report/": {
                    "description": "Get the followup report.",
                    "type": "Private",
                },
                "/get_calendar_info/": {
                    "description": "Get the day wise calendar data.",
                    "type": "Private",
                },
                "/get_head_counselors_list/": {
                    "description": "Get the list of college_head_counselors.",
                    "type": "Private",
                },
                "/get_human_languages/": {
                    "description": "Get list of languages used in college.",
                    "type": "Private",
                },
                "/get_leads_application_data": {
                    "description": "Get leads and application data in counselor dashboard.",
                    "type": "Private",
                },
                "/get_pending_followup/": {
                    "description": "Get the pending followup details.",
                    "type": "Private",
                },
                "/key_indicators/": {
                    "description": "Get key indicator section information by counselor id (s).",
                    "type": "Private",
                },
                "/lead_allocated_counselor/": {
                    "description": "Get the list of counselor allocated to lead.",
                    "type": "Private",
                },
                "/lead_stage_count_summary/": {
                    "description": "Get or download lead stage count summary information.",
                    "type": "Private",
                },
                "/leave_college_counselor": {
                    "description": "Leave college counsellor",
                    "type": "Private",
                },
                "/manual_counselor": {
                    "description": "Allocated manual counselor to student.",
                    "type": "Private",
                },
                "/manual_counselor_assign": {
                    "description": "Manually assign counselor to the lead.",
                    "type": "Private",
                },
                "/map_with_head_counselor/": {
                    "description": "Map the counselor with head counselor",
                    "type": "Private",
                },
                "/multiple_application_to_one_counselor": {
                    "description": "Get list of application forms associated with counselor id.",
                    "type": "Private",
                },
                "/quick_view/": {
                    "description": "Get the data of Admission status based on route 'score_board', college_id and "
                                   "date_range.",
                    "type": "Private",
                },
                "/send_email_to_multiple_lead/": {
                    "description": "Send mail to multiple leads.",
                    "type": "Private",
                },
                "/source_lead_performing": {
                    "description": "Get source performance reports.",
                    "type": "Private",
                },
            },
        },
        "countries": {
            "description": "Operations related to countries, states, and cities",
            "name": "Country",
            "prefix": "countries",
            "routes": {
                "/": {"description": "Get List of Countries.", "type": "Public"},
                "/get_cities_based_on_states/": {
                    "description": "Get cities based on multiple state codes.",
                    "type": "Public",
                },
                "/{country_code}/": {
                    "description": "Get Country Details using ISO2 Code.",
                    "type": "Public",
                },
                "/{country_code}/states/": {
                    "description": "List of States within the Country based on country code.",
                    "type": "Public",
                },
                "/{country_code}/states/{state_code}": {
                    "description": "Get the state details using country_code and state_code.",
                    "type": "Public",
                },
                "/{country_code}/states/{state_code}/cities": {
                    "description": "Get the list of cities within a state using country_code and state_code.",
                    "type": "Public",
                },
            },
        },
        "course": {
            "description": "Course-related operations",
            "name": "Course",
            "prefix": "course",
            "routes": {
                "/add_specializations/": {
                    "description": "Add specializations to the course.",
                    "type": "Private",
                },
                "/create/": {"description": "Create new course.", "type": "Private"},
                "/edit/": {"description": "Edit an existing course.", "type": "Private"},
                "/list/": {"description": "Get a list of courses.", "type": "Public"},
                "/specialization_list/": {
                    "description": "Get a list of course specializations.",
                    "type": "Public",
                },
                "/status/": {
                    "description": "Enable or Disable course.",
                    "type": "Private",
                },
                "/update_specializations/": {
                    "description": "Update specializations of the course.",
                    "type": "Private",
                },
            },
        },
        "data_segment": {
            "description": "Operations related to data segment",
            "name": "Data Segment",
            "prefix": "data_segment",
            "routes": {
                "/": {
                    "description": "Get all data segment names of a college.",
                    "type": "Private",
                },
                "/add_data_segment_student": {
                    "description": "Custom assign student to the data segment.",
                    "type": "Private",
                },
                "/count_of_entities/": {
                    "description": "Get the count of data segment entities.",
                    "type": "Private",
                },
                "/create/": {
                    "description": "Create data segment for college.",
                    "type": "Private",
                },
                "/create_share_link_segment": {
                    "description": "Create the link of data segment share segment and send to the user.",
                    "type": "Private",
                },
                "/data_segment_shared_user_details": {
                    "description": "Get the user permission details for a segment shared",
                    "type": "Private",
                },
                "/delete/": {
                    "description": "Delete data segment by id or name.",
                    "type": "Private",
                },
                "/dkper/{token}": {
                    "description": "Get the details from the shared link from the data segment.",
                    "type": "Private",
                },
                "/get_by_name_or_id/": {
                    "description": "Get data segment details by id or name.",
                    "type": "Private",
                },
                "/header_view/": {
                    "description": "Get the details of data segment based on data segment id.",
                    "type": "Private",
                },
                "/remove_data_segment_permission_access": {
                    "description": "Remove data segment permission access.",
                    "type": "Private",
                },
                "/search_for_add_data_segment": {
                    "description": "Get the all students details based on given data type.",
                    "type": "Private",
                },
                "/student_mapped": {
                    "description": "Get student details i.e. mapped with data segment.",
                    "type": "Private",
                },
                "/update_shared_user_permission": {
                    "description": "Update the data segment shared user permission.",
                    "type": "Private",
                },
                "s/": {"description": "Get all data segments", "type": "Private"},
                "s/change_status/": {
                    "description": "Change status of data segments by ids.",
                    "type": "Private",
                },
                "s/communication_performance_dashboard/": {
                    "description": "Get top performing data segments details.",
                    "type": "Private",
                },
                "s/download/": {
                    "description": "Download data segment details by ids.",
                    "type": "Private",
                },
                "s/quick_view_info/": {
                    "description": "Get quick view information of data segments.",
                    "type": "Private",
                },
            },
        },
        "document_verification": {
            "description": "Operations related to document verification management",
            "name": "Document Verification",
            "prefix": "document_verification",
            "routes": {
                "/quick_view/": {
                    "description": "Get Quick View Details",
                    "type": "Private",
                },
                "/update_dv_status/": {
                    "description": "Update document Status",
                    "type": "Private",
                },
                "/auditor_remark/": {
                    "description": "Add Auditor Remark for Document",
                    "type": "Private",
                },
                "/get_auditor_remarks/": {
                    "description": "Get Auditor Remarks",
                    "type": "Private",
                },
                "/download_application_or_all_documents/": {
                    "description": "Download student application or all documents",
                    "type": "Private",
                },
            },
        },
        "email": {
            "description": "Operations related to email management",
            "name": "Email",
            "prefix": "email",
            "routes": {
                "/unsubscribe/{token}": {
                    "description": "Unsubscribe promotional email service.",
                    "type": "Public",
                },
                "/webhook/": {
                    "description": "Webhook for capture email status by karix.",
                    "type": "Public",
                },
                "/webook/amazon_ses/": {
                    "description": "Webhook for capture email status by amazon ses.",
                    "type": "Public",
                },
            },
        },
        "event": {
            "description": "Operations related to events management",
            "name": "Event",
            "prefix": "event",
            "routes": {
                "/add_or_update/": {
                    "description": "Add an event data in the database.",
                    "type": "Private",
                },
                "/delete_by_name_or_id/": {
                    "description": "Delete an event from database by name or id.",
                    "type": "Private",
                },
                "/get_by_name_or_id/": {
                    "description": "Get an event data by name or id.",
                    "type": "Private",
                },
                "/type/add_or_update/": {
                    "description": "Add event types in the database.",
                    "type": "Private",
                },
                "/types": {
                    "description": "Get all event types from the database.",
                    "type": "Private",
                },
                "s/": {"description": "Get all events data.", "type": "Private"},
            },
        },
        "followup_notes": {
            "description": "Operations related to followup notes management",
            "name": "Followup and Notes",
            "prefix": "followup_notes",
            "routes": {
                "/add_lead_stage_label": {
                    "description": "Add lead stage label on client database.",
                    "type": "Private",
                },
                "/get_lead_stage_label": {
                    "description": "Get lead stage label from client database.",
                    "type": "Private",
                },
                "/get_pending_followup": {
                    "description": "Get all pending leads.",
                    "type": "Private",
                },
                "/head_counselor_details": {
                    "description": "Get all head counselor details.",
                    "type": "Private",
                },
                "/multiple_lead_stage": {
                    "description": "Add/Update lead stage information for multiple applications.",
                    "type": "Private",
                },
                "/update_followup_status/{application_id}/": {
                    "description": "Update followup status based on application id.",
                    "type": "Private",
                },
                "/{application_id}/": {
                    "description": "Add or get follow-up and notes.",
                    "type": "Private",
                },
            },
        },
        "interview": {
            "description": "Operations related to interviews",
            "name": "Interview Module",
            "prefix": "interview",
            "routes": {
                "/add_students_into_list/": {
                    "description": "Add students into interview list.",
                    "type": "Private",
                },
                "/create_or_update_interview_list/": {
                    "description": "Create or update interview list for program.",
                    "type": "Private",
                },
                "/create_or_update_selection_procedure/": {
                    "description": "Create or update selection procedure for course.",
                    "type": "Private",
                },
                "/delete_list/": {
                    "description": "Delete interview lists by interview_list_ids.",
                    "type": "Private",
                },
                "/delete_selection_procedure/": {
                    "description": "Delete selection procedure of course.",
                    "type": "Private",
                },
                "/delete_selection_procedures/": {
                    "description": "Delete selection procedures by ids.",
                    "type": "Private",
                },
                "/delete_slots_or_panels/": {
                    "description": "Delete slots or panels by ids.",
                    "type": "Private",
                },
                "/delete_students_from_list/": {
                    "description": "Delete students from interview list.",
                    "type": "Private",
                },
                "/download_interview_list/": {
                    "description": "Download interview lists by interview_list_ids.",
                    "type": "Private",
                },
                "/download_view_interview_detail/": {
                    "description": "Download view interview details by id.",
                    "type": "Private",
                },
                "/gd_pi_header_list/": {
                    "description": "Get gd pi header list.",
                    "type": "Private",
                },
                "/gd_pi_interview_list/": {
                    "description": "Get GD PI Interview list details.",
                    "type": "Private",
                },
                "/get_hod_header/": {
                    "description": "Get summary of interview applicants.",
                    "type": "Private",
                },
                "/get_selection_procedure/": {
                    "description": "Get selection procedure of course.",
                    "type": "Private",
                },
                "/interview_list_header/": {
                    "description": "Get interview list header by id.",
                    "type": "Private",
                },
                "/marking_details/": {
                    "description": "Get marking details based on program name.",
                    "type": "Private",
                },
                "/selection_procedures/": {
                    "description": "Get selection procedures data based on page number and page size.",
                    "type": "Private",
                },
                "/store_feedback/": {
                    "description": "Add marks obtained by the given student.",
                    "type": "Private",
                },
                "/view_interview_detail/": {
                    "description": "Get interview details by id.",
                    "type": "Private",
                },
                "_list/applications_data_based_on_program/": {
                    "description": "Get interview list applicants data based on program with/without filters.",
                    "type": "Private",
                },
                "_list/approval_pending_applicants_data/": {
                    "description": "Get approval pending applicants' data with pagination.",
                    "type": "Private",
                },
                "_list/change_interview_status_of_candidates/": {
                    "description": "Change the status of interview candidates, useful for further/next process.",
                    "type": "Private",
                },
                "_list/change_status_by_ids/": {
                    "description": "Change status of interview lists by ids.",
                    "type": "Private",
                },
                "_list/reviewed_applicants_data/": {
                    "description": "Get reviewed applicants' data with pagination.",
                    "type": "Private",
                },
                "_list/selected_student_applications_data/": {
                    "description": "Get interview list selected applicants data based on interview list id.",
                    "type": "Private",
                },
                "_list/send_applicants_for_approval/": {
                    "description": "Send applicants for approval.",
                    "type": "Private",
                },
            },
        },
        "interview_list": {
            "description": "Retrieve the list of interviews",
            "name": "Interview List",
            "prefix": "interview_list",
            "routes": {
                "/assign_application/panelist": {
                    "description": "Assign applicant/panelist to the slot.",
                    "type": "Private",
                },
                "/get_interview_header/": {
                    "description": "Get all the interview list header details from the meili search server.",
                    "type": "Private",
                },
                "/get_interview_list/": {
                    "description": "Get all the interview details from the meili search.",
                    "type": "Private",
                },
                "/reschedule_interview": {
                    "description": "Reschedule an interview for an application.",
                    "type": "Private",
                },
                "/slot_time_management": {
                    "description": "Modify the slot time management.",
                    "type": "Private",
                },
                "/unassigned_application": {
                    "description": "Unassigned/Remove applicant/panelist from a slot.",
                    "type": "Private",
                },
            },
        },
        "lead": {
            "description": "Admin lead-related operations",
            "name": "Admin Lead",
            "prefix": "lead",
            "routes": {
                "/add_secondary_tertiary_email_phone/": {
                    "description": "Add secondary and tertiary email or phone number.",
                    "type": "Private",
                },
                "/add_tag/": {"description": "Add tag to student.", "type": "Private"},
                "/delete_tag/": {
                    "description": "Delete tag from student.",
                    "type": "Private",
                },
                "/lead_data_count": {
                    "description": "Get the lead data based on counts.",
                    "type": "Private",
                },
                "/lead_details_user/{application_id}": {
                    "description": "Get list of lead detail user data based on application_id.",
                    "type": "Private",
                },
                "/lead_header": {
                    "description": "Get the lead header data for the lead dashboard.",
                    "type": "Private",
                },
                "/lead_notifications/{application_id}": {
                    "description": "Returns the application status of student' application based on application_id.",
                    "type": "Private",
                },
                "/lead_profile_header/{application_id}": {
                    "description": "Get list of lead profile header data based on application_id.",
                    "type": "Private",
                },
                "/send_email_sidebar": {
                    "description": "send mail to recipient in background with message 'mail send successfully'.",
                    "type": "Private",
                },
                "/show_today_lead_data/": {
                    "description": "Get current lead stage data and assign counselor count.",
                    "type": "Private",
                },
                "/step_wise_data": {
                    "description": "Get application steps count with/without counselor/program filter.",
                    "type": "Private",
                },
                "/user_activity/": {
                    "description": "Get all users list based on last accessed and inputs: skips and limit.",
                    "type": "Private",
                },
            },
        },
        "logs": {
            "description": "Retrieve a temporary S3 URL for logs",
            "name": "Log",
            "prefix": "logs",
            "routes": {"/": {"description": "Log file.", "type": "Public"}},
        },
        "manage": {
            "description": "Operations related to leads management",
            "name": "Manage Lead",
            "prefix": "manage",
            "routes": {
                "/action_on_raw_data/": {
                    "description": "Perform action on successful lead of raw data.",
                    "type": "Private",
                },
                "/converted_lead_and_application_list/": {
                    "description": "API for getting the list of student and applications which is converted from raw data.",
                    "type": "Private",
                },
                "/delete_lead_offline_data/": {
                    "description": "Delete the lead offline data and offline data from lead history collection.",
                    "type": "Private",
                },
                "/display_offline/": {
                    "description": "Display offline data using filter and daterange.",
                    "type": "Private",
                },
                "/download_raw_data/": {
                    "description": "API for downloading offline data in excel by the using of unique id.",
                    "type": "Private",
                },
                "/get_all_raw_data/": {
                    "description": "Get all raw data.",
                    "type": "Private",
                },
                "/lead_upload_display_offline/": {
                    "description": "Display offline data using filter and daterange.",
                    "type": "Private",
                },
                "/list_of_raw_data_names/": {
                    "description": "Get list of raw data names.",
                    "type": "Private",
                },
                "/raw_data": {
                    "description": "Upload raw data in raw_data collection.",
                    "type": "Private",
                },
                "/show_successful_lead": {
                    "description": "Fetch all successful leads.",
                    "type": "Private",
                },
                "/system_successful_lead_data": {
                    "description": "Get list of successful leads.",
                    "type": "Private",
                },
            },
        },
        "map_data": {
            "description": "Operations related to maps",
            "name": "Map",
            "prefix": "map_data",
            "routes": {
                "/city_wise_data/{state_code}": {
                    "description": "Get the geographical map city wise data of college.",
                    "type": "Private",
                },
                "/{college_id}": {
                    "description": "Get the geographical map data of college.",
                    "type": "Private",
                },
            },
        },
        "nested_automation": {
            "description": "Operations related to nested automation management",
            "name": "Nested Automation",
            "prefix": "nested_automation",
            "routes": {
                "/automation_link_to_data_segment": {
                    "description": "Assign data segment to automation.",
                    "type": "Private",
                },
                "/automation_list": {
                    "description": "Get all automation list.",
                    "type": "Private",
                },
                "/automation_top_bar_data": {
                    "description": "Get automation top bar details.",
                    "type": "Private",
                },
                "/change_automation_status": {
                    "description": "Stop the automation.",
                    "type": "Private",
                },
                "/communication_data/": {
                    "description": "Get automation (s) communication data.",
                    "type": "Private",
                },
                "/copy_automation": {
                    "description": "Copy an automation data.",
                    "type": "Private",
                },
                "/delete_automation": {
                    "description": "Delete an automation by automation id.",
                    "type": "Private",
                },
                "/get_active_data_segments": {
                    "description": "Get active data segment based on given filters.",
                    "type": "Private",
                },
                "/get_data_by_id/": {
                    "description": "Get automation data by id.",
                    "type": "Private",
                },
                "/top_bar_details/": {
                    "description": "Get automation top bar details.",
                    "type": "Private",
                },
            },
        },
        "notifications": {
            "description": "Retrieve notifications",
            "name": "Notification",
            "prefix": "notifications",
            "routes": {
                "/hide_by_id/": {
                    "description": "Hide notification by id.",
                    "type": "Private",
                },
                "/update/": {
                    "description": "Update notification status by id.",
                    "type": "Public",
                },
                "/{user_email}/": {
                    "description": "Get notifications of user by id.",
                    "type": "Public",
                },
            },
        },
        "oauth": {
            "description": "OAuth authentication. Obtain and verify `token` here.",
            "name": "Authentication",
            "prefix": "oauth",
            "routes": {
                "/refresh_token/generate/": {
                    "description": "Generate refresh token.",
                    "type": "Public",
                },
                "/refresh_token/revoke/": {
                    "description": "Revoke refresh token.",
                    "type": "Public",
                },
                "/refresh_token/verify/": {
                    "description": "Verify refresh token.",
                    "type": "Public",
                },
                "/token": {"description": "Login", "type": "Public"},
                "/tokeninfo": {"description": "Get token info API.", "type": "Public"},
            },
        },
        "payments": {
            "description": "Operations related to payments",
            "name": "Payment Gateway",
            "prefix": "payments",
            "routes": {
                "/": {"description": "Fetch all payment details.", "type": "Public"},
                "/application/{application_id}/": {
                    "description": "Fetch all payment details by application_id.",
                    "type": "Public",
                },
                "/create_order/": {
                    "description": "Create a new order.",
                    "type": "Private",
                },
                "/get_client_id": {
                    "description": "Get payment's client id.",
                    "type": "Private",
                },
                "/manual_capture/": {
                    "description": "Store manual payment data.",
                    "type": "Private",
                },
                "/order_details/{order_id}": {
                    "description": "Returns the order details using order_id.",
                    "type": "Public",
                },
                "/payment_details/{payment_id}/": {
                    "description": "Returns the payment details using payment_id.",
                    "type": "Public",
                },
                "/send_receipt_through_mail/": {
                    "description": "Send payment receipt through mail.",
                    "type": "Private",
                },
                "/webhook/{college_id}/": {
                    "description": "Returns the Webhook details through college_id.",
                    "type": "Public",
                },
                "/{payment_id}/": {
                    "description": "Fetch payment details by payment_id.",
                    "type": "Public",
                },
                "/{payment_id}/capture/": {
                    "description": "Capture a payment by payment_id.",
                    "type": "Public",
                },
                "/{payment_id}/card/": {
                    "description": "Fetch card details of payment by payment_id.",
                    "type": "Public",
                },
                "/{payment_id}/update/": {
                    "description": "Update the payment details.",
                    "type": "Public",
                },
            },
        },
        "planner": {
            "description": "Operations related to planner management",
            "name": "Planner Module",
            "prefix": "planner",
            "routes": {
                "/calender_info/": {
                    "description": "Get day wise PI/GD information for given month and year.",
                    "type": "Private",
                },
                "/create_or_update_panel/": {
                    "description": "Either create a new panel or update existing panel depending on whether the panel_id "
                                   "is provided.",
                    "type": "Private",
                },
                "/create_or_update_slot/": {
                    "description": "Either create a new slot or update existing slot based on slot_id.",
                    "type": "Private",
                },
                "/date_wise_panel_slot_hours/": {
                    "description": "Get date wise panel slot hours details.",
                    "type": "Private",
                },
                "/day_wise_slot_panel_data/": {
                    "description": "Get day wise slots and panels data along with next day.",
                    "type": "Private",
                },
                "/get_panel_names/": {
                    "description": "Get panel names with/without filters.",
                    "type": "Private",
                },
                "/get_slot_or_panel_data/": {
                    "description": "Get slot or panel data by id.",
                    "type": "Private",
                },
                "/invite_student_to_meeting/": {
                    "description": "Invite student for meeting through mail.",
                    "type": "Private",
                },
                "/month_wise_slots_info/": {
                    "description": "Get month wise slots info with/without filter according to program.",
                    "type": "Private",
                },
                "/panel/get_data_by_id/": {
                    "description": "Get panel details based on id.",
                    "type": "Private",
                },
                "/profile_marking_details/": {
                    "description": "Fetch details of student profile and marking scheme.",
                    "type": "Private",
                },
                "/publish_slots_or_panels/": {
                    "description": "Publish slots or panels based on ids.",
                    "type": "Private",
                },
                "/slot/get_data_by_id/": {
                    "description": "Get slot details based on id.",
                    "type": "Private",
                },
                "/student_profile/": {
                    "description": "Fetch details of a student.",
                    "type": "Private",
                },
                "/take_a_slot/": {
                    "description": "Take a slot based on id.",
                    "type": "Private",
                },
                "/unassign_applicants_from_slots/": {
                    "description": "Un-assign all applicants from given slots.",
                    "type": "Private",
                },
            },
        },
        "promocode_vouchers": {
            "description": "Operations related to promocode voucher management",
            "name": "Promocode Vouchers",
            "prefix": "promocode_vouchers",
            "routes": {
                "/create_promocode/": {
                    "description": "Create a new promocode.",
                    "type": "Private",
                },
                "/create_voucher/": {
                    "description": "Create a new voucher",
                    "type": "Private",
                },
                "/delete_promocode_voucher/": {
                    "description": "Delete a promocode or voucher.",
                    "type": "Private",
                },
                "/get_applied_students/": {
                    "description": "Fetch all applied students info.",
                    "type": "Private",
                },
                "/get_promocodes/": {
                    "description": "Get list of all promocodes.",
                    "type": "Private",
                },
                "/get_quick_view/": {
                    "description": "Get quick view details.",
                    "type": "Private",
                },
                "/get_voucher_details/": {
                    "description": "Get a particular voucher details.",
                    "type": "Private",
                },
                "/get_vouchers/": {
                    "description": "Get list of all vouchers.",
                    "type": "Private",
                },
                "/payment_through_code/": {
                    "description": "Proceed a payment through code (voucher code/ promocode with full discount).",
                    "type": "Private",
                },
                "/update_promocode/": {
                    "description": "Update or edit an existing promocode.",
                    "type": "Private",
                },
                "/update_voucher/": {
                    "description": "Update or edit an existing voucher.",
                    "type": "Private",
                },
                "/verify_promocode_voucher/": {
                    "description": "Verify the existance of given promocode or voucher.",
                    "type": "Private",
                },
            },
        },
        "publisher": {
            "description": "Operations related to publisher",
            "name": "Publisher",
            "prefix": "publisher",
            "routes": {
                "/add_leads_using_json_or_csv/{college_id}/": {
                    "description": "Add leads to college using json file.",
                    "type": "Private",
                },
                "/add_student/": {
                    "description": "Add student data.",
                    "type": "Private",
                },
                "/get_all_leads/": {
                    "description": "Get all leads of publisher based on publisher associated source value.",
                    "type": "Private",
                },
                "/get_publisher_leads_count_by_source_for_graph": {
                    "description": "Get publisher leads source.",
                    "type": "Private",
                },
                "/get_publisher_percentage_data": {
                    "description": "Get publisher leads percentage source.",
                    "type": "Private",
                },
            },
        },
        "qa_manager": {
            "description": "Operations related to QA manager",
            "name": "QA Manager",
            "prefix": "qa_manager",
            "routes": {
                "/call_list/": {
                    "description": "Get all calls for review.",
                    "type": "Private",
                },
                "/call_list_metrics/": {
                    "description": "Get the data of all the matrix of header i.e. related to QC.",
                    "type": "Private",
                },
                "/call_review/": {
                    "description": "Add a call review.",
                    "type": "Private",
                },
                "/counsellor/": {
                    "description": "Get list of all counsellors with their reviews for Counsellor head and qa manager.",
                    "type": "Private",
                },
                "/qa/": {
                    "description": "Get qa's reviews performance list.",
                    "type": "Private",
                },
                "/rejected_call_list_metrics/": {
                    "description": "Get Rejected Call QC overview data.",
                    "type": "Private",
                },
            },
        },
        "query": {
            "description": "Retrieve queries",
            "name": "Query",
            "prefix": "query",
            "routes": {
                "/assigned_counselor/": {
                    "description": "Assigned query/ticket to counselor.",
                    "type": "Private",
                },
                "/based_on_program/": {
                    "description": "Get query details based on application id or ticket id.",
                    "type": "Private",
                },
                "/change_status/": {
                    "description": "Change status of query/ticket.",
                    "type": "Private",
                },
                "/get/": {
                    "description": "Get query details based on application id or ticket id.",
                    "type": "Private",
                },
                "/list/": {"description": "Get all queries list.", "type": "Private"},
                "/reply/": {"description": "Reply to query.", "type": "Private"},
            },
        },
        "query_category": {
            "description": "Operations related to query categories",
            "name": "Query Categories",
            "prefix": "query_category",
            "routes": {
                "/create_query_categories/": {
                    "description": "Create a new query category.",
                    "type": "Public",
                }
            },
        },
        "reports": {
            "description": "Retrieve reports",
            "name": "Report",
            "prefix": "reports",
            "routes": {
                "/": {
                    "description": "Get all reports based on date range and pagination.",
                    "type": "Private",
                },
                "/current_user/": {
                    "description": "Get reports of current user based on date range and pagination.",
                    "type": "Private",
                },
                "/delete_report_by_id/": {
                    "description": "Delete report by id.",
                    "type": "Private",
                },
                "/generate_request_data/": {
                    "description": "Generate/update report based on request data.",
                    "type": "Private",
                },
                "/get_download_url_by_request_id/": {
                    "description": "Download reports data by report id(s).",
                    "type": "Private",
                },
                "/get_saved_report_templates/": {
                    "description": "Get all saved Report Templates.",
                    "type": "Private",
                },
                "/webhook/": {
                    "description": "Update report result based on request id.",
                    "type": "Public",
                },
            },
        },
        "resource": {
            "description": "Operations related to resource management",
            "name": "Resource",
            "prefix": "resource",
            "routes": {
                "/create_key_category/": {
                    "description": "Create a new key category.",
                    "type": "Private",
                },
                "/create_or_update_a_question/": {
                    "description": "Create or update a question..",
                    "type": "Private",
                },
                "/create_or_update_a_script/": {
                    "description": "Create or Update the Script.",
                    "type": "Private",
                },
                "/delete_a_script/": {
                    "description": "Delete a script from database.",
                    "type": "Private",
                },
                "/delete_key_category/": {
                    "description": "Delete a key category by index number.",
                    "type": "Private",
                },
                "/delete_questions/": {
                    "description": "Delete questions based on ids.",
                    "type": "Private",
                },
                "/get_key_categories/": {
                    "description": "Get all key categories.",
                    "type": "Private",
                },
                "/get_questions/": {
                    "description": "Get the questions with/without filters.",
                    "type": "Private",
                },
                "/get_user_updates/": {
                    "description": "Get the user updates.",
                    "type": "Private",
                },
                "/scripts/": {
                    "description": "Get all scripts with pagination.",
                    "type": "Private",
                },
                "/send_update_to_profile/": {
                    "description": "Send update to the selected profiles.",
                    "type": "Private",
                },
            },
        },
        "role": {
            "description": "Operations related to roles management",
            "name": "Role",
            "prefix": "role",
            "routes": {
                "/create_role/": {"description": "Create a new role.", "type": "Private"}
            },
        },
        "role_permissions": {
            "description": "Operations related to RBAC management",
            "name": "Role and Permissions",
            "prefix": "role_permissions",
            "routes": {
                "/create_role/": {"description": "Create a new role in the system.",
                                  "type": "Private"},
                "/roles": {
                    "description": "Retrieve a paginated list of all roles along with their associated permissions.",
                    "type": "Private",
                },
                "/roles/{role_id}": {
                    "description": "Retrieve a specific role by its ID along with its associated permissions.",
                    "type": "Private",
                },
                "/update_role/{role_id}": {
                    "description": "Update an existing role record in the database.",
                    "type": "Private",
                },
                "/delete_role/{role_id}": {
                    "description": "Delete an existing role record in the database by its ID.",
                    "type": "Private",
                },
                "/create_permission/": {
                    "description": "Create a new permission in the system.",
                    "type": "Private",
                },
                "/permissions": {
                    "description": "Retrieve a paginated list of all permissions.",
                    "type": "Private",
                },
                "/permissions/{permission_id}": {
                    "description": "Retrieve a specific permission by its ID.",
                    "type": "Private",
                },
                "/update_permission/{permission_id}": {
                    "description": "Update an existing permission record in the database.",
                    "type": "Private",
                },
                "/assign_permission/{role_id}": {
                    "description": "Assign permissions to a specific role by its ID.",
                    "type": "Private",
                },
                "/revoke_permissions/{role_id}": {
                    "description": "Revoke specified permissions from a given role by its ID.",
                    "type": "Private",
                },
                "/delete_permission/{permission_id}": {
                    "description": "Delete an existing permission by its ID.",
                    "type": "Private",
                },
                "/create_group/": {"description": "Create a new group in the system.",
                                   "type": "Private"},
                "/groups": {
                    "description": "Retrieve a paginated list of all groups along with their associated permissions.",
                    "type": "Private",
                },
                "/groups/{group_id}": {
                    "description": "Retrieve a specific group by its ID along with its associated permissions.",
                    "type": "Private",
                },
                "/update_group/{group_id}": {
                    "description": "This endpoint update an existing group.",
                    "type": "Private",
                },
                "/delete_group/{group_id}": {
                    "description": "This endpoint delete an existing group by its ID.",
                    "type": "Private",
                },
                "/assign_permission/group/{group_id}": {
                    "description": "This endpoint allows authorized users to assign multiple permissions to a group.",
                    "type": "Private",
                },
                "/revoke_permissions/group/{group_id}": {
                    "description": "This endpoint allows authorized users to revoke multiple permissions from a group.",
                    "type": "Private",
                },
                "/create_feature_group": {
                    "description": "This endpoint create a feature group.",
                    "type": "Private",
                },
                "/update_feature_group": {
                    "description": "This endpoint update a feature group.",
                    "type": "Private",
                },
                "/create_role_feature": {
                    "description": "This endpoint create a role.",
                    "type": "Private",
                },
                "/update_role_feature": {
                    "description": "This endpoint update the roles",
                    "type": "Private",
                },
                "/get_specific_roles": {
                    "description": "This endpoint get a role.",
                    "type": "Private",
                },
                "/get_specific_group": {
                    "description": "This endpoint get feature group.",
                    "type": "Private",
                }
            },
        },
        "sms": {
            "description": "Operations related to sms router",
            "name": "SMS Router",
            "prefix": "sms",
            "routes": {
                "/send_to_user/": {
                    "description": "Send SMS to a given students.",
                    "type": "Private",
                },
                "/webhook/": {
                    "description": "Capture the sms delivery status.",
                    "type": "Public",
                },
            },
        },
        "student": {
            "description": "Manage students. All student-related operations.",
            "name": "Student",
            "prefix": "student",
            "routes": {
                "/_beta/basic_details/": {
                    "description": "Add or update basic details.",
                    "type": "Private",
                },
                "/add_or_update_details/{course_name}/": {
                    "description": "Add or update parent details.",
                    "type": "Private",
                },
                "/address_details/{course_name}/": {
                    "description": "Add or update address details.",
                    "type": "Private",
                },
                "/basic_details/{course_name}/": {
                    "description": "Add or update basic details.",
                    "type": "Private",
                },
                "/board_detail/": {"description": "Board details.", "type": "Private"},
                "/change_password/": {
                    "description": "Change password.",
                    "type": "Private",
                },
                "/document_details/{course_name}/": {
                    "description": "Upload student documents.",
                    "type": "Private",
                },
                "/education_details/{course_name}/": {
                    "description": "Add or update education details.",
                    "type": "Private",
                },
                "/get_document/": {
                    "description": "Get student document.",
                    "type": "Private",
                },
                "/get_students_details/": {
                    "description": "Get student full details.",
                    "type": "Private",
                },
                "/get_students_primary_details/": {
                    "description": "Get student primary details.",
                    "type": "Private",
                },
                "/inter_school_subject_detail/{stream}": {
                    "description": "Inter school subject.",
                    "type": "Private",
                },
                "/parent_details/{course_name}/": {
                    "description": "Add or update parent details.",
                    "type": "Private",
                },
            },
        },
        "student/documents": {
            "description": "Operations related to text "
                           "extraction from student documents",
            "name": "Student Document Text Extraction",
            "prefix": "student/documents",
            "routes": {
                "/retry_extraction/": {
                    "description": "Get extracted data of student documents.",
                    "type": "Private",
                },
                "/text_extraction_info/{student_id}/": {
                    "description": "Get extracted data of student documents.",
                    "type": "Private",
                },
            },
        },
        "student/email": {
            "description": "Operations for sending an email to "
                           "students and verifying it",
            "name": "Student Email",
            "prefix": "student/email",
            "routes": {
                "/comments_and_status/": {
                    "description": "Send comments and status to student student i.e. posted on document locker.",
                    "type": "Private",
                },
                "/dkper/redirect/{token}": {
                    "description": "Get direct.",
                    "type": "Public",
                },
                "/reset_password/{token}/": {
                    "description": "Student reset password.",
                    "type": "Public",
                },
                "/reset_password_template/": {
                    "description": "Send email for rest password.",
                    "type": "Public",
                },
                "/verification/": {
                    "description": "Send verification email to student.",
                    "type": "Private",
                },
            },
        },
        "student_admin": {
            "description": "Add menu permissions",
            "name": "Super Admin",
            "prefix": "student_admin",
            "routes": {
                "/menu_permission": {
                    "description": "Update the menu_permission field in user_collection.",
                    "type": "Private",
                }
            },
        },
        "student_application": {
            "description": "All operations related to student applications",
            "name": "Student Application",
            "prefix": "student_application",
            "routes": {
                "/check_form_status/": {
                    "description": "Check Application form status of current user.",
                    "type": "Private",
                },
                "/declaration/": {
                    "description": "Declaration of Application.",
                    "type": "Private",
                },
                "/get_all_course_of_current_user": {
                    "description": "Current User List of Course from Current College.",
                    "type": "Private",
                },
                "/get_student_application": {
                    "description": "Get Current Student Application.",
                    "type": "Private",
                },
                "/update_payment_status/{application_id}/": {
                    "description": "Update Payment Status of student application.",
                    "type": "Private",
                },
            },
        },
        "student_call_log": {
            "description": "Retrieve logs related to student calls",
            "name": "Student Call Log",
            "prefix": "student_call_log",
            "routes": {
                "/{application_id}/": {
                    "description": "Fetch all call logs of a student based on application id.",
                    "type": "Public",
                }
            },
        },
        "student_communication_log": {
            "description": "Retrieve logs related to student communication",
            "name": "Student Communication Log",
            "prefix": "student_communication_log",
            "routes": {
                "/{application_id}/": {
                    "description": "Fetch communication logs of a student.",
                    "type": "Public",
                }
            },
        },
        "student_query": {
            "description": "Students can create queries/tickets",
            "name": "Student Query",
            "prefix": "student_query",
            "routes": {
                "/create/": {
                    "description": "Create student query.",
                    "type": "Private",
                }
            },
        },
        "student_timeline": {
            "description": "Operations related to student timeline",
            "name": "Student Timeline",
            "prefix": "student_timeline",
            "routes": {
                "/followup_and_notes/{application_id}/": {
                    "description": "Get timeline of followup and notes.",
                    "type": "Public",
                },
                "/{application_id}/": {
                    "description": "Get Timeline of a Student based on application id.",
                    "type": "Public",
                },
            },
        },
        "student_user_crud": {
            "description": "User operations. The **login** logic is also here.",
            "name": "Student User CRUD",
            "prefix": "student_user_crud",
            "routes": {
                "/board_detail/": {"description": "Board details.", "type": "Public"},
                "/email_mobile_verify": {
                    "description": "Email or Mobile Verify.",
                    "type": "Public",
                },
                "/login_with_otp/": {
                    "description": "Login with OTP.",
                    "type": "Public",
                },
                "/logout/": {"description": "Student logout.", "type": "Private"},
                "/signup": {"description": "Student signup.", "type": "Public"},
                "/update_student_primary_data/": {
                    "description": "Update student primary data.",
                    "type": "Private",
                },
                "/verify_captcha/": {
                    "description": "Verify google recaptcha v3.",
                    "type": "Public",
                },
                "/verify_otp/": {"description": "Verify OTP.", "type": "Public"},
            },
        },
        "tawk": {
            "description": "Operations related to tawk",
            "name": "Tawk Chat Bot",
            "prefix": "tawk",
            "routes": {
                "/get_all_data": {
                    "description": "Get all users chat data from the database.",
                    "type": "Private",
                },
                "/webhook": {
                    "description": "Store chat data in our database through webhook.",
                    "type": "Public",
                },
            },
        },
        "telephony": {
            "description": "Operations related to telephony integration",
            "name": "Telephony Integration",
            "prefix": "telephony",
            "routes": {
                "/assign_application_on_call": {
                    "description": "Assign application on call after call end.",
                    "type": "Private",
                },
                "/assigned_counsellor_on_missed_call": {
                    "description": "Assign and update Counsellor of any missed call.",
                    "type": "Private",
                },
                "/check_in_or_out": {
                    "description": "update the status of telephony check-in to 'Active' or 'Inactive'.",
                    "type": "Private",
                },
                "/counsellor_call_activity": {
                    "description": "Update the counsellor call activity.",
                    "type": "Private",
                },
                "/counsellor_call_log_header": {
                    "description": "Update the counsellor call log header.",
                    "type": "Private",
                },
                "/dashboard_header": {
                    "description": "Get telephony dashboard header data.",
                    "type": "Private",
                },
                "/download_call_recording": {
                    "description": "Download all call recordings.",
                    "type": "Private",
                },
                "/get_answered_by_users": {
                    "description": "Get list of all answered by users",
                    "type": "Private",
                },
                "/get_checkout_reasons": {
                    "description": "Get list of all telephony check-out reasons.",
                    "type": "Private",
                },
                "/get_dialed_by_users": {
                    "description": "Get list of all Dialed user.",
                    "type": "Private",
                },
                "/inbound_call_log": {
                    "description": "Fetch list of inbound call logs.",
                    "type": "Private",
                },
                "/initiate_call": {
                    "description": "Initiate call to lead by counsellor, head counsellor or moderator.",
                    "type": "Private",
                },
                "/landing_number": {
                    "description": "Get list of organization's landing numbers.",
                    "type": "Private",
                },
                "/missed_call_list": {
                    "description": "Get list of missed call data for missed call dashboard.",
                    "type": "Private",
                },
                "/missed_call_top_strip": {
                    "description": "Get missed call top strip data.",
                    "type": "Private",
                },
                "/multiple_check_in_or_out": {
                    "description": "update the multiple status of telephony check-in to 'Active' or 'Inactive'.",
                    "type": "Private",
                },
                "/outbound_call_log": {
                    "description": "Fetch list of outbound call logs.",
                    "type": "Private",
                },
                "/save_and_dispose": {
                    "description": "Dispose popup after call end by updating with application.",
                    "type": "Private",
                },
                "/webhook": {
                    "description": "Get data from telephony and save it accordingly",
                    "type": "Public",
                },
                "/call_quality_table": {
                    "description": "Call quality table for all counsellor calls",
                    "type": "Private",
                },
                "/call_quality_table_download": {
                    "description": "Call quality table for all counsellor calls download API",
                    "type": "Private",
                },
            },
        },
        "templates": {
            "description": "Operations related to templates management",
            "name": "Template",
            "prefix": "templates",
            "routes": {
                "/": {"description": "Get all templates.", "type": "Private"},
                "/add_or_get_template_category": {
                    "description": "Get the template data by template id.",
                    "type": "Private",
                },
                "/add_or_update/": {
                    "description": "Add or update template.",
                    "type": "Private",
                },
                "/add_template_merge_field/": {
                    "description": "Add template merge field.",
                    "type": "Private",
                },
                "/delete/": {
                    "description": "Delete template by id.",
                    "type": "Private",
                },
                "/delete_gallery_data": {
                    "description": "API for deleting the gallery data by passing the gallery data id (it should be single "
                                   "or multiple)",
                    "type": "Private",
                },
                "/download_media": {
                    "description": "API for getting links of selected media download",
                    "type": "Private",
                },
                "/gallery_upload": {
                    "description": "API for upload files like image, video and pdf and generate access link.",
                    "type": "Private",
                },
                "/get_media_gallery": {
                    "description": "API for getting all media data for template gallery",
                    "type": "Private",
                },
                "/get_media_uploaded_user_list": {
                    "description": "API for getting List of users who have uploaded photo/video/file",
                    "type": "Private",
                },
                "/get_spec_media_details": {
                    "description": "API for getting specific media data for template gallery",
                    "type": "Private",
                },
                "/get_template_details": {
                    "description": "Get the template data by template id.",
                    "type": "Private",
                },
                "/get_template_merge_fields/": {
                    "description": "Get template merge fields.",
                    "type": "Private",
                },
                "/otp/": {"description": "Get all OTP templates.", "type": "Private"},
                "/otp/add_or_update/": {
                    "description": "Create or update otp template.",
                    "type": "Private",
                },
                "/otp/delete/": {
                    "description": "Delete OTP template by id.",
                    "type": "Private",
                },
                "/otp/get_by_name_or_id/": {
                    "description": "Get data segment details by id or name.",
                    "type": "Private",
                },
                "/particular_role_user_list": {
                    "description": "User list according to particular role list for template creation module",
                    "type": "Private",
                },
                "/roles": {
                    "description": "API for getting all users role details list for template creation",
                    "type": "Private",
                },
                "/sender_email_id_list": {
                    "description": "Getting sender email id list of organization from the database.",
                    "type": "Private",
                },
                "/set_active/": {
                    "description": "Activate email template based on template id.",
                    "type": "Private",
                },
                "/tags/": {
                    "description": "Get all tag names based on template type.",
                    "type": "Private",
                },
                "/update_status/": {
                    "description": "Enable or disable status of template.",
                    "type": "Private",
                },
            },
        },
        "unsubscribe": {
            "description": "Operations related to unsubscribe module",
            "name": "Unsubscribe",
            "prefix": "unsubscribe",
            "routes": {
                "/collect_unsubscribed_students/": {
                    "description": "Stores unsubscribed students list into the cache.",
                    "type": "Public",
                }
            },
        },
        "user": {
            "description": "Operations for admin users",
            "name": "User",
            "prefix": "user",
            "routes": {
                "/change_password/": {
                    "description": "Change user password.",
                    "type": "Private",
                },
                "/chart_info/": {
                    "description": "Get/download the user chart information.",
                    "type": "Private",
                },
                "/create_new_user/": {
                    "description": "Create a New User.",
                    "type": "Private",
                },
                "/create_super_admin/": {
                    "description": "Create Super Admin.",
                    "type": "Private",
                },
                "/current_user_details/": {
                    "description": "Get current user details.",
                    "type": "Private",
                },
                "/delete_all_users/": {
                    "description": "Delete all user.",
                    "type": "Private",
                },
                "/delete_by_ids/": {
                    "description": "Delete users data by ids.",
                    "type": "Private",
                },
                "/dkper/user/{token}": {
                    "description": "Get user token.",
                    "type": "Public",
                },
                "/download_data/": {
                    "description": "Download users data by IDs.",
                    "type": "Private",
                },
                "/download_panelist/": {
                    "description": "Download panelists data by Ids.",
                    "type": "Private",
                },
                "/enable_or_disable/": {
                    "description": "Enable or disable user.",
                    "type": "Private",
                },
                "/enable_or_disable_users/": {
                    "description": "Enable or disable users by ids.",
                    "type": "Private",
                },
                "/get_all_menu_and_permission/": {
                    "description": "Get all users menu list and permissions.",
                    "type": "Private",
                },
                "/get_data_by_id/": {
                    "description": "Get user data by id.",
                    "type": "Private",
                },
                "/get_details/": {
                    "description": "Get all college user details.",
                    "type": "Private",
                },
                "/get_menu_and_permission/": {
                    "description": "Get menu list and permissions based on user type.",
                    "type": "Private",
                },
                "/list/": {"description": "Get list of user.", "type": "Private"},
                "/panelist_manager_header_info/": {
                    "description": "Get panelist manager header info.",
                    "type": "Private",
                },
                "/panelists/": {
                    "description": "Get panelist data with/without filter",
                    "type": "Private",
                },
                "/reset_password/": {
                    "description": "Reset Password of User.",
                    "type": "Public",
                },
                "/session_info/": {
                    "description": "Get session info of users.",
                    "type": "Private",
                },
                "/timeline/": {
                    "description": "Get timeline of users based on filter.",
                    "type": "Private",
                },
                "/update/": {
                    "description": "Update user data by id.",
                    "type": "Private",
                },
                "/update_permissions/": {
                    "description": "Update the user permission based on user_type.",
                    "type": "Private",
                },
            },
        },
        "whatsapp": {
            "description": "Operations related to whatsapp management",
            "name": "Whatsapp",
            "prefix": "whatsapp",
            "routes": {
                "/send_whatsapp_to_user/": {
                    "description": "Send whatsapp SMS to a particular student.",
                    "type": "Private",
                },
                "/webook/": {
                    "description": "Capture whatsapp activity through webhook.",
                    "type": "Public",
                },
                "/whatsapp_send_file": {
                    "description": "Send whatsapp file with text and current user.",
                    "type": "Private",
                },
            },
        },
        "document_Verification": {
            "description": "Operations related to document verification management",
            "name": "Document Verification",
            "prefix": "document_verification",
            "routes": {
                "/quick_view/": {
                    "description": "Get Quick View Details",
                    "type": "Private"
                },
                "/get_applications/": {
                    "description": "Get applications based on filter",
                    "type": "Private"
                },
                "/update_dv_status/": {
                    "description": "Update document Status",
                    "type": "Private"
                }
            },
        },
        "client_router": {
            "description": "Operations related to curd operations of client automation routes",
            "name": "Client Automation",
            "prefix": "client_automation",
            "routes": {
                "/add_college": {
                    "description": "Add college data.",
                    "type": "Private"
                },
                "/get_colleges": {
                    "description": "API endpoint to fetch a paginated list of colleges based on the role of the "
                                   "logged-in user.",
                    "type": "Private"
                },
                "/{college_id}/add_course": {
                    "description": "API to add course details to a college.",
                    "type": "Private"
                },
                "/add_features_screen": {
                    "description": "Add client screen details by the admin or account manager",
                    "type": "Private"
                },
                "/update_feature_screen": {
                    "description": "Update client screen details by the admin or account manager",
                    "type": "Private"
                },
                "/delete_feature_screen": {
                    "description": "Delete screen details by the super admin",
                    "type": "Private"
                },
                "/get_feature_screen": {
                    "description": "API to get screen details by the super admin.",
                    "type": "Private"
                },
                "/get_required_feature_roles": {
                    "description": "Retrieves required role information for a client's or college's screen configuration.",
                    "type": "Private"
                },
                "/save_signup_form/{college_id}": {
                    "description": "Save student registration form fields into the colleges collection.",
                    "type": "Private"
                },
                "/update_activation_status_of_college": {
                    "description": "Update the activation status of a college.",
                    "type": "Private"
                },
                "/get_screen_details": {
                    "description": "Get the student registration form fields for a specific college.",
                    "type": "Private"
                },
                "/list_of_all_colleges": {
                    "description": "Fetches application form fields along with college details, with pagination.",
                    "type": "Private"
                },
                "/update_status_of_college/": {
                    "description": "Update the status of one or more colleges.",
                    "type": "Private"
                },
                "/update_color_theme/": {
                    "description": "Update color theme API for Dynamic Student Dashboard",
                    "type": "Private"
                },
                "/get_color_theme/{college_id}": {
                    "description": "Get color theme API for Dynamic Student Dashboard",
                    "type": "Private"
                },
            },
        },
        "master_router": {
            "description": "Operations related to curd operations of master routes",
            "name": "Master Module",
            "prefix": "master",
            "routes": {
                "/create_master_stage": {
                    "description": "Create Master Stage",
                    "type": "Private"
                },
                "/get_all_master_stages": {
                    "description": "Get All Master Stages",
                    "type": "Private"
                },
                "/get_master_stage/{stage_id}": {
                    "description": "Get Master Stage by Id",
                    "type": "Private"
                },
                "/update_master_stage/{stage_id}": {
                    "description": "Update Master Stage by Id",
                    "type": "Private"
                },
                "/delete_master_stage/{stage_id}": {
                    "description": "Delete Master Stage by Id",
                    "type": "Private"
                },
                "/create_master_sub_stage": {
                    "description": "Create Master Sub Stage",
                    "type": "Private"
                },
                "/get_master_sub_stage/{sub_stage_id}": {
                    "description": "Get Master Sub Stage by ID",
                    "type": "Private"
                },
                "/get_all_master_sub_stages": {
                    "description": "Get all Master Sub Stages",
                    "type": "Private"
                },
                "/update_master_sub_stage/{sub_stage_id}": {
                    "description": "Update Master Sub Stage by Id",
                    "type": "Private"
                },
                "/delete_master_sub_stage/{sub_stage_id}": {
                    "description": "Delete Master Sub Stage by Id",
                    "type": "Private"
                },
                "/validate_key_name": {
                    "description": "Endpoint to validate the uniqueness and format of a given key name used for "
                                   "application fields",
                    "type": "Private"
                },
                "/Retrieve_all_stages_and_sub_stages": {
                    "description": "Retrieve all master stages and their associated sub stage.",
                    "type": "Private"
                },
                "/add_master_screen": {
                    "description": "Add master screen data.",
                    "type": "Private"
                },
                "/update_master_screen": {
                    "description": "Update master screen data.",
                    "type": "Private"
                },
                "/delete_master_screen": {
                    "description": "Delete the master screen data",
                    "type": "Private"
                },
                "/get_master_screen": {
                    "description": "Fetch screen details by the super admin.",
                    "type": "Private"
                },
                "/retrieve_all_stages": {
                    "description": "Retrieves all stages and sub-stages for a given client or college.",
                    "type": "Private"
                },
                "/fetch_list_of_all_fields": {
                    "description": "Fetches application form fields from the database with optional search "
                                   "and pagination.",
                    "type": "Private"
                },
                "/validate_registration_form": {
                    "description": "Validates the registration form for a specific client or college.",
                    "type": "Private"
                },
                "/validate_client_or_college_form_data": {
                    "description": "Validates the form data for a specific client or college.",
                    "type": "Private"
                },
                "/update_client_or_college_form_data": {
                    "description": "Updates the form data for a specific client or college.",
                    "type": "Private"
                },
                "/get_form_options": {
                    "description": "Retrieves a specific form option configuration by its ID.",
                    "type": "Private"
                },
                "/create_form_option": {
                    "description": "Creates a new form option based on the provided field data.",
                    "type": "Private"
                },
                "/return_api_functions": {
                    "description": "Fetched the Api functions based on provided client or college ID.",
                    "type": "Private"
                },
                "/get_all_templates/": {
                    "description": "Retrieve all application form templates.",
                    "type": "Private"
                },
                "/get_user_registration_fields": {
                    "description": "Fetch user registration fields based on role.",
                    "type": "Private"
                },
                "/create_user": {
                    "description": "Create a new user based on dynamic fields associated with the target role.",
                    "type": "Private"
                }
            }
        },
        "scholarship": {
            "description": "Operations related to scholarship",
            "name": "Scholarship",
            "prefix": "scholarship",
            "routes": {
                "/create/": {
                    "description": "Create a scholarship",
                    "type": "Private"
                },
                "/programs_fee_and_eligible_count_info/": {
                    "description": "Get programs fee and eligible count information based on scholarship information.",
                    "type": "Private"
                },
                "/update_status/": {
                    "description": "Update scholarship status.",
                    "type": "Private"
                },
                "s/get_information/": {
                    "description": "Get scholarships information.",
                    "type": "Private"
                },
                "/table_information/": {
                    "description": "Get scholarship table information like scholarship name along program names, count,"
                                   " eligible count, offered count, availed_by count, available count, availed_amount.",
                    "type": "Private"
                },
                "/get_summary_data/": {
                    "description": "Get scholarship summary information like total scholarship count along with "
                                   "active/closed count, total availed count.",
                    "type": "Private"
                },
                "/give_custom_scholarship/": {
                    "description": "Give custom scholarship to applicants.",
                    "type": "Private"
                },
                "/get_give_custom_scholarship_table_data/": {
                    "description": "Get give custom scholarship table data.",
                    "type": "Private"
                },
                "/applicants_data/": {
                    "description": "Get the scholarship applicants data based on scholarship data type.",
                    "type": "Private"
                },
                "/send_letter_to_applicants/": {
                    "description": "Send scholarship letter to applicants.",
                    "type": "Private"
                },
                "/delist_applicants/": {
                    "description": "De-list applicants from scholarship list.",
                    "type": "Private"
                },
                "/change_default_scholarship/": {
                    "description": "Change default scholarship of applicant.",
                    "type": "Private"
                },
                "/overview_details/": {
                    "description": "Get the scholarship overview details.",
                    "type": "Private"
                }
            }
        },
        "client_student_dashboard": {
            "description": "CRUD Operations related to Client Stages and Sub Stages Management",
            "name": "Client Student Dashboard",
            "prefix": "client_student_dashboard",
            "routes": {
                "/set_default_client_stages": {
                    "description": "Set Default Client Stages",
                    "type": "Private"
                },
                "/create_client_stage": {
                    "description": "Create Client Stage",
                    "type": "Private"
                },
                "/get_all_client_stages/": {
                    "description": "Get All Client Stages",
                    "type": "Private"
                },
                "/get_client_stage/{stage_id}": {
                    "description": "Get Client Stage by Id",
                    "type": "Private"
                },
                "/update_client_stage/{stage_id}": {
                    "description": "Update Client Stage by Id",
                    "type": "Private"
                },
                "/delete_client_stage/": {
                    "description": "Delete Client Stage by Id",
                    "type": "Private"
                },
                "/set_default_client_sub_stages": {
                    "description": "Set Default Client Sub Stages",
                    "type": "Private"
                },
                "/create_client_sub_stage": {
                    "description": "Create Client Sub Stage",
                    "type": "Private"
                },
                "/get_client_sub_stage/": {
                    "description": "Get Client Sub Stage by ID",
                    "type": "Private"
                },
                "/get_all_client_sub_stages/": {
                    "description": "Get all Client Sub Stages",
                    "type": "Private"
                },
                "/update_client_sub_stage/{sub_stage_id}": {
                    "description": "Update Client Sub Stage by Id",
                    "type": "Private"
                },
                "/delete_client_sub_stage/": {
                    "description": "Delete Client Sub Stage by Id",
                    "type": "Private"
                },
                "/remove_fields": {
                    "description": "Remove Specified Fields from Client",
                    "type": "Private"
                },
                "/relocate_field": {
                    "description": "Relocate Specified Fields",
                    "type": "Private"
                },
                "/custom_field/": {
                    "description": "Add Custom Fields",
                    "type": "Private"
                },
                "/validate_passing_year": {
                    "description": "Relocate Specified Fields",
                    "type": "Private"
                },
            }
        },
    }
}]
