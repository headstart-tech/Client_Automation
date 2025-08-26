# Indexes data

indexes = {
    "queries": [
        {
            "name": "student_id_1",
            "keys": {
                "student_id": 1
            }
        },
        {
            "name": "status_1",
            "keys": {
                "status": 1
            }
        }
    ],
    "data_segment_student_mapping": [
        {
            "name": "student_id_1",
            "keys": {
                "student_id": 1
            }
        }
    ],
    "activity_email": [
        {
            "name": "created_at_1",
            "keys": {
                "created_at": 1
            }
        },
        {
            "name": "total_email_1",
            "keys": {
                "total_email": 1
            }
        },
        {
            "name": "created_at_1_total_email_1",
            "keys": {
                "created_at": 1,
                "total_email": 1
            }
        }
    ],
    "offline_data": [
        {
            "name": "duplicate_lead_data_1",
            "keys": {
                "duplicate_lead_data": 1
            }
        },
        {
            "name": "failed_lead_data_1",
            "keys": {
                "failed_lead_data": 1
            }
        },
        {
            "name": "imported_by_1",
            "keys": {
                "imported_by": 1
            }
        },
        {
            "name": "import_status_1",
            "keys": {
                "import_status": 1
            }
        }
    ],
    "leadsFollowUp": [
        {
            "name": "student_id_1",
            "keys": {
                "student_id": 1
            }
        },
        {
            "name": "lead_stage_1",
            "keys": {
                "lead_stage": 1
            }
        },
        {
            "name": "application_id_1",
            "keys": {
                "application_id": 1
            }
        },
        {
            "name": "previous_lead_stage_1_previous_lead_stage_label_1_lead_stage_1_lead_stage_label_1",
            "keys": {
                "previous_lead_stage": 1,
                "previous_lead_stage_label": 1,
                "lead_stage": 1,
                "lead_stage_label": 1
            }
        }
    ],
    "notifications": [
        {
            "name": "send_to_1_created_at_-1_hide_1",
            "keys": {
                "send_to": 1,
                "created_at": -1,
                "hide": 1
            }
        }
    ],
    "dataSegment": [
        {
            "name": "data_segment_name_1",
            "keys": {
                "data_segment_name": 1
            }
        },
        {
            "name": "module_name_1_segment_type_1_enabled_1",
            "keys": {
                "module_name": 1,
                "segment_type": 1,
                "enabled": 1
            }
        }
    ],
    "communicationLog": [
        {
            "name": "student_id_1",
            "keys": {
                "student_id": 1
            }
        }
    ],
    "whatsapp_sms_activity": [
        {
            "name": "send_to_1",
            "keys": {
                "send_to": 1
            }
        }
    ],
    "call_activity": [
        {
            "name": "caller_id_1",
            "keys": {
                "caller_id": 1
            }
        },
        {
            "name": "timestamp_-1",
            "keys": {
                "timestamp": -1
            }
        },
        {
            "name": "call_from_1",
            "keys": {
                "call_from": 1
            }
        },
        {
            "name": "call_to_1",
            "keys": {
                "call_to": 1
            }
        },
        {
            "name": "call_to_number_1",
            "keys": {
                "call_to_number": 1
            }
        },
        {
            "name": "call_from_number_1",
            "keys": {
                "call_from_number": 1
            }
        },
        {
            "name": "call_from_1_show_popup_1",
            "keys": {
                "call_from": 1,
                "show_popup": 1
            }
        },
        {
            "name": "call_to_1_show_popup_1",
            "keys": {
                "call_to": 1,
                "show_popup": 1
            }
        }
    ],
    "studentSecondaryDetails": [
        {
            "name": "student_id_1",
            "keys": {
                "student_id": 1
            }
        },
        {
            "name": "education_details_inter_school_details_obtained_cgpa",
            "keys": {
                "education_details.inter_school_details.obtained_cgpa": 1
            }
        },
        {
            "name": "education_details.inter_school_details.obtained_cgpa_1_education_details.inter_school_details.board_1_education_details.inter_school_details.is_pursuing_1_education_details.tenth_school_details_1_education_details.inter_school_details.marking_scheme_1",
            "keys": {
                "education_details.inter_school_details.obtained_cgpa": 1,
                "education_details.inter_school_details.board": 1,
                "education_details.inter_school_details.is_pursuing": 1,
                "education_details.tenth_school_details": 1,
                "education_details.inter_school_details.marking_scheme": 1
            }
        }
    ],
    "raw_data": [
        {
            "name": "created_at_-1",
            "keys": {
                "created_at": -1
            }
        }
    ],
    "sms_activity": [
        {
            "name": "sms_response.submitResponses.state_1",
            "keys": {
                "sms_response.submitResponses.state": 1
            }
        },
        {
            "name": "send_to_1",
            "keys": {
                "send_to": 1
            }
        }
    ],
    "automation_communicationLog": [
        {
            "name": "student_id_1",
            "keys": {
                "student_id": 1
            }
        },
        {
            "name": "data_segment_id_1",
            "keys": {
                "data_segment_id": 1
            }
        }
    ],
    "studentsPrimaryDetails": [
        {
            "name": "user_name_1",
            "keys": {
                "user_name": 1
            },
            "type": "Unique Index"
        },
        {
            "name": "is_email_verify_1_unsubscribe_1",
            "keys": {
                "is_email_verify": 1,
                "unsubscribe": 1
            }
        },
        {
            "name": "is_email_verify_1_unsubscribe_1_is_verify_1",
            "keys": {
                "is_email_verify": 1,
                "unsubscribe": 1,
                "is_verify": 1
            }
        },
        {
            "name": "unsubscribe_1",
            "keys": {
                "unsubscribe": 1
            }
        },
        {
            "name": "unsubscribe_1_publisher_id_1_is_verify_1",
            "keys": {
                "unsubscribe": 1,
                "publisher_id": 1,
                "is_verify": 1
            }
        },
        {
            "name": "is_verify_1",
            "keys": {
                "is_verify": 1
            }
        },
        {
            "name": "is_verify_1_publisher_id_1",
            "keys": {
                "is_verify": 1,
                "publisher_id": 1
            }
        },
        {
            "name": "basic_details.mobile_number_1",
            "keys": {
                "basic_details.mobile_number": 1
            }
        },
        {
            "name": "allocate_to_counselor.counselor_id_1",
            "keys": {
                "allocate_to_counselor.counselor_id": 1
            }
        },
        {
            "name": "41b76c314ed6192d529928eb21abd1ca",
            "keys": {
                "is_verify": 1,
                "address_details.communication_address.state.state_code": 1,
                "source.primary_source.utm_source": 1,
                "created_at": 1,
                "allocate_to_counselor.counselor_id": 1,
                "source.primary_source.utm_medium": 1,
                "source.primary_source.lead_type": 1,
                "source.primary_source": 1,
                "source.secondary_source": 1,
                "source.tertiary_source": 1,
                "student_primary.address_details.communication_address.city.city_name": 1,
                "extra_fields": 1,
                "basic_details.mobile_number": 1
            }
        },
        {
            "name": "1bfed4d98a924ba959f3ac734b8f1bfd",
            "keys": {
                "is_verify": 1,
                "address_details.communication_address.state.state_code": 1,
                "address_details.communication_address.city.city_name": 1,
                "allocate_to_counselor.counselor_id": 1,
                "source.primary_source": 1,
                "source.secondary_source": 1,
                "source.teritiary_source": 1,
                "source.primary_source.utm_source": 1,
                "source.primary_source.utm_medium": 1,
                "source.primary_source.lead_type": 1,
                "extra_fields": 1
            }
        },
        {
            "name": "created_at_-1",
            "keys": {
                "created_at": -1
            }
        },
        {
            "name": "address_details.communication_address.state.state_id_1",
            "keys": {
                "address_details.communication_address.state.state_id": 1
            }
        },
        {
            "name": "_id_1_college_id_1_allocate_to_counselor.counselor_id_1_created_at_1",
            "keys": {
                "_id": 1,
                "college_id": 1,
                "allocate_to_counselor.counselor_id": 1,
                "created_at": 1
            }
        },
        {
            "name": "85218a34a5af416b47d2935304cb36ae",
            "keys": {
                "is_verify": 1,
                "address_details.communication_address.state.state_code": 1,
                "address_details.communication_address.city.city_name": 1,
                "address_details.communication_address.country.country_code": 1,
                "source.primary_source.utm_source": 1,
                "source.primary_source.utm_medium": 1,
                "source.primary_source.lead_type": 1,
                "source.primary_source": 1,
                "source.secondary_source": 1,
                "source.teritiary_source": 1,
                "created_at": 1,
                "allocate_to_counselor.counselor_id": 1,
                "extra_fields": 1,
                "registration_device": 1,
                "registration_attempts": 1,
                "last_registration_date": 1,
                "basic_details.mobile_number": 1,
                "first_lead_activity_date": 1,
                "last_modified_date": 1
            }
        },
        {
            "name": "address_details_1",
            "keys": {
                "address_details": 1
            }
        },
        {
            "name": "address_details_1_accept_payment_1_address_details.communication_address.address_line2_1",
            "keys": {
                "address_details": 1,
                "accept_payment": 1,
                "address_details.communication_address.address_line2": 1
            }
        },
        {
            "name": "address_details_-1",
            "keys": {
                "address_details": -1
            }
        }
    ],
    "studentTimeline": [
        {
            "name": "student_id_1",
            "keys": {
                "student_id": 1
            }
        }
    ],
    "studentApplicationForms": [
        {
            "name": "current_stage_1",
            "keys": {
                "current_stage": 1
            }
        },
        {
            "name": "college_id_1",
            "keys": {
                "college_id": 1
            }
        },
        {
            "name": "college_id_1_declaration_1",
            "keys": {
                "college_id": 1,
                "declaration": 1
            }
        },
        {
            "name": "application.current_stage_1",
            "keys": {
                "application.current_stage": 1
            }
        },
        {
            "name": "student_id_1_allocate_to_counselor.counselor_id_1",
            "keys": {
                "student_id": 1,
                "allocate_to_counselor.counselor_id": 1
            }
        },
        {
            "name": "college_id_1_enquiry_date_-1",
            "keys": {
                "college_id": 1,
                "enquiry_date": -1
            }
        },
        {
            "name": "course_id_1_spec_name1_1_enquiry_date_-1",
            "keys": {
                "course_id": 1,
                "spec_name1": 1,
                "enquiry_date": -1
            }
        },
        {
            "name": "allocate_to_counselor.counselor_id_1",
            "keys": {
                "allocate_to_counselor.counselor_id": 1
            }
        },
        {
            "name": "9bdb31ddc947feb63b7e3c9d7a64e7ab",
            "keys": {
                "college_id": 1,
                "enquiry_date": 1,
                "current_stage": 1,
                "course_id": 1,
                "spec_name1": 1,
                "payment_initiated": 1,
                "payment_info.status": 1,
                "payment_info.created_at": 1,
                "declaration": 1
            }
        },
        {
            "name": "f8279ece1912c4a44f46ffd4fc91a05b",
            "keys": {
                "college_id": 1,
                "enquiry_date": 1,
                "current_stage": 1,
                "course_id": 1,
                "spec_name_1": 1,
                "payment_initiated": 1,
                "payment_info.status": 1,
                "payment_info.created_at": 1,
                "created_at": 1,
                "allocate_to_counselor.counselor_id": 1,
                "declaration": 1
            }
        },
        {
            "name": "82ebfc374e97cb571bba134791aa3bae",
            "keys": {
                "college_id": 1,
                "payment_info.status": 1,
                "enquiry_date": 1,
                "current_stage": 1,
                "declaration": 1,
                "course_id": 1,
                "spec_name_1": 1,
                "payment_initiated": 1,
                "payment_info.created_at": 1,
                "allocate_to_counselor.counselor_id": 1
            }
        },
        {
            "name": "custom_application_id_1",
            "keys": {
                "custom_application_id": 1
            }
        },
        {
            "name": "student_id_1_payment_info.status_1_admission_1",
            "keys": {
                "student_id": 1,
                "payment_info.status": 1,
                "admission": 1
            }
        },
        {
            "name": "30a811f64a88626da27dac92527c44ba",
            "keys": {
                "student_id": 1
            }
        }
    ]
}