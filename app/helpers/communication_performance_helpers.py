"""
Communication Performance Module data helper.
"""
import datetime
import json

from app.database.aggregation.admin_user import AdminUser
from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj
from bson.objectid import ObjectId


class CommunicationPerformanceHeader:
    """
    All related functions of communication performance
    """

    async def counselor_ids(self, user: dict, college_id: str ) -> list:
        """
         Get the list of counselors ids.

         Params:
            user (dict): the details of the user
            college_id (str): id of the college

        Returns:
            list: A list of counselor ids based on user role.
        """
        role = user.get("role", {}).get("role_name")
        counselor_id = []
        if role == "college_counselor":
            counselor_id = [ObjectId(user.get("_id"))]
        elif role == "college_head_counselor":
            counselor_id = await AdminUser().get_users_ids_by_role_name(
                "college_counselor", college_id, user.get("_id")
            )
            counselor_id.append(ObjectId(user.get("_id")))
        return counselor_id

    async def header_details(self, date_range: dict, change_indicator: str, counselor_id: list) -> dict:
        """
            Retrieves header details based on a given date range and change indicator.

            Params:
                date_range (dict): A dictionary containing start and end dates.
                                   Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
                change_indicator (str): A string indicating the type of change to be queried.
                                         Example: "last_7_days", "last_15_days", or "last_30_days".
                counselor_id (list): list of counselor ids for filtering the data based on counselors

            Returns:
                dict: A dictionary containing header details, potentially including counts, summaries,
                      or any relevant data based on the provided date range and change indicator.
        """
        data = await self.communication_header_helper(date_range, counselor_id)
        start_date, middle_date, previous_date = await utility_obj. \
            get_start_date_and_end_date_by_change_indicator(change_indicator)
        today = datetime.date.today()
        previous_date_data = await self.communication_header_helper(
            date_range={"start_date": str(start_date),"end_date": str(middle_date)},
            counselor_id=counselor_id
        )
        current_date_data = await self.communication_header_helper(
            date_range={"start_date": str(previous_date),"end_date": str(today)},
            counselor_id=counselor_id
        )

        total_communication_change_indicator = await utility_obj.get_percentage_difference_with_position(
            previous_date_data.get("communication_sent", 0), current_date_data.get("communication_sent", 0))
        total_email_change_indicator = await utility_obj.get_percentage_difference_with_position(
            previous_date_data.get("email_sent", 0), current_date_data.get("email_sent", 0))
        total_sms_change_indicator = await utility_obj.get_percentage_difference_with_position(
            previous_date_data.get("sms_sent", 0), current_date_data.get("sms_sent", 0))
        total_whatsapp_change_indicator = await utility_obj.get_percentage_difference_with_position(
            previous_date_data.get("whatsapp_sent", 0), current_date_data.get("whatsapp_sent", 0))

        data.update({
            "communication_sent_perc": total_communication_change_indicator.get("percentage", 0),
            "communication_sent_pos": total_communication_change_indicator.get("position", "equal"),
            "email_sent_perc": total_email_change_indicator.get("percentage", 0),
            "email_sent_pos": total_email_change_indicator.get("position", "equal"),
            "sms_sent_perc": total_sms_change_indicator.get("percentage", 0),
            "sms_sent_pos": total_sms_change_indicator.get("position", "equal"),
            "whatsapp_sent_perc": total_whatsapp_change_indicator.get("percentage", 0),
            "whatsapp_sent_pos": total_whatsapp_change_indicator.get("position", "equal"),

        })
        return data

    async def communication_header_helper(self, date_range: dict, counselor_id: list) -> dict:
        """
            Provides communication header details based on the specified date range.

            Params:
                date_range (dict): A dictionary containing the start and end dates to filter the data.
                                   Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
                counselor_id (list): list of counselor ids for filtering the data based on counselors

            Returns:
                dict: A dictionary containing processed communication header details.
                      This may include counts, summaries, or other relevant data filtered
                      by the provided date range.
        """
        student_ids = None
        if counselor_id:
            student_ids = await self.list_student_ids(counselor_id)
        pipeline = [
            *(
                [
                    {
                        '$match': {
                            'student_id': {
                                '$in': student_ids
                            }
                        }
                    }
                ]
                if counselor_id else []
            ),
            {
                '$project': {
                    'email_sent': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$email_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {"$and": []}
                            }
                        }
                    },
                    'email_sent_automated': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$email_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                {
                                                    '$ifNull': [
                                                        '$$data.release_type', 'Manual'
                                                    ]
                                                }, 'Automation'
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'email_sent_manual': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$email_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                {
                                                    '$ifNull': [
                                                        '$$data.release_type', 'Manual'
                                                    ]
                                                }, 'Manual'
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'sms_sent': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$sms_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {"$and": []}
                            }
                        }
                    },
                    'sms_sent_automated': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$sms_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                {
                                                    '$ifNull': [
                                                        '$$data.release_type', 'Manual'
                                                    ]
                                                }, 'Automation'
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'sms_sent_manual': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$sms_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                {
                                                    '$ifNull': [
                                                        '$$data.release_type', 'Manual'
                                                    ]
                                                }, 'Manual'
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'whatsapp_sent': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$whatsapp_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {"$and": []}
                            }
                        }
                    },
                    'whatsapp_sent_automated': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$whatsapp_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                {
                                                    '$ifNull': [
                                                        '$$data.release_type', 'Manual'
                                                    ]
                                                }, 'Automation'
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'whatsapp_sent_manual': {
                        '$size': {
                            '$filter': {
                                'input': {
                                    '$ifNull': [
                                        '$whatsapp_summary.transaction_id', []
                                    ]
                                },
                                'as': 'data',
                                'cond': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                {
                                                    '$ifNull': [
                                                        '$$data.release_type', 'Manual'
                                                    ]
                                                }, 'Manual'
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }, {
                '$group': {
                    '_id': None,
                    'email_sent': {
                        '$sum': '$email_sent'
                    },
                    'email_sent_automated': {
                        '$sum': '$email_sent_automated'
                    },
                    'email_sent_manual': {
                        '$sum': '$email_sent_manual'
                    },
                    'sms_sent': {
                        '$sum': '$sms_sent'
                    },
                    'sms_sent_automated': {
                        '$sum': '$sms_sent_automated'
                    },
                    'sms_sent_manual': {
                        '$sum': '$sms_sent_manual'
                    },
                    'whatsapp_sent': {
                        '$sum': '$whatsapp_sent'
                    },
                    'whatsapp_sent_automated': {
                        '$sum': '$whatsapp_sent_automated'
                    },
                    'whatsapp_sent_manual': {
                        '$sum': '$whatsapp_sent_manual'
                    }
                }
            }
        ]
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date')
            )

            for stage in pipeline:
                if "$project" in stage:
                    for field in stage["$project"]:
                        if "$size" in stage["$project"][field]:
                            cond = stage["$project"][field]["$size"]["$filter"]["cond"]
                            if "$and" in cond:
                                cond["$and"].extend([
                                    {"$gte": ["$$data.created_at", start_date]},
                                    {"$lt": ["$$data.created_at", end_date]}
                                ])
        result = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        result = result[0] if result else {}
        result["communication_sent"] = result.get("email_sent", 0) + result.get("sms_sent", 0) + result.get(
            "whatsapp_sent", 0)
        return result

    async def counselor_pipeline(self, counselor_id: list) -> list:
        """
        Get lookup pipeline information for match data based on counselors.

        Params:
            counselor_id (list): List of counselors ids.

        Returns:
            list: A list of dictionaries where each dictionary represents pipeline stage along with information.
        """
        return [{
            '$lookup': {
                'from': 'studentsPrimaryDetails',
                'localField': 'student_id',
                'foreignField': '_id',
                'as': 'students'
            }
        }, {
            '$unwind': '$students'
        }, {
            '$match': {
                'students.allocate_to_counselor.counselor_id': {
                    '$in': counselor_id
                }
            }
        }]

    async def date_wise_performance_graph(self, date_range: dict, communication_type: str, counselor_id: list) -> list:
        """
            Generates date-wise performance data for a specific communication type
            within the specified date range.

            Params:
                date_range (dict): A dictionary containing the start and end dates to filter the data.
                                   Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
                communication_type (str): The type of communication to analyze.
                                          Example: "email", "sms", or "whatsapp".
                counselor_id (list): List of counselor ids to filter data

            Returns:
                list: A list of dictionaries where each dictionary represents performance data
                      for a specific date. Example:
                      [
                          {"date": "01 Jan 2024", "data_sent": 100, "data_delivered": 5},
                          {"date": "02 Jan 2024", "data_sent": 120, "data_delivered": 3},
                          ...
                      ]
        """
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=30)
        end_date = end_date.strftime("%Y-%m-%d")
        start_date = start_date.strftime("%Y-%m-%d")
        if date_range:
            start_date, end_date = date_range.get('start_date'), date_range.get('end_date')
        start_date, end_date = await utility_obj.date_change_format(
            start_date, end_date)
        number_of_days = int((end_date - start_date).days) + 1
        pipeline = [
            {
                '$match': {
                    f'{communication_type}_summary.transaction_id.created_at': {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }
            },
            *(await self.counselor_pipeline(counselor_id)if counselor_id else []),
            {
                '$project': {
                    f'{communication_type}_summary.transaction_id': 1
                }
            }, {
                '$unwind': {
                    'path': f'${communication_type}_summary.transaction_id',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$match': {
                    f'{communication_type}_summary.transaction_id.created_at': {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }
            },
            {
                '$project': {
                    'date': {
                        '$dateToString': {
                            'format': '%d %b %Y',
                            'date': f'${communication_type}_summary.transaction_id.created_at'
                        }
                    },
                    'dateObj': f'${communication_type}_summary.transaction_id.created_at',
                    'data_sent': {
                        '$cond': {
                            'if': {
                                '$gt': [
                                    f'${communication_type}_summary.transaction_id', None
                                ]
                            },
                            'then': 1,
                            'else': 0
                        }
                    },
                    'data_delivered': {
                        '$cond': {
                            'if': {
                                '$and': [
                                    {
                                        '$eq': [
                                            f'${communication_type}_summary.transaction_id.email_delivered', True
                                        ]
                                    }, {
                                        '$ne': [
                                            f'${communication_type}_summary.transaction_id.email_delivered', None
                                        ]
                                    }
                                ]
                            },
                            'then': 1,
                            'else': 0
                        }
                    }
                }
            }, {
                '$group': {
                    '_id': '$date',
                    'dateObj': {'$first': '$dateObj'},
                    'data_sent': {
                        '$sum': '$data_sent'
                    },
                    'data_delivered': {
                        '$sum': '$data_delivered'
                    }
                }
            }, {
                '$sort': {
                    'dateObj': 1
                }
            }, {
                '$facet': {
                    'data': [
                        {
                            '$project': {
                                'date': '$_id',
                                'dateObj': 1,
                                'data_sent': 1,
                                'data_delivered': 1
                            }
                        }
                    ],
                    'allDates': [
                        {
                            '$project': {
                                '_id': 0,
                                'dates': {
                                    '$map': {
                                        'input': {"$range": [1, number_of_days + 1]},
                                        'as': 'day',
                                        'in': {
                                            'date': {
                                                '$dateToString': {
                                                    'format': '%d %b %Y',
                                                    'date': {
                                                        '$add': [
                                                            start_date, {
                                                                '$multiply': [
                                                                    '$$day', 86400000
                                                                ]
                                                            }
                                                        ]
                                                    }
                                                }
                                            },
                                            'dateObj': {
                                                '$add': [
                                                    start_date, {
                                                        '$multiply': [
                                                            '$$day', 86400000
                                                        ]
                                                    }
                                                ]
                                            },
                                            'data_sent': 0,
                                            'data_delivered': 0
                                        }
                                    }
                                }
                            }
                        }, {
                            '$unwind': '$dates'
                        }, {
                            '$replaceRoot': {
                                'newRoot': '$dates'
                            }
                        }
                    ]
                }
            }, {
                '$project': {
                    'merged': {
                        '$concatArrays': [
                            '$data', '$allDates'
                        ]
                    }
                }
            }, {
                '$unwind': '$merged'
            }, {
                '$replaceRoot': {
                    'newRoot': '$merged'
                }
            }, {
                '$group': {
                    '_id': '$date',
                    'dateObj': {'$first': '$dateObj'},
                    'data_sent': {
                        '$max': '$data_sent'
                    },
                    'data_delivered': {
                        '$max': '$data_delivered'
                    }
                }
            },
            {
                '$sort': {
                    'dateObj': 1
                }
            }
        ]
        result = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        return result

    async def release_details(self, date_range: dict, communication_type: str, counselor_id:list):
        """
                Retrieves release details for a specific communication type within the given date range.
                Optionally supports preparing the details for download.

                Params:
                    date_range (dict): A dictionary specifying the start and end dates for filtering the data.
                                       Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
                    communication_type (str): The type of communication to analyze.
                                              Example: "email", "sms", or "whatsapp".

                Returns:
                    list: A list containing the release details.
                Raises:
                    ValueError: If the `date_range` dictionary is missing required keys or contains invalid values.
                    TypeError: If `date_range` is not a dictionary or `communication_type` is not a string.
        """
        if communication_type == "email":
            pipeline = [
                {
                    '$match': {
                        'email_summary': {
                            '$exists': True
                        }
                    }
                },
                *(await self.counselor_pipeline(counselor_id)if counselor_id else []),
                {
                    '$project': {
                        'manual_releases': {
                            'sent': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            "$and": [
                                                {'$eq': [
                                                    {
                                                        '$ifNull': [
                                                            '$$transaction.release_type', 'Manual'
                                                        ]
                                                    }, 'Manual'
                                                ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'delivered': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Manual'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_delivered', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'open': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Manual'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_open', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'click': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Manual'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_click', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'bounce': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Manual'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_bounce', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        },
                        'automated_releases': {
                            'sent': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            "$and": [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Automation'
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'delivered': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Automation'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_delivered', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'open': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Automation'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_open', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'click': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Automation'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_click', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            'bounce': {
                                '$size': {
                                    '$filter': {
                                        'input': '$email_summary.transaction_id',
                                        'as': 'transaction',
                                        'cond': {
                                            '$and': [
                                                {
                                                    '$eq': [
                                                        {
                                                            '$ifNull': [
                                                                '$$transaction.release_type', 'Manual'
                                                            ]
                                                        }, 'Automation'
                                                    ]
                                                }, {
                                                    '$eq': [
                                                        '$$transaction.email_bounce', True
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'manual_releases_sent': {
                            '$sum': '$manual_releases.sent'
                        },
                        'manual_releases_delivered': {
                            '$sum': '$manual_releases.delivered'
                        },
                        'manual_releases_open': {
                            '$sum': '$manual_releases.open'
                        },
                        'manual_releases_click': {
                            '$sum': '$manual_releases.click'
                        },
                        'manual_releases_bounce': {
                            '$sum': '$manual_releases.bounce'
                        },
                        'automated_releases_sent': {
                            '$sum': '$automated_releases.sent'
                        },
                        'automated_releases_delivered': {
                            '$sum': '$automated_releases.delivered'
                        },
                        'automated_releases_open': {
                            '$sum': '$automated_releases.open'
                        },
                        'automated_releases_click': {
                            '$sum': '$automated_releases.click'
                        },
                        'automated_releases_bounce': {
                            '$sum': '$automated_releases.bounce'
                        }
                    }
                }, {
                    '$project': {
                        "_id": 0,
                        'manual_releases': {
                            'sent': '$manual_releases_sent',
                            'delivered': '$manual_releases_delivered',
                            'delivery': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$manual_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$manual_releases_delivered', '$manual_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            },
                            'open': '$manual_releases_open',
                            'open_percentage': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$manual_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$manual_releases_open', '$manual_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            },
                            'click': '$manual_releases_click',
                            'click_percentage': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$manual_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$manual_releases_click', '$manual_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            },
                            'bounce': '$manual_releases_bounce',
                            'bounce_percentage': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$manual_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$manual_releases_bounce', '$manual_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            }
                        },
                        'automated_releases': {
                            'sent': '$automated_releases_sent',
                            'delivered': '$automated_releases_delivered',
                            'delivery': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$automated_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$automated_releases_delivered', '$automated_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            },
                            'open': '$automated_releases_open',
                            'open_percentage': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$automated_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$automated_releases_open', '$automated_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            },
                            'click': '$automated_releases_click',
                            'click_percentage': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$automated_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$automated_releases_click', '$automated_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            },
                            'bounce': '$automated_releases_bounce',
                            'bounce_percentage': {
                                '$cond': [
                                    {
                                        '$gt': [
                                            '$automated_releases_sent', 0
                                        ]
                                    }, {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$automated_releases_bounce', '$automated_releases_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    }, 0
                                ]
                            }
                        }
                    }
                }
            ]
            unsubscribe_pipeline = [
                {
                    "$match": {
                         "unsubscribe.value": True
                    }
                },
                *(
                    [{
                        '$match': {
                            'allocate_to_counselor.counselor_id': {
                                '$in': counselor_id
                            }
                        }
                    }]
                    if counselor_id else []
                ),
                {
                    '$group': {
                        '_id': {
                            '$ifNull': [
                                '$unsubscribe.release_type', 'Manual'
                            ]
                        },
                        'count': {
                            '$sum': 1
                        }
                    }
                }, {
                    '$project': {
                        '_id': 0,
                        'release_type': '$_id',
                        'count': 1
                    }
                }
            ]
            if date_range:
                start_date, end_date = await utility_obj.date_change_format(
                    date_range.get('start_date'), date_range.get('end_date'))
                date_filter = [
                    {
                        "$gte": [
                            "$$transaction.created_at",
                            start_date
                        ]
                    },
                    {
                        "$lte": [
                            "$$transaction.created_at",
                            end_date
                        ]
                    }
                ]
                for field in ["sent", "delivered", "open", "click", "bounce"]:
                    x = 4 if counselor_id else 1
                    (pipeline[x].get("$project", {}).get("manual_releases", {}).get(f"{field}", {}).get("$size", {}).
                     get("$filter", {}).get("cond", {}).get("$and").extend(date_filter))
                    (pipeline[x].get("$project", {}).get("automated_releases", {}).get(f"{field}", {}).get("$size", {}).
                     get("$filter", {}).get("cond", {}).get("$and").extend(date_filter))
                unsubscribe_pipeline.insert(0, {
                    "$match": {
                        "unsubscribe.timestamp": {"$gte": start_date, "$lte": end_date}
                    }
                })
            results = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
            unsubscribed_data = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
                unsubscribe_pipeline).to_list(None)
            raw_unsubscribed_data = await DatabaseConfiguration().raw_data.aggregate(
                unsubscribe_pipeline).to_list(None)
            result_data = results[0] if results else {}
            result_data['manual_releases'].update({
                'unsubscribe': 0,
                "unsubscribe_percentage": 0

            })
            result_data['automated_releases'].update({
                'unsubscribe': 0,
                "unsubscribe_percentage": 0

            })
            for entry in unsubscribed_data:
                release_type = entry['release_type']
                raw_details = {
                        key: value
                        for data in raw_unsubscribed_data
                        if data.get('release_type', "") == release_type
                        for key, value in data.items()
                    }
                count = entry.get('count', 0) + raw_details.get("count", 0)
                if release_type == "Manual":
                    manual_sent = result_data.get('manual_releases', {}).get("sent")
                    result_data['manual_releases'].update({
                        'unsubscribe': count,
                        "unsubscribe_percentage": round((count/manual_sent) * 100, 2)
                        if manual_sent != 0 else 0

                    })
                elif release_type == "Automated":
                    automated_sent = result_data.get('automated_releases', {}).get("sent", 0)
                    result_data['automated_releases'].update({
                        'unsubscribe': count,
                        "unsubscribe_percentage": round((count/automated_sent) * 100, 2) if automated_sent != 0 else 0

                    })
            for record in results:
                manual = record['manual_releases']
                automated = record['automated_releases']
                record['total_releases'] = {
                    'sent': manual.get('sent', 0) + automated.get('sent', 0),
                    'delivered': manual.get('delivered', 0) + automated.get('delivered', 0),
                    'open': manual.get('open', 0) + automated.get('open', 0),
                    'click': manual.get('click', 0) + automated.get('click', 0),
                    'bounce': manual.get('bounce', 0) + automated.get('bounce', 0),
                    'unsubscribe': manual.get('unsubscribe', 0) + automated.get('unsubscribe', 0),
                }
                total = record["total_releases"]
                total_sent = total.get("sent")
                record["total_releases"].update({
                    "delivery": round(total.get("delivered")/total_sent * 100, 2) if total_sent != 0 else 0,
                    "open_percentage": round(total.get("open") / total_sent * 100, 2) if total_sent != 0 else 0,
                    "click_percentage": round(total.get("click") / total_sent * 100, 2) if total_sent != 0 else 0,
                    "bounce_percentage": round(total.get("bounce") / total_sent * 100, 2) if total_sent != 0 else 0,
                    "unsubscribe_percentage": round(total.get("unsubscribe") / total_sent * 100, 2) if total_sent != 0 else 0
                })
            results = [{"name": type, **data} for type, data in results[0].items()]
            return results
        elif communication_type == "sms":
            results = await self.get_sms_release_details(date_range, counselor_id)
            return results
        else:
            return []

    async def get_sms_release_details(self, date_range: dict, counselor_id:list):
        """
                Retrieves release details for SMS communications within the specified date range.

                Args:
                    date_range (dict): A dictionary specifying the start and end dates for filtering the SMS data.
                                       Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
                    counselor_id (list) : list of counselor_ids for filtering the data
                Returns:
                    list: A list containing SMS release details, such as the total count of sent SMS,
                          delivered SMS, and other relevant metrics.
                Raises:
                    ValueError: If the `date_range` dictionary is missing required keys or contains invalid values.
                    TypeError: If `date_range` is not a dictionary.
        """
        pipeline = [
            {
                '$match': {
                    'sms_summary': {
                        '$exists': True
                    }
                }
            },
            *(await self.counselor_pipeline(counselor_id)if counselor_id else []),
            {
                '$project': {
                    'manual_releases': {
                        'sent': {
                            '$size': {
                                '$filter': {
                                    'input': '$sms_summary.transaction_id',
                                    'as': 'transaction',
                                    'cond': {
                                        "$and": [
                                            {'$eq': [
                                                {
                                                    '$ifNull': [
                                                        '$$transaction.release_type', 'Manual'
                                                    ]
                                                }, 'Manual'
                                            ]
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        'delivered': {
                            '$size': {
                                '$filter': {
                                    'input': '$sms_summary.transaction_id',
                                    'as': 'transaction',
                                    'cond': {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$ifNull': [
                                                            '$$transaction.release_type', 'Manual'
                                                        ]
                                                    }, 'Manual'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$$transaction.sms_delivered', True
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        'not_delivered': {
                            '$size': {
                                '$filter': {
                                    'input': '$sms_summary.transaction_id',
                                    'as': 'transaction',
                                    'cond': {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$ifNull': [
                                                            '$$transaction.release_type', 'Manual'
                                                        ]
                                                    }, 'Manual'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$$transaction.state', "SUBMIT_ACCEPTED"
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'automated_releases': {
                        'sent': {
                            '$size': {
                                '$filter': {
                                    'input': '$sms_summary.transaction_id',
                                    'as': 'transaction',
                                    'cond': {
                                        "$and": [
                                            {
                                                '$eq': [
                                                    {
                                                        '$ifNull': [
                                                            '$$transaction.release_type', 'Manual'
                                                        ]
                                                    }, 'Automation'
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        'delivered': {
                            '$size': {
                                '$filter': {
                                    'input': '$sms_summary.transaction_id',
                                    'as': 'transaction',
                                    'cond': {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$ifNull': [
                                                            '$$transaction.release_type', 'Manual'
                                                        ]
                                                    }, 'Automation'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$$transaction.sms_delivered', True
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        'not_delivered': {
                            '$size': {
                                '$filter': {
                                    'input': '$sms_summary.transaction_id',
                                    'as': 'transaction',
                                    'cond': {
                                        '$and': [
                                            {
                                                 '$eq': [
                                                    {
                                                        '$ifNull': [
                                                            '$$transaction.release_type', 'Manual'
                                                        ]
                                                    }, 'Automation'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$$transaction.state', "SUBMIT_ACCEPTED"
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'manual_releases_sent': {
                        '$sum': '$manual_releases.sent'
                    },
                    'manual_releases_delivered': {
                        '$sum': '$manual_releases.delivered'
                    },
                    'manual_releases_not_delivered': {
                        '$sum': '$manual_releases.not_delivered'
                    },
                    'automated_releases_sent': {
                        '$sum': '$automated_releases.sent'
                    },
                    'automated_releases_delivered': {
                        '$sum': '$automated_releases.delivered'
                    },
                    'automated_releases_not_delivered': {
                        '$sum': '$automated_releases.not_delivered'
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'manual_releases': {
                        'sent': '$manual_releases_sent',
                        'delivered': '$manual_releases_delivered',
                        'not_delivered': '$manual_releases_not_delivered',
                    },
                    'automated_releases': {
                        'sent': '$automated_releases_sent',
                        'delivered': '$automated_releases_delivered',
                        'not_delivered': '$automated_releases_not_delivered'
                    }
                }
            }
        ]
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'), date_range.get('end_date'))
            date_filter = [
                {
                    "$gte": [
                        "$$transaction.created_at",
                        start_date
                    ]
                },
                {
                    "$lte": [
                        "$$transaction.created_at",
                        end_date
                    ]
                }
            ]
            for field in ["sent", "delivered", "not_delivered"]:
                x = 4 if counselor_id else 1
                (pipeline[x].get("$project", {}).get("manual_releases", {}).get(f"{field}", {}).get("$size", {}).
                 get("$filter", {}).get("cond", {}).get("$and").extend(date_filter))
                (pipeline[x].get("$project", {}).get("automated_releases", {}).get(f"{field}", {}).get("$size", {}).
                 get("$filter", {}).get("cond", {}).get("$and").extend(date_filter))
        results = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        for record in results:
            manual = record['manual_releases']
            automated = record['automated_releases']
            record['total_releases'] = {
                'sent': manual.get('sent', 0) + automated.get('sent', 0),
                'delivered': manual.get('delivered', 0) + automated.get('delivered', 0),
                'not_delivered': manual.get('not_delivered', 0) + automated.get("not_delivered", 0)
            }
        results = [{"name": type, **data} for type, data in results[0].items()]
        return results

    async def get_profile_wise_details(self, date_range: dict, communication_type: str,
                                       sort: str | None, sort_type: str | None, counselor_id: list | None):
        """
            Retrieves communication details grouped by profile within the specified date range.
            Supports filtering by communication type and optional sorting.

            Params:
                date_range (dict): A dictionary specifying the start and end dates to filter the data.
                                   Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
                communication_type (str): The type of communication to analyze.
                                          Example: "email", "sms", or "whatsap-".
                sort (str | None): The field to sort the results by. Can be `None` if sorting is not required.
                                   Example: "sent", "opened", "failed".
                sort_type (str | None): The sorting order, either "asc" (ascending) or "desc" (descending).
                                        Defaults to `None`.
                counselor_id (list | None): list of counselor ids for filtering data

            Returns:
                list: A list of dictionaries containing communication details grouped by profile.
                      Each dictionary includes metrics such as sent, opened, failed counts, etc.
            Raises:
                ValueError: If `date_range` is missing required keys or contains invalid values.
                TypeError: If inputs are not of the expected types.
        """
        if communication_type == "email":
            results, total = await self.email_details_pipeline(field="user", date_range=date_range,
                                                               sort=sort, sort_type=sort_type,
                                                               counselor_id=counselor_id)
            results.append(
                {
                    "user_name": "Total",
                    "data_id": "None",
                    "email_id": "None",
                    "profile_name": "None",
                    **total
                })
            return results
        elif communication_type == "sms":
            return await self.get_sms_profile_wise_details(date_range, sort, sort_type, counselor_id)
        else:
            pass

    async def get_sms_profile_wise_details(self, date_range: dict, sort: str | None,
                                           sort_type: str | None, counselor_id: list | None) -> list:
        """
        Retrieves SMS details categorized by profile within the specified date range.
        Supports optional sorting of the results.

        Args:
            date_range (dict): A dictionary containing the start and end dates to filter SMS data.
                               Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            sort (str | None): The field to sort the results by. Can be `None` if sorting is not required.
                               Example: "sent".
            sort_type (str | None): The sorting order, either "asc" (ascending) or "dsc" (descending).
                                    Defaults to `None`.
            counselor_id (list | None): List of counselor ids to filter data
        Returns:
            list: A list of dictionaries containing SMS details grouped by profile.
                  Each dictionary includes relevant metrics like sent, failed counts, etc.

        Raises:
            ValueError: If `date_range` is missing required keys or contains invalid values.
            TypeError: If inputs are not of the expected types.
        """
        results, total = await self.sms_details_pipeline(field="user", date_range=date_range,
                                                         sort=sort, sort_type=sort_type,
                                                         counselor_id=counselor_id)
        results.append(
            {
                "user_name": "Total",
                "user_id": "None",
                "email_id": "None",
                "profile_name": "None",
                **total
            })
        return results

    async def list_student_ids(self, counselor_id: list) -> list:
        """
        Get the list of student ids based on associated counselors.

        Params:
            counselor_id (list): List of counselor ids.

        Returns:
            - list: List of student ids based on associated counselors.
        """
        students = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {
                    "$match": {
                        "allocate_to_counselor.counselor_id": {"$in": counselor_id}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "student_ids": {"$push": "$_id"}
                    }
                },
                {
                    "$project": {
                        "_id": 0
                    }
                }
            ]
        ).to_list(None)
        return students[0].get("student_ids") if students else []

    async def sms_details_pipeline(self, field: str, date_range: dict, sort: str,
                                   sort_type: str, data_type: list | None = None,
                                   segment_type: str | None = None, release_type: str | None =None,
                                   user_id: str | None = None,
                                   offline_data_id: str | None = None, data_segment_id: str | None = None,
                                   counselor_id: list |None =None) -> tuple:
        """
        Processes and retrieves sms details based on specified filters, sorting, and segmenting criteria.
        The data is organized using a pipeline approach.

        Args:
            field (str): The field to group or filter the data on.
                         Example: "user", "datasegment".
            date_range (dict): A dictionary specifying the start and end dates for filtering data.
                               Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            sort (str): The field by which to sort the data.
                        Example: "sent", "opened", "failed".
            sort_type (str): The sorting order. Either "asc" for ascending or "desc" for descending order.
                             Example: "asc" or "dsc".
            data_type (list | None): Optional filter for the type of data to process.
                                    Example: "application" or "raw". Defaults to `None`.
            segment_type (str | None): Optional filter for segmenting the data.
                                       Example: "static", "dynamic". Defaults to `None`.
            release_type (str | None): Optional. Specifies the type of release to filter the data.
                                   Example: "Manual", "Automatic".
            user_id (str | None): Optional. Filters the data by the specific user's identifier.
            offline_data_id (str | None): Optional. Filters the data by a specific offline data identifier.
            data_segment_id (str | None): Optional. Filters the data by a specific data segment identifier.
            counselor_id (list | None): List of counselor id to filter data
        Returns:
            tuple: A tuple containing:
                - list of results (list): The processed email details data.
                - total (dict): The total of email records that match the given filters.

        Raises:
            ValueError: If `date_range` is missing required keys or contains invalid values.
            TypeError: If inputs are not of the expected types.
        """
        if field == "user":
            group = {
                'user_id': {
                    '$ifNull': [
                        '$sms_summary.transaction_id.user.id', 'None'
                    ]
                },
                'user_name': {
                    '$ifNull': [
                        '$sms_summary.transaction_id.user.name', 'None'
                    ]
                },
                'email_id': {
                    '$ifNull': [
                        '$sms_summary.transaction_id.user.user_name', 'None'
                    ]
                },
                'profile_name': {
                    '$ifNull': [
                        '$sms_summary.transaction_id.user.role', 'None'
                    ]
                }
            }
            project = {'user_id': {
                        '$toString': '$_id.user_id'
                    },
                    'user_name': '$_id.user_name',
                    'email_id': '$_id.email_id',
                    'profile_name': '$_id.profile_name'}
        elif field == "datasegment":
            group = \
                {
                    'datasegment_id': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.data_segment._id', 'None'
                        ]
                    },
                    'datasegment_name': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.data_segment.name', 'None'
                        ]
                    },
                    'data_type': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.data_segment.data_type', 'None'
                        ]
                    },
                    'segment_type': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.data_segment.segment_type', 'None'
                        ]
                    }
                }
            project = {
                'datasegment_id': {
                    '$toString': '$_id.datasegment_id'
                },
                'datasegment_name': '$_id.datasegment_name',
                'data_type': '$_id.data_type',
                'segment_type': '$_id.segment_type'
            }
        elif field == "offline_data":
            group = \
                {
                    'offline_data_id': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.offline_data._id', 'None'
                        ]
                    },
                    'offline_data_name': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.offline_data.name', 'None'
                        ]
                    }
                }
            project = {
                'offline_data_id': {
                    '$toString': '$_id.offline_data_id'
                },
                'offline_data_name': '$_id.offline_data_name'
            }
        elif field == "template":
            group = \
                {
                    'template_id': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.template_id', 'None'
                        ]
                    },
                    'template_name': {
                        '$ifNull': [
                            '$sms_summary.transaction_id.template_name', 'None'
                        ]
                    }
                }
            project = {
                'template_id': {
                    '$toString': '$_id.template_id'
                },
                'template_name': '$_id.template_name'
            }
        student_ids = None
        if counselor_id:
            student_ids = await self.list_student_ids(counselor_id)
        pipeline = [
            {
                '$match': {
                    'sms_summary': {
                        '$exists': True
                    }
                }
            },
            *(
                [
                    {
                        '$match': {
                            'student_id': {
                                '$in': student_ids
                            }
                        }
                    }
                ]
                if counselor_id else []
            ),
            {
                '$unwind': {
                    'path': '$sms_summary.transaction_id',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$group': {
                    "_id": group,
                    'sent': {
                        '$sum': 1
                    },
                    'delivered': {
                        '$sum': {
                             '$cond': [
                                {
                                    '$eq': [
                                        '$sms_summary.transaction_id.sms_delivered', True
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'not_delivered': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$ne': [
                                        '$sms_summary.transaction_id.status', "SUBMIT_ACCEPTED"
                                    ]
                                }, 1, 0
                            ]
                        }
                    }
                }
            }, {
                '$addFields': {
                    'delivery': {
                        '$cond': {
                            'if': {
                                '$ne': [
                                    '$sent', 0
                                ]
                            },
                            'then': {
                                '$round': [
                                    {
                                        '$multiply': [
                                            {
                                                '$divide': [
                                                    '$delivered', '$sent'
                                                ]
                                            }, 100
                                        ]
                                    }, 2
                                ]
                            },
                            'else': 0
                        }
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    **project,
                    'sent': 1,
                    'delivered': 1,

                    'delivery': 1,
                    "not_delivered": 1
                }
            }
        ]
        match = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'), date_range.get('end_date'))
            date_filter = {
                "$gte": start_date,
                "$lte": end_date
            }
            match.update({
                    "sms_summary.transaction_id.created_at": date_filter
            })
        if sort:
            sort_type = 1 if sort_type == "asc" else -1
            pipeline.append({
                "$sort": {sort: sort_type}
            })
        if data_type:
            match.update({"sms_summary.transaction_id.data_segment.data_type": {"$in": data_type}})
        if segment_type:
            match.update({"sms_summary.transaction_id.data_segment.segment_type": segment_type})
        if release_type:
            match.update({
                "sms_summary.transaction_id.release_type": release_type.title()
            })
        if user_id:
            match.update({
                "sms_summary.transaction_id.user.id": ObjectId(user_id)
                if ObjectId.is_valid(user_id) else str(user_id)
            })
        if data_segment_id:
            match.update({
                "sms_summary.transaction_id.data_segment._id": ObjectId(data_segment_id)
                if ObjectId.is_valid(data_segment_id) else str(data_segment_id)
            })
        if offline_data_id:
            match.update({
                "sms_summary.transaction_id.offline_data._id": ObjectId(offline_data_id)
                if ObjectId.is_valid(offline_data_id) else str(offline_data_id)
            })
        if match:
            x = 3 if counselor_id else 2
            pipeline.insert(x, {"$match": match})
        results = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        total = {
            'sent': 0,
            'delivered': 0,
            'delivery': 0,
            "not_delivered": 0
        }
        for res in results:
            total.update({
                'sent': total.get('sent', 0) + res.get("sent", 0),
                'delivered': total.get('delivered', 0) + res.get('delivered', 0),
                'not_delivered': total.get('not_delivered', 0) + res.get('not_delivered', 0)
            })
        total_sent = total.get("sent")
        total.update({
            "delivery": round(total.get("delivered") / total_sent * 100, 2) if total_sent else 0
        })
        return results, total


    async def email_details_pipeline(self, field: str, date_range: dict, sort: str,
                                     sort_type: str, data_type: list | None = None,
                                     segment_type: str | None = None,
                                     release_type: str | None = None,
                                     user_id: str | None = None,
                                     offline_data_id: str | None = None,
                                     data_segment_id: str | None = None,
                                     counselor_id : list | None = None) -> tuple:
        """
        Processes and retrieves email details based on specified filters, sorting, and segmenting criteria.
        The data is organized using a pipeline approach.

        Args:
            field (str): The field to group or filter the data on.
                         Example: "user", "datasegment".
            date_range (dict): A dictionary specifying the start and end dates for filtering data.
                               Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            sort (str): The field by which to sort the data.
                        Example: "sent", "opened", "failed".
            sort_type (str): The sorting order. Either "asc" for ascending or "desc" for descending order.
                             Example: "asc" or "dsc".
            data_type (str | None): Optional filter for the type of data to process.
                                    Example: "application" or "raw". Defaults to `None`.
            segment_type (str | None): Optional filter for segmenting the data.
                                       Example: "static", "dynamic". Defaults to `None`.
            release_type (str | None): Optional. Specifies the type of release to filter the data.
                                   Example: "Manual", "Automatic".
            user_id (str | None): Optional. Filters the data by the specific user's identifier.
            offline_data_id (str | None): Optional. Filters the data by a specific offline data identifier.
            data_segment_id (str | None): Optional. Filters the data by a specific data segment identifier.
            counselor_id (list | None): List of counselor ids to filter data
        Returns:
            tuple: A tuple containing:
                - list of results (list): The processed email details data.
                - total (dict): The total of email records that match the given filters.

        Raises:
            ValueError: If `date_range` is missing required keys or contains invalid values.
            TypeError: If inputs are not of the expected types.
        """
        if field == "user":
            group = \
                {
                    'user_id': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.user.id', None]},
                                    {"$eq": ['$email_summary.transaction_id.user.id', ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else": '$email_summary.transaction_id.user.id'
                        }
                    },
                    'user_name': {
                          "$cond": {
                            "if": {
                              "$or": [
                                {"$eq": ["$email_summary.transaction_id.user.name", None]},
                                {"$eq": ["$email_summary.transaction_id.user.name", ""]}
                              ]
                            },
                            "then": "Transactional",
                            "else": "$email_summary.transaction_id.user.name"
                          }
                    },
                    'email_id': {
                        '$ifNull': [
                            '$email_summary.transaction_id.user.user_name', 'None'
                        ]
                    },
                    'profile_name': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.user.role', None]},
                                    {"$eq": ['$email_summary.transaction_id.user.role', ""]}
                                ]
                            },
                            "then": "None",
                            "else": '$email_summary.transaction_id.user.role'
                        }
                    }
                }
            project = {
                'data_id': {
                        '$toString': '$_id.user_id'
                    },
                'user_name': '$_id.user_name',
                'email_id': '$_id.email_id',
                'profile_name': '$_id.profile_name'
            }
            unsubscribe_field = "user_id"
        elif field == "datasegment":
            unsubscribe_field = "datasegment_id"
            group = \
                {
                    'datasegment_id': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.data_segment._id', None]},
                                    {"$eq": ['$email_summary.transaction_id.data_segment._id', ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else": '$email_summary.transaction_id.data_segment._id'
                        }
                    },
                    'datasegment_name': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.data_segment.name', None]},
                                    {"$eq": ['$email_summary.transaction_id.data_segment.name', ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else": '$email_summary.transaction_id.data_segment.name'
                        }
                    },
                    'data_type': {
                        '$ifNull': [
                            '$email_summary.transaction_id.data_segment.data_type', 'None'
                        ]
                    },
                    'segment_type': {
                        '$ifNull': [
                            '$email_summary.transaction_id.data_segment.segment_type', 'None'
                        ]
                    }
                }
            project = {
                'data_id': {
                    '$toString': {
                        '$ifNull': ['$_id.datasegment_id', "Transactional"]
                    }
                },
                'datasegment_name': {
                    '$ifNull': ['$_id.datasegment_name', "Transactional"]
                },
                'data_type': {
                    '$ifNull': ['$_id.data_type', None]
                },
                'segment_type': {
                    '$ifNull': ['$_id.segment_type', None]
                }
            }
        elif field == "offline_data":
            unsubscribe_field = "offline_data_id"
            group = \
                {
                    'offline_data_id': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.offline_data._id', None]},
                                    {"$eq": ['$email_summary.transaction_id.offline_data._id', ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else": '$email_summary.transaction_id.offline_data._id'
                        }
                    },
                    'offline_data_name': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.offline_data.name', None]},
                                    {"$eq": ['$email_summary.transaction_id.offline_data.name', ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else": '$email_summary.transaction_id.offline_data.name'
                        }
                    },
                }
            project = {
                'data_id': {
                    '$toString': {
                        '$ifNull': ['$_id.offline_data_id', "Transactional"]
                    }
                },
                'offline_data_name': {
                    '$ifNull': ['$_id.offline_data_name', "Transactional"]
                }
            }
        elif field == "template":
            unsubscribe_field = "template_id"
            group = \
                {
                    'template_id': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.template_id', None]},
                                    {"$eq": ['$email_summary.transaction_id.template_id', ""]},
                                    {"$eq": ['$email_summary.transaction_id.template_id', "None"]}
                                ]
                            },
                            "then": "Transactional",
                            "else": '$email_summary.transaction_id.template_id'
                        }
                    },
                    'template_name': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": ['$email_summary.transaction_id.template_name', None]},
                                    {"$eq": ['$email_summary.transaction_id.template_name', ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else": '$email_summary.transaction_id.template_name'
                        }
                    },
                }
            project = {
                'data_id': {
                    '$toString': '$_id.template_id'
                },
                'template_name': '$_id.template_name'
            }

        student_ids = None
        if counselor_id:
            student_ids = await self.list_student_ids(counselor_id)
        pipeline = [
            {
                '$match': {
                    'email_summary': {
                        '$exists': True
                    }
                }
            },
            *(
                [
                    {
                        '$match': {
                            'student_id': {
                                '$in': student_ids
                            }
                        }
                    }
                ]
                if counselor_id else []
            ),
            {
                '$unwind': {
                    'path': '$email_summary.transaction_id',
                    'preserveNullAndEmptyArrays': True
                }
            },

            {
                '$group': {
                    '_id': group,
                    'sent': {
                        '$sum': 1
                    },
                    'delivered': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$email_summary.transaction_id.email_delivered', True
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'open': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$email_summary.transaction_id.email_open', True
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'click': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$email_summary.transaction_id.email_click', True
                                    ]
                                }, 1, 0
                            ]
                        }
                    },
                    'bounce': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$eq': [
                                        '$email_summary.transaction_id.email_bounce', True
                                    ]
                                }, 1, 0
                            ]
                        }
                    }
                }
            }, {
                '$addFields': {
                    'delivery': {
                        '$cond': {
                            'if': {
                                '$ne': [
                                    '$sent', 0
                                ]
                            },
                            'then': {
                                '$round': [
                                    {
                                        '$multiply': [
                                            {
                                                '$divide': [
                                                    '$delivered', '$sent'
                                                ]
                                            }, 100
                                        ]
                                    }, 2
                                ]
                            },
                            'else': 0
                        }
                    },
                    'open_percentage': {
                        '$cond': {
                            'if': {
                                '$ne': [
                                    '$sent', 0
                                ]
                            },
                            'then': {
                                '$round': [
                                    {
                                        '$multiply': [
                                            {
                                                '$divide': [
                                                    '$open', '$sent'
                                                ]
                                            }, 100
                                        ]
                                    }, 2
                                ]
                            },
                            'else': 0
                        }
                    },
                    'click_percentage': {
                        '$cond': {
                            'if': {
                                '$ne': [
                                    '$sent', 0
                                ]
                            },
                            'then': {
                                '$round': [
                                    {
                                        '$multiply': [
                                            {
                                                '$divide': [
                                                    '$click', '$sent'
                                                ]
                                            }, 100
                                        ]
                                    }, 2
                                ]
                            },
                            'else': 0
                        }
                    },
                    'bounce_percentage': {
                        '$cond': {
                            'if': {
                                '$ne': [
                                    '$sent', 0
                                ]
                            },
                            'then': {
                                '$round': [
                                    {
                                        '$multiply': [
                                            {
                                                '$divide': [
                                                    '$bounce', '$sent'
                                                ]
                                            }, 100
                                        ]
                                    }, 2
                                ]
                            },
                            'else': 0
                        }
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    **project,
                    'sent': 1,
                    'delivered': 1,
                    'delivery': 1,
                    'open': 1,
                    'open_percentage': 1,
                    'click': 1,
                    'click_percentage': 1,
                    'bounce': 1,
                    'bounce_percentage': 1
                }
            }
        ]
        unsubscribe_pipeline = [
            {
                '$match': {
                    'unsubscribe.value': True
                }
            },
            *(
                [{
                    '$match': {
                        'allocate_to_counselor.counselor_id': {
                            '$in': counselor_id
                        }
                    }
                }]
                if counselor_id else []
            ),
            {
                '$group': {
                    '_id': {
                        '$ifNull': [
                            f'$unsubscribe.{unsubscribe_field}', 'None'
                        ]
                    },
                    'unsubscribe': {
                        '$sum': 1
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'data_id': {
                        '$toString': '$_id'
                    },
                    'unsubscribe': 1
                }
            }
        ]
        match = {}
        unsubscribe_match = {}
        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'), date_range.get('end_date'))
            date_filter = {
                "$gte": start_date,
                "$lte": end_date
            }
            match.update({
                    "email_summary.transaction_id.created_at": date_filter
            })
            unsubscribe_match.update({"unsubscribe.timestamp": date_filter})
            unsubscribe_pipeline[0].get("$match", {}).update({"unsubscribe.timestamp": date_filter})
        if sort:
            sort_type = 1 if sort_type == "asc" else -1
            if sort != "unsubscribe":
                pipeline.append({
                    "$sort": {sort: sort_type}
                })
        if data_type:
            match.update({
                "email_summary.transaction_id.data_segment.data_type": {"$in": data_type}
            })
            unsubscribe_match.update({"unsubscribe.data_segment_data_type": {"$in": data_type}})
        if segment_type:
            match.update({
                "email_summary.transaction_id.data_segment.segment_type": segment_type
            })
            unsubscribe_match.update({"unsubscribe.data_segment_type": segment_type})
        if release_type:
            match.update({
                "email_summary.transaction_id.release_type": release_type.title()
            })
            unsubscribe_match.update({"unsubscribe.release_type": release_type})
        if user_id:
            if user_id in ["None", "Transactional", "Automation"]:
                user_id = "" if user_id in ["None", "Transactional"] else user_id
                match.update({
                    "$or": [
                        {"email_summary.transaction_id.user.id": user_id},
                        {"email_summary.transaction_id.user.id": {"$exists": False}}
                    ]
                })
                unsubscribe_match.update(
                    {
                        "$or": [{"unsubscribe.user_id": user_id}, {"unsubscribe.user_id": {"$exists": False}}]
                    }
                )

            else:
                match.update({
                    "email_summary.transaction_id.user.id": ObjectId(user_id)
                    if ObjectId.is_valid(user_id) else str(user_id)
                })
                unsubscribe_match.update({"unsubscribe.user_id": ObjectId(user_id)
                if ObjectId.is_valid(user_id) else str(user_id)})
        if data_segment_id:
            if data_segment_id in ["None", "Transactional", "Automation"]:
                data_segment_id = "" if data_segment_id in ["None", "Transactional"] else data_segment_id
                match.update({
                    "$or": [
                        {"email_summary.transaction_id.data_segment._id": data_segment_id},
                        {"email_summary.transaction_id.data_segment._id": {"$exists": False}}
                    ]
                })
                unsubscribe_match.update(
                    {
                        "$or": [{"unsubscribe.datasegment_id": data_segment_id}, {"unsubscribe.datasegment_id": {"$exists": False}}]
                    }
                )
            else:
                match.update({
                    "email_summary.transaction_id.data_segment._id": ObjectId(data_segment_id)
                    if ObjectId.is_valid(data_segment_id) else str(data_segment_id)
                })
                unsubscribe_match.update({"unsubscribe.datasegment_id": ObjectId(data_segment_id)
                    if ObjectId.is_valid(data_segment_id) else str(data_segment_id)})
        if offline_data_id:
            if offline_data_id in ["None", "Transactional", "Automation"]:
                offline_data_id = "" if offline_data_id in ["None", "Transactional"] else offline_data_id
                match.update({
                    "$or": [
                        {"email_summary.transaction_id.offline_data._id": offline_data_id},
                        {"email_summary.transaction_id.offline_data._id": {"$exists": False}}
                    ]
                })
                unsubscribe_match.update(
                    {
                        "$or": [{"unsubscribe.offline_data_id": offline_data_id}, {"unsubscribe.offline_data_id": {"$exists": False}}]
                    }
                )
            else:
                match.update({
                    "email_summary.transaction_id.offline_data._id": ObjectId(offline_data_id)
                    if ObjectId.is_valid(offline_data_id) else str(offline_data_id)
                })
                unsubscribe_match.update({"unsubscribe.offline_data_id": ObjectId(offline_data_id)
                if ObjectId.is_valid(offline_data_id) else str(offline_data_id)})
        if match:
            x = 3 if counselor_id else 2
            pipeline.insert(x, {"$match": match})
            unsubscribe_pipeline.insert(x, {"$match": unsubscribe_match})

        results = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        unsubscribe_results = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(
                unsubscribe_pipeline).to_list(None)
        raw_data_unsubscribe_results = await DatabaseConfiguration().raw_data.aggregate(
                unsubscribe_pipeline).to_list(None)
        unsubscribe_results = {data.get("data_id"): data for data in unsubscribe_results}
        raw_data_unsubscribe_results = {data.get("data_id"): data for data in raw_data_unsubscribe_results}
        total = {
            'sent': 0,
            'delivered': 0,
            'open': 0,
            'click': 0,
            'bounce': 0,
            'unsubscribe': 0,
        }
        for res in results:
            unsubscribe_detail = unsubscribe_results.get(res.get("data_id"), {})
            raw_unsubscribe_detail = raw_data_unsubscribe_results.get(res.get("data_id"), {})
            sent_count = res.get("sent", 0)
            if unsubscribe_detail or raw_unsubscribe_detail:
                unsubscribe_count = unsubscribe_detail.get("unsubscribe", 0) + raw_unsubscribe_detail.get("unsubscribe", 0)
                res.update({
                    "unsubscribe": unsubscribe_count,
                    "unsubscribe_percentage": round(unsubscribe_count / sent_count * 100, 2) if sent_count != 0 else 0
                })
            else:
                res.update({
                    "unsubscribe": 0,
                    "unsubscribe_percentage": 0
                })
            total.update({
                'sent': total.get('sent', 0) + sent_count,
                'delivered': total.get('delivered', 0) + res.get('delivered', 0),
                'open': total.get('open', 0) + res.get('open', 0),
                'click': total.get('click', 0) + res.get('click', 0),
                'bounce': total.get('bounce', 0) + res.get('bounce', 0),
                'unsubscribe': total.get('unsubscribe', 0) + res.get('unsubscribe', 0),
            })
        total_sent = total.get("sent")
        total.update({
            "delivery": round(total.get("delivered") / total_sent * 100, 2) if total_sent else 0,
            "open_percentage": round(total.get("open") / total_sent * 100, 2) if total_sent else 0,
            "click_percentage": round(total.get("click") / total_sent * 100, 2) if total_sent else 0,
            "bounce_percentage": round(total.get("bounce") / total_sent * 100, 2) if total_sent else 0,
            "unsubscribe_percentage": round(total.get("unsubscribe") / total_sent * 100, 2) if total_sent else 0
        })
        if sort and sort == "unsubscribe":
            results = (
                sorted(results, key=lambda x: x[sort], reverse=True)
                if sort_type != 1
                else sorted(results, key=lambda x: x[sort])
            )
        return results, total

    async def get_data_segment_wise_details(self, date_range: dict, communication_type: str, sort: str | None,
                                            sort_type: str | None, data_type: list | None, segment_type: str| None,
                                            counselor_id: list | None):
        """
            Retrieves segment-wise data details for a specific communication type within the specified date range.
            Supports sorting and filtering by data type and segment type.

            Params:
                date_range (dict): A dictionary specifying the start and end dates to filter the data.
                                   Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
                communication_type (str): The type of communication to analyze.
                                          Example: "email", "sms", or "whatsapp".
                sort (str | None): The field to sort the data by. Can be `None` if no sorting is required.
                                   Example: "sent", e.t.c;
                sort_type (str | None): The sorting direction, either "asc" (ascending) or "dsc" (descending).
                                        Example: "asc" or "dsc". Defaults to `None`.
                data_type (list | None): An optional parameter to filter the data by type.
                                        Example: "raw" or "application".
                segment_type (str | None): An optional parameter to filter data by specific segments.
                                           Example: "static", "dynamic"
                counselor_id (list | None): list of counselor ids for filter
            Returns:
                list: A list containing segment-wise data details based on the specified filters and sort order.

            Raises:
                ValueError: If `date_range` is missing required keys or contains invalid values.
                TypeError: If input parameters are not of the expected types.
        """
        if communication_type == "email":
            results, total = await self.email_details_pipeline(field="datasegment", date_range=date_range,
                                                               sort=sort, sort_type=sort_type, data_type=data_type,
                                                               segment_type=segment_type,
                                                               counselor_id=counselor_id)
            results.append(
                {
                    "datasegment_name": "Total",
                    "data_id": "None",
                    "data_type": "None",
                    "segment_type": "None",
                    **total
                }
            )
            return results
        elif communication_type == "sms":
            results, total = await self.sms_details_pipeline(field="datasegment", date_range=date_range,
                                                             sort=sort, sort_type=sort_type, data_type=data_type,
                                                             segment_type=segment_type,
                                                             counselor_id=counselor_id)
            results.append(
                {
                    "datasegment_name": "Total",
                    "datasegment_id": "None",
                    "data_type": "None",
                    "segment_type": "None",
                    **total
                }
            )
            return results
        else:
            pass

    async def get_offline_data_details(self, date_range: dict, communication_type: str, sort: str | None,
                                            sort_type: str | None, counselor_id: list | None):
        """
        Retrieves offline communication data details within the specified date range.
        Supports filtering by communication type and optional sorting.

        Params:
            date_range (dict): Specifies the start and end dates for filtering the offline data.
                               Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            communication_type (str): The type of communication to analyze.
                                      Example: "email", "SMS", or "notification".
            sort (str | None): Optional. The field to sort the results by.
                               Example: "processed", "failed", "pending".
            sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                    Defaults to `None`.
            counselor_id (list | None) : List of counselor ids to filter data

        Returns:
            list: A list of dictionaries containing offline communication metrics grouped by category.
                  Each dictionary includes metrics such as processed, failed, and pending counts.

        Raises:
            ValueError: If `date_range` is missing required keys or contains invalid values.
            TypeError: If inputs are not of the expected types.
        """
        if communication_type == "email":
            results, total = await self.email_details_pipeline(field="offline_data", date_range=date_range,
                                                               sort=sort, sort_type=sort_type, counselor_id=counselor_id)
            results.append(
                {
                    "offline_data_name": "Total",
                    "data_id": "None",
                    **total
                }
            )
            return results
        elif communication_type == "sms":
            results, total = await self.sms_details_pipeline(field="offline_data", date_range=date_range,
                                                             sort=sort, sort_type=sort_type, counselor_id=counselor_id)
            results.append(
                {
                    "offline_data_name": "Total",
                    "offline_data_id": "None",
                    **total
                }
            )
            return results
        else:
            pass

    async def get_template_wise_details(self, date_range: dict, communication_type: str, sort: str | None,
                                        sort_type: str | None, release_type: str | None,
                                        user_id: str | None, offline_data_id: str | None, data_segment_id: str | None,
                                        counselor_id: list | None):
        """
        Retrieves communication details grouped by templates within the specified date range.
        Supports filtering by communication type and optional sorting.

        Params::
            date_range (dict): Specifies the start and end dates for filtering the data.
                               Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            communication_type (str): The type of communication to analyze.
                                      Example: "email", "SMS", or "notification".
            sort (str | None): Optional. The field to sort the results by.
                               Example: "sent", "opened", "failed".
            sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                    Defaults to `None`.
            release_type (str | None): Optional. Specifies the type of release to filter the data.
                                   Example: "Manual", "Automatic".
            user_id (str | None): Optional. Filters the data by the specific user's identifier.
            offline_data_id (str | None): Optional. Filters the data by a specific offline data identifier.
            data_segment_id (str | None): Optional. Filters the data by a specific data segment identifier.
            counselor_id (list | None) : list of counselor ids for filter data

        Returns:
            list: A list of dictionaries containing communication metrics grouped by template.
                  Each dictionary includes metrics such as sent, opened, and failed counts.
                  Example:

        Raises:
            ValueError: If `date_range` is missing required keys or contains invalid values.
            TypeError: If inputs are not of the expected types.
        """
        if communication_type == "email":
            results, total = await self.email_details_pipeline(field="template", date_range=date_range,
                                                               sort=sort, sort_type=sort_type,
                                                               release_type=release_type, user_id=user_id,
                                                               offline_data_id=offline_data_id,
                                                               data_segment_id=data_segment_id,
                                                               counselor_id=counselor_id)
            results.append(
                {
                    "template_name": "Total",
                    "data_id": "None",
                    **total
                }
            )
            return results
        elif communication_type == "sms":
            results, total = await self.sms_details_pipeline(field="template", date_range=date_range,
                                                             sort=sort, sort_type=sort_type,
                                                             release_type=release_type, user_id=user_id,
                                                             offline_data_id=offline_data_id,
                                                             data_segment_id=data_segment_id,
                                                             counselor_id=counselor_id)
            results.append(
                {
                    "template_name": "Total",
                    "template_id": "None",
                    **total
                }
            )
            return results
        else:
            pass

    async def get_date_wise_details(self, date_range: dict, dates: list, communication_type: str, sort: str | None,
                                    sort_type: str | None, counselor_id: list | None):
        """
        Retrieves communication details categorized by dates within the specified date range or custom date list.
        Supports filtering by communication type and optional sorting.

        Params:
            date_range (dict): Specifies the start and end dates for filtering the data.
                               Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            dates (list): A list of specific dates to include in the results.
                          Overrides `date_range` if provided.
                          Example: ["2024-01-01", "2024-01-15", "2024-01-31"].
            communication_type (str): The type of communication to analyze.
                                      Example: "email", "SMS", or "notification".
            sort (str | None): Optional. The field to sort the results by.
                               Example: "sent", "failed", "opened".
            sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                    Defaults to `None`.
            counselor_id (list | None): list of counselor id for filter

        Returns:
            list: A list of dictionaries containing communication details grouped by date.

        Raises:
            ValueError: If both `date_range` and `dates` are missing or invalid.
            TypeError: If inputs are not of the expected types.
        """
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=7)
        end_date = end_date.strftime("%Y-%m-%d")
        start_date = start_date.strftime("%Y-%m-%d")
        if date_range:
            start_date, end_date = date_range.get('start_date'), date_range.get('end_date')
        start_date, end_date = await utility_obj.date_change_format(
            start_date, end_date)
        number_of_days = int((end_date - start_date).days) + 1
        if communication_type == "email":
            pipeline = [
                {
                    '$match': {
                        'email_summary.transaction_id.created_at': {
                            '$gte': start_date,
                            '$lt': end_date
                        }
                    }
                },
                *(await self.counselor_pipeline(counselor_id)if counselor_id else []),
                {
                    '$project': {
                        'email_summary.transaction_id': 1
                    }
                }, {
                    '$unwind': {
                        'path': '$email_summary.transaction_id',
                        'preserveNullAndEmptyArrays': True
                    }
                },
                {
                    '$match': {
                        'email_summary.transaction_id.created_at': {
                            '$gte': start_date,
                            '$lt': end_date
                        }
                    }
                },
                {
                    '$project': {
                        'date': {
                            '$dateToString': {
                                'format': "%Y-%m-%d",
                                'date': '$email_summary.transaction_id.created_at'
                            }
                        },
                        'email_sent': {
                            '$cond': {
                                'if': {
                                    '$gt': [
                                        '$email_summary.transaction_id', None
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        },
                        'email_delivered': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                f'$email_summary.transaction_id.email_delivered', True
                                            ]
                                        }
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        },
                        'email_open': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                f'$email_summary.transaction_id.email_open', True
                                            ]
                                        }
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        },
                        'email_click': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                f'$email_summary.transaction_id.email_click', True
                                            ]
                                        }
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        },
                        'email_bounce': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                f'$email_summary.transaction_id.email_bounce', True
                                            ]
                                        }
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        }
                    }
                }, {
                    '$group': {
                        '_id': '$date',
                        'email_sent': {
                            '$sum': '$email_sent'
                        },
                        'email_delivered': {
                            '$sum': '$email_delivered'
                        },
                        'email_open': {
                            '$sum': '$email_open'
                        },
                        'email_click': {
                            '$sum': '$email_click'
                        },
                        'email_bounce': {
                            '$sum': '$email_bounce'
                        }
                    }
                }, {
                    '$sort': {
                        '_id': 1
                    }
                }, {
                    '$facet': {
                        'data': [
                            {
                                '$project': {
                                    'date': '$_id',
                                    'email_sent': 1,
                                    'email_delivered': 1,
                                    'email_open': 1,
                                    'email_click': 1,
                                    'email_bounce': 1,
                                }
                            }
                        ],
                        'allDates': [
                            {
                                '$project': {
                                    '_id': 0,
                                    'dates': {
                                        '$map': {
                                            'input': {"$range": [1, number_of_days + 1]},
                                            'as': 'day',
                                            'in': {
                                                'date': {
                                                    '$dateToString': {
                                                        'format': "%Y-%m-%d",
                                                        'date': {
                                                            '$add': [
                                                                start_date, {
                                                                    '$multiply': [
                                                                        '$$day', 86400000
                                                                    ]
                                                                }
                                                            ]
                                                        }
                                                    }
                                                },
                                                'email_sent': 0,
                                                'email_delivered': 0,
                                                'email_open': 0,
                                                'email_click': 0,
                                                'email_bounce': 0,
                                            }
                                        }
                                    }
                                }
                            }, {
                                '$unwind': '$dates'
                            }, {
                                '$replaceRoot': {
                                    'newRoot': '$dates'
                                }
                            }
                        ]
                    }
                }, {
                    '$project': {
                        'merged': {
                            '$concatArrays': [
                                '$data', '$allDates'
                            ]
                        }
                    }
                }, {
                    '$unwind': '$merged'
                }, {
                    '$replaceRoot': {
                        'newRoot': '$merged'
                    }
                }, {
                    '$group': {
                        '_id': '$date',
                        'email_sent': {
                            '$max': '$email_sent'
                        },
                        'email_delivered': {
                            '$max': '$email_delivered'
                        },
                        'email_open': {
                            '$max': '$email_open'
                        },
                        'email_click': {
                            '$max': '$email_click'
                        },
                        'email_bounce': {
                            '$max': '$email_bounce'
                        },

                    }
                },
                {
                    '$sort': {
                        '_id': -1
                    },
                },
                {
                    '$addFields': {
                        'email_delivery': {
                            '$cond': {
                                'if': {
                                    '$ne': [
                                        '$email_sent', 0
                                    ]
                                },
                                'then': {
                                    '$round': [
                                        {
                                            '$multiply': [
                                                {
                                                    '$divide': [
                                                        '$email_delivered', '$email_sent'
                                                    ]
                                                }, 100
                                            ]
                                        }, 2
                                    ]
                                },
                                'else': 0
                            }
                        },
                        'open_percentage': {
                            '$cond': {
                                'if': {
                                    '$ne': [
                                        '$email_sent', 0
                                    ]
                                },
                                'then': {
                                    '$round': [
                                        {
                                            '$multiply': [
                                                {
                                                    '$divide': [
                                                        '$email_open', '$email_sent'
                                                    ]
                                                }, 100
                                            ]
                                        }, 2
                                    ]
                                },
                                'else': 0
                            }
                        },
                        'click_percentage': {
                            '$cond': {
                                'if': {
                                    '$ne': [
                                        '$email_sent', 0
                                    ]
                                },
                                'then': {
                                    '$round': [
                                        {
                                            '$multiply': [
                                                {
                                                    '$divide': [
                                                        '$email_click', '$email_sent'
                                                    ]
                                                }, 100
                                            ]
                                        }, 2
                                    ]
                                },
                                'else': 0
                            }
                        },
                        'bounce_percentage': {
                            '$cond': {
                                'if': {
                                    '$ne': [
                                        '$email_sent', 0
                                    ]
                                },
                                'then': {
                                    '$round': [
                                        {
                                            '$multiply': [
                                                {
                                                    '$divide': [
                                                        '$email_bounce', '$email_sent'
                                                    ]
                                                }, 100
                                            ]
                                        }, 2
                                    ]
                                },
                                'else': 0
                            }
                        }
                    }
                }, {
                '$project': {
                    '_id': 1,
                    'email_sent': 1,
                    'email_delivered': 1,
                    'email_delivery': 1,
                    'email_open': 1,
                    'open_percentage': 1,
                    'email_click': 1,
                    'click_percentage': 1,
                    'email_bounce': 1,
                    'bounce_percentage': 1
                }
            }
            ]
            unsubscribe_pipeline = [
                {
                    '$match': {
                        "unsubscribe.value": True,
                        'unsubscribe.timestamp': {
                            '$gte': start_date,
                            '$lt': end_date
                        }
                    }
                },
                *(
                    [{
                        '$match': {
                            'allocate_to_counselor.counselor_id': {
                                '$in': counselor_id
                            }
                        }
                    }]
                    if counselor_id else []
                ),
                {
                    '$project': {
                        'date': {
                            '$dateToString': {
                                'format': "%Y-%m-%d",
                                'date': '$unsubscribe.timestamp'
                            }
                        },
                        'unsubscribe': {
                            '$cond': {
                                'if': {
                                    '$gt': [
                                        '$unsubscribe.value', None
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        }
                    }
                }, {
                    '$group': {
                        '_id': '$date',
                        'unsubscribe': {
                            '$sum': '$unsubscribe'
                        }
                    }
                }, {
                    '$sort': {
                        '_id': 1
                    }
                }, {
                    '$facet': {
                        'data': [
                            {
                                '$project': {
                                    'date': '$_id',
                                    'unsubscribe': 1,
                                }
                            }
                        ],
                        'allDates': [
                            {
                                '$project': {
                                    '_id': 0,
                                    'dates': {
                                        '$map': {
                                            'input': {"$range": [1, number_of_days + 1]},
                                            'as': 'day',
                                            'in': {
                                                'date': {
                                                    '$dateToString': {
                                                        'format': "%Y-%m-%d",
                                                        'date': {
                                                            '$add': [
                                                                start_date, {
                                                                    '$multiply': [
                                                                        '$$day', 86400000
                                                                    ]
                                                                }
                                                            ]
                                                        }
                                                    }
                                                },
                                                'unsubscribe': 0
                                            }
                                        }
                                    }
                                }
                            }, {
                                '$unwind': '$dates'
                            }, {
                                '$replaceRoot': {
                                    'newRoot': '$dates'
                                }
                            }
                        ]
                    }
                }, {
                    '$project': {
                        'merged': {
                            '$concatArrays': [
                                '$data', '$allDates'
                            ]
                        }
                    }
                }, {
                    '$unwind': '$merged'
                }, {
                    '$replaceRoot': {
                        'newRoot': '$merged'
                    }
                }, {
                    '$group': {
                        '_id': '$date',
                        'unsubscribe': {
                            '$max': '$unsubscribe'
                        }
                    }
                },
                {
                    '$sort': {
                        '_id': -1
                    },
                }
            ]
            if dates:
                documents, unsubscribe_documents, unsubscribe_dates, utc_dates = [], [], [], []
                for date in dates:
                    start, end = await utility_obj.date_change_format(date, date)
                    utc_dates.append({
                        "email_summary.transaction_id.created_at": {
                            "$gte": start,
                            "$lt": end
                        }
                    })
                    unsubscribe_dates.append({
                        'unsubscribe.timestamp': {
                            "$gte": start,
                            "$lt": end
                        }
                    })
                    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d %b %Y")
                    documents.append({'_id': formatted_date, 'email_sent': 0, 'email_delivered': 0, 'email_open': 0,
                                     'email_click': 0, 'email_bounce': 0})
                    unsubscribe_documents.append({'_id': formatted_date, 'unsubscribe': 0})
                pipeline = [
                    {
                        '$match': {'$or': utc_dates}
                    },
                    *(await self.counselor_pipeline(counselor_id)if counselor_id else []),
                    {
                        '$project': {
                            'email_summary.transaction_id': 1
                        }
                    }, {
                        '$unwind': {
                            'path': '$email_summary.transaction_id',
                            'preserveNullAndEmptyArrays': True
                        }
                    },
                    {
                        '$match': {'$or': utc_dates}
                    },
                    {
                        '$project': {
                            'date': {
                                '$dateToString': {
                                    'format': "%Y-%m-%d",
                                    'date': '$email_summary.transaction_id.created_at'
                                }
                            },
                            'email_sent': {
                                '$cond': {
                                    'if': {
                                        '$gt': [
                                            '$email_summary.transaction_id', None
                                        ]
                                    },
                                    'then': 1,
                                    'else': 0
                                }
                            },
                            'email_delivered': {
                                '$cond': {
                                    'if': {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    f'$email_summary.transaction_id.email_delivered', True
                                                ]
                                            }
                                        ]
                                    },
                                    'then': 1,
                                    'else': 0
                                }
                            },
                            'email_open': {
                                '$cond': {
                                    'if': {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    f'$email_summary.transaction_id.email_open', True
                                                ]
                                            }
                                        ]
                                    },
                                    'then': 1,
                                    'else': 0
                                }
                            },
                            'email_click': {
                                '$cond': {
                                    'if': {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    f'$email_summary.transaction_id.email_click', True
                                                ]
                                            }
                                        ]
                                    },
                                    'then': 1,
                                    'else': 0
                                }
                            },
                            'email_bounce': {
                                '$cond': {
                                    'if': {
                                        '$and': [
                                            {
                                                '$eq': [
                                                    f'$email_summary.transaction_id.email_bounce', True
                                                ]
                                            }
                                        ]
                                    },
                                    'then': 1,
                                    'else': 0
                                }
                            }
                        }
                    }, {
                        '$group': {
                            '_id': '$date',
                            'email_sent': {
                                '$sum': '$email_sent'
                            },
                            'email_delivered': {
                                '$sum': '$email_delivered'
                            },
                            'email_open': {
                                '$sum': '$email_open'
                            },
                            'email_click': {
                                '$sum': '$email_click'
                            },
                            'email_bounce': {
                                '$sum': '$email_bounce'
                            }
                        }
                    },
                    {
                        '$unionWith': {
                            'pipeline': [
                                {'$documents': documents}
                            ]
                        }
                    },
                    {
                        '$group': {
                            '_id': '$_id',
                            'email_sent': {'$sum': '$email_sent'},
                            'email_delivered': {'$sum': '$email_delivered'},
                            'email_open': {'$sum': '$email_open'},
                            'email_click': {'$sum': '$email_click'},
                            'email_bounce': {'$sum': '$email_bounce'}
                        }
                    },
                    {'$addFields': {
                        'email_sent': {'$ifNull': ['$email_sent', 0]},
                        'email_delivered': {'$ifNull': ['$email_delivered', 0]},
                        'email_open': {'$ifNull': ['$email_open', 0]},
                        'email_click': {'$ifNull': ['$email_click', 0]},
                        'email_bounce': {'$ifNull': ['$email_bounce', 0]}
                    }},
                    {
                        '$sort': {
                            '_id': 1
                        }
                    },
                    {
                        '$addFields': {
                            'email_delivery': {
                                '$cond': {
                                    'if': {
                                        '$ne': [
                                            '$email_sent', 0
                                        ]
                                    },
                                    'then': {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$email_delivered', '$email_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    },
                                    'else': 0
                                }
                            },
                            'open_percentage': {
                                '$cond': {
                                    'if': {
                                        '$ne': [
                                            '$email_sent', 0
                                        ]
                                    },
                                    'then': {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$email_open', '$email_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    },
                                    'else': 0
                                }
                            },
                            'click_percentage': {
                                '$cond': {
                                    'if': {
                                        '$ne': [
                                            '$email_sent', 0
                                        ]
                                    },
                                    'then': {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$email_click', '$email_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    },
                                    'else': 0
                                }
                            },
                            'bounce_percentage': {
                                '$cond': {
                                    'if': {
                                        '$ne': [
                                            '$email_sent', 0
                                        ]
                                    },
                                    'then': {
                                        '$round': [
                                            {
                                                '$multiply': [
                                                    {
                                                        '$divide': [
                                                            '$email_bounce', '$email_sent'
                                                        ]
                                                    }, 100
                                                ]
                                            }, 2
                                        ]
                                    },
                                    'else': 0
                                }
                            }
                        }
                    }, {
                        '$project': {
                            '_id': 1,
                            'email_sent': 1,
                            'email_delivered': 1,
                            'email_delivery': 1,
                            'email_open': 1,
                            'open_percentage': 1,
                            'email_click': 1,
                            'click_percentage': 1,
                            'email_bounce': 1,
                            'bounce_percentage': 1
                        }
                    },
                    {
                        '$sort': {
                            '_id': -1
                        }
                    }
                ]
                unsubscribe_pipeline = [
                    {
                        '$match': {
                            "unsubscribe.value": True,
                            "$or": unsubscribe_dates
                        }
                    },
                    *(
                        [{
                            '$match': {
                                'allocate_to_counselor.counselor_id': {
                                    '$in': counselor_id
                                }
                            }
                        }]
                        if counselor_id else []
                    ),
                    {
                        '$project': {
                            'date': {
                                '$dateToString': {
                                    'format': "%Y-%m-%d",
                                    'date': '$unsubscribe.timestamp'
                                }
                            },
                            'unsubscribe': {
                                '$cond': {
                                    'if': {
                                        '$gt': [
                                            '$unsubscribe.value', None
                                        ]
                                    },
                                    'then': 1,
                                    'else': 0
                                }
                            }
                        }
                    }, {
                        '$group': {
                            '_id': '$date',
                            'unsubscribe': {
                                '$sum': '$unsubscribe'
                            }
                        }
                    },
                    {
                        '$unionWith': {
                            'pipeline': [
                                {'$documents': unsubscribe_documents}
                            ]
                        }
                    },
                    {
                        '$group': {
                            '_id': '$_id',
                            'unsubscribe': {'$sum': '$unsubscribe'},
                        }
                    },
                    {
                        '$sort': {
                            '_id': -1
                        },
                    }
                ]
            if sort and sort != "unsubscribe":
                pipeline.append({
                    "$sort": {
                        f"email_{sort}": 1 if sort_type == "asc" else -1
                    }
                })
            results = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
            unsubscribe_results = await DatabaseConfiguration().studentsPrimaryDetails.aggregate(unsubscribe_pipeline).to_list(None)
            raw_unsubscribed_data = await DatabaseConfiguration().raw_data.aggregate(
                unsubscribe_pipeline).to_list(None)
            unsubscribe_results = {data.get("_id"): data for data in unsubscribe_results}
            raw_unsubscribed_data = {data.get("_id"): data for data in raw_unsubscribed_data}
            total = {
                'email_sent': 0,
                'email_delivered': 0,
                'email_open': 0,
                'email_click': 0,
                'email_bounce': 0,
                'email_unsubscribe': 0,
            }
            for res in results:
                unsubscribe_detail = unsubscribe_results.get(res.get("_id"), {})
                raw_unsubscribed_detail = raw_unsubscribed_data.get(res.get("_id"), {})
                sent_count = res.get("email_sent", 0)
                if unsubscribe_detail or raw_unsubscribed_detail:
                    unsubscribe_count = (unsubscribe_detail.get("unsubscribe", 0) +
                                         raw_unsubscribed_detail.get("unsubscribe", 0))
                    res.update({
                        "unsubscribe": unsubscribe_count,
                        "unsubscribe_percentage": round(unsubscribe_count / sent_count * 100,
                                                        2) if sent_count != 0 else 0
                    })
                else:
                    res.update({
                        "unsubscribe": 0,
                        "unsubscribe_percentage": 0
                    })
                total.update({
                    'email_sent': total.get('email_sent', 0) + sent_count,
                    'email_delivered': total.get('email_delivered', 0) + res.get('email_delivered', 0),
                    'email_open': total.get('email_open', 0) + res.get('email_open', 0),
                    'email_click': total.get('email_click', 0) + res.get('email_click', 0),
                    'email_bounce': total.get('email_bounce', 0) + res.get('email_bounce', 0),
                    'unsubscribe': total.get('unsubscribe', 0) + res.get('unsubscribe', 0),
                })
            total_sent = total.get("sent")
            total.update({
                "email_delivery": round(total.get("delivered") / total_sent * 100, 2) if total_sent else 0,
                "open_percentage": round(total.get("open") / total_sent * 100, 2) if total_sent else 0,
                "click_percentage": round(total.get("click") / total_sent * 100, 2) if total_sent else 0,
                "bounce_percentage": round(total.get("bounce") / total_sent * 100, 2) if total_sent else 0,
                "unsubscribe_percentage": round(total.get("unsubscribe") / total_sent * 100, 2) if total_sent else 0
            })
            results.append(
                {
                    "_id": "Total",
                    **total
                }
            )
            return results
        elif communication_type == "sms":
            return await self.get_sms_date_wise_details(date_range, dates, sort, sort_type, counselor_id)

    async def get_sms_date_wise_details(self, date_range: dict | None, dates: list | None,
                                        sort: str | None, sort_type: str | None, counselor_id: list | None):
        """
        Retrieves SMS details categorized by dates within the specified date range.
        Supports sorting and custom date filtering.

        Params:
            date_range (dict | None): Optional. Specifies the start and end dates for filtering SMS data.
                                      Example: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}.
            dates (list | None): Optional. A list of specific dates to include in the results.
                                 Overrides `date_range` if provided.
                                 Example: ["2024-01-01", "2024-01-15", "2024-01-31"].
            sort (str | None): Optional. The field to sort the results by.
                               Example: "sent", "failed", "delivered".
            sort_type (str | None): Optional. The sorting order, either "asc" (ascending) or "desc" (descending).
                                    Defaults to `None`.
            counselor_id (list | None): list of counselor ids for filtering data
        Returns:
            list: A list of dictionaries containing SMS details grouped by date.
                  Each dictionary includes metrics such as sent, delivered, failed counts, etc.

        Raises:
            ValueError: If both `date_range` and `dates` are `None`.
            TypeError: If inputs are not of the expected types.
        """
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=7)
        end_date = end_date.strftime("%Y-%m-%d")
        start_date = start_date.strftime("%Y-%m-%d")
        if date_range:
            start_date, end_date = date_range.get('start_date'), date_range.get('end_date')
        start_date, end_date = await utility_obj.date_change_format(
            start_date, end_date)
        number_of_days = int((end_date - start_date).days) + 1
        pipeline = [
            {
                '$match': {
                    'sms_summary.transaction_id.created_at': {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }
            },
            *(await self.counselor_pipeline(counselor_id)if counselor_id else []),
            {
                '$project': {
                    'sms_summary.transaction_id': 1
                }
            }, {
                '$unwind': {
                    'path': '$sms_summary.transaction_id',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$match': {
                    'sms_summary.transaction_id.created_at': {
                        '$gte': start_date,
                        '$lt': end_date
                    }
                }
            },
            {
                '$project': {
                    'date': {
                        '$dateToString': {
                            'format': "%Y-%m-%d",
                            'date': '$sms_summary.transaction_id.created_at'
                        }
                    },
                    'sms_sent': {
                        '$cond': {
                            'if': {
                                '$gt': [
                                    '$sms_summary.transaction_id', None
                                ]
                            },
                            'then': 1,
                            'else': 0
                        }
                    },
                    'sms_delivered': {
                        '$cond': {
                            'if': {
                                '$and': [
                                    {
                                        '$eq': [
                                            f'$sms_summary.transaction_id.sms_delivered', True
                                        ]
                                    }
                                ]
                            },
                            'then': 1,
                            'else': 0
                        }
                    },
                    'sms_not_delivered': {
                        '$cond': {
                            'if': {
                                '$and': [
                                    {
                                        '$ne': [
                                            f'$sms_summary.transaction_id.status', "SUBMIT_ACCEPTED"
                                        ]
                                    }
                                ]
                            },
                            'then': 1,
                            'else': 0
                        }
                    }
                }
            }, {
                '$group': {
                    '_id': '$date',
                    'sms_sent': {
                        '$sum': '$sms_sent'
                    },
                    'sms_delivered': {
                        '$sum': '$sms_delivered'
                    },
                    'sms_not_delivered': {
                        '$sum': '$sms_not_delivered'
                    }
                }
            }, {
                '$sort': {
                    '_id': -1
                }
            }, {
                '$facet': {
                    'data': [
                        {
                            '$project': {
                                'date': '$_id',
                                'sms_sent': 1,
                                'sms_delivered': 1,
                                'sms_not_delivered': 1,
                            }
                        }
                    ],
                    'allDates': [
                        {
                            '$project': {
                                '_id': 0,
                                'dates': {
                                    '$map': {
                                        'input': {"$range": [1, number_of_days + 1]},
                                        'as': 'day',
                                        'in': {
                                            'date': {
                                                '$dateToString': {
                                                    'format': "%Y-%m-%d",
                                                    'date': {
                                                        '$add': [
                                                            start_date, {
                                                                '$multiply': [
                                                                    '$$day', 86400000
                                                                ]
                                                            }
                                                        ]
                                                    }
                                                }
                                            },
                                            'sms_sent': 0,
                                            'sms_delivered': 0,
                                            'sms_not_delivered': 0
                                        }
                                    }
                                }
                            }
                        }, {
                            '$unwind': '$dates'
                        }, {
                            '$replaceRoot': {
                                'newRoot': '$dates'
                            }
                        }
                    ]
                }
            }, {
                '$project': {
                    'merged': {
                        '$concatArrays': [
                            '$data', '$allDates'
                        ]
                    }
                }
            }, {
                '$unwind': '$merged'
            }, {
                '$replaceRoot': {
                    'newRoot': '$merged'
                }
            }, {
                '$group': {
                    '_id': '$date',
                    'sms_sent': {
                        '$max': '$sms_sent'
                    },
                    'sms_delivered': {
                        '$max': '$sms_delivered'
                    },
                    'sms_not_delivered': {
                        '$max': '$sms_not_delivered'
                    }

                }
            },
            {
                '$sort': {
                    '_id': -1
                },
            }
        ]
        if dates:
            documents, utc_dates = [], []
            for date in dates:
                start, end = await utility_obj.date_change_format(date, date)
                utc_dates.append({
                    "sms_summary.transaction_id.created_at": {
                        "$gte": start,
                        "$lt": end
                    }
                })
                date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d %b %Y")
                documents.append({'_id': formatted_date, 'sms_sent': 0, 'sms_delivered': 0, 'sms_not_delivered': 0})

            pipeline = [
                {
                    '$match': {
                        "$or": utc_dates
                    }
                },
                *(await self.counselor_pipeline(counselor_id)if counselor_id else []),
                {
                    '$project': {
                        'sms_summary.transaction_id': 1
                    }
                }, {
                    '$unwind': {
                        'path': '$sms_summary.transaction_id',
                        'preserveNullAndEmptyArrays': True
                    }
                },
                {
                    '$match': {
                        "$or": utc_dates
                    }
                },
                {
                    '$project': {
                        'date': {
                            '$dateToString': {
                                'format': "%Y-%m-%d",
                                'date': '$sms_summary.transaction_id.created_at'
                            }
                        },
                        'sms_sent': {
                            '$cond': {
                                'if': {
                                    '$gt': [
                                        '$sms_summary.transaction_id', None
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        },
                        'sms_delivered': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {
                                            '$eq': [
                                                f'$sms_summary.transaction_id.sms_delivered', True
                                            ]
                                        }
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        },
                        'sms_not_delivered': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {
                                            '$ne': [
                                                f'$sms_summary.transaction_id.status', "SUBMIT_ACCEPTED"
                                            ]
                                        }
                                    ]
                                },
                                'then': 1,
                                'else': 0
                            }
                        }
                    }
                }, {
                    '$group': {
                        '_id': '$date',
                        'sms_sent': {
                            '$sum': '$sms_sent'
                        },
                        'sms_delivered': {
                            '$sum': '$sms_delivered'
                        },
                        'sms_not_delivered': {
                            '$sum': '$sms_not_delivered'
                        }
                    }
                },
                {
                    '$unionWith': {
                        'pipeline': [
                            {'$documents': documents}
                        ]
                    }
                },
                {
                    '$group': {
                        '_id': '$_id',
                        'sms_sent': {
                            '$sum': '$sms_sent'
                        },
                        'sms_delivered': {
                            '$sum': '$sms_delivered'
                        },
                        'sms_not_delivered': {
                            '$sum': '$sms_not_delivered'
                        }
                    }
                },
                {'$addFields': {
                    'sms_sent': {'$ifNull': ['$sms_sent', 0]},
                    'sms_delivered': {'$ifNull': ['$sms_delivered', 0]},
                    'sms_not_delivered': {'$ifNull': ['$sms_not_delivered', 0]}
                }},
                {
                    '$sort': {
                        '_id': -1
                    }
                }
            ]
        if sort:
            pipeline.append({
                "$sort": {
                    f"sms_{sort}": 1 if sort_type == "asc" else -1
                }
            })
        results = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        total = {
            'sms_sent': 0,
            'sms_delivered': 0,
            'sms_not_delivered': 0
        }
        for res in results:
            total.update({
                'sms_sent': total.get('sms_sent', 0) + res.get("sms_sent", 0),
                'sms_delivered': total.get('sms_delivered', 0) + res.get('sms_delivered', 0),
                'sms_not_delivered': total.get('sms_not_delivered', 0) + res.get('sms_not_delivered', 0),
            })
        results.append(
            {
                "_id": "Total",
                **total
            }
        )
        return results


    async def get_student_communication_details(self, date: str, communication_type: str,  user_ids: list | None = None,
                                                data_segment_ids: list | None = None, template_ids: list | None = None,
                                                program_name: list | None = None, page_num: int | None = None,
                                                page_size: int | None = None, search: str | None =None,
                                                download: bool | None = False,
                                                counselor_id: list | None = None):
        """
        Retrieves communication details for students based on various filters.

        Params:
            date (str): The specific date for filtering communication details.
                        Example: "YYYY-MM-DD".
            communication_type (str): The type of communication to analyze.
                                      Example: "email", "sms", or "whatsapp".
            user_ids (list | None): Optional. A list of user IDs to filter the communication details.
                                    Example: ["user1", "user2"].
            data_segment_ids (list | None): Optional. A list of data segment IDs to filter the communication details.
                                            Example: ["segment1", "segment2"].
            template_ids (list | None): Optional. A list of template IDs to filter the communication details.
                                        Example: ["template1", "template2"].
            program_name (list | None): Optional. A list of program names to filter the communication details.
            page_num (int | None): Optional. The page number for pagination.
                                   Example: 1.
            page_size (int | None): Optional. The number of records to return per page.
                                    Example: 50.
            search (str | None): Search goes on name, email, number
            download (bool | None): If true then download else return normal results
            counselor_id (list | None) : list of counselors ids

        Returns:
            dict: A dictionary containing filtered student communication details, including pagination metadata.

        Raises:
            ValueError: If any of the parameters are invalid or missing required data.
        """
        start_date, end_date = await utility_obj.date_change_format(date, date)
        match, last_match, search_match = {}, {}, {}
        if user_ids:
            match.update({
                f"{communication_type}_summary.transaction_id.user.id": {
                    "$in": [
                        ObjectId(user_id) if ObjectId.is_valid(user_id) else str(user_id)
                        for user_id in user_ids
                    ]
                }
            })
        if data_segment_ids:
            match.update({f"{communication_type}_summary.transaction_id.data_segment._id": {
                    "$in": [
                        ObjectId(data_segment_id) if ObjectId.is_valid(data_segment_id) else str(data_segment_id)
                        for data_segment_id in data_segment_ids
                    ]
                }})
        if template_ids:
            match.update({f"{communication_type}_summary.transaction_id.template_id": {
                "$in": [
                    value
                    for template_id in template_ids
                    for value in (
                        ObjectId(template_id) if ObjectId.is_valid(template_id) else str(template_id),
                        str(template_id),
                    )
                ]
            }})
        if program_name:
            course_filter = [
                {
                    "application_details.course_id": ObjectId(prog.get("course_id")),
                    "application_details.spec_name1": prog.get("course_specialization"),
                }
                for prog in program_name
            ]
            last_match.update({"$or": course_filter})
        if search:
            search_match.update(
                {
                    "$or": [
                        {"primary_details.basic_details.first_name": {"$regex": f".*{search}.*", "$options": "i"}},
                        {"primary_details.basic_details.middle_name": {"$regex": f".*{search}.*", "$options": "i"}},
                        {"primary_details.basic_details.last_name": {"$regex": f".*{search}.*", "$options": "i"}},
                        {"primary_details.user_name": {"$regex": f".*{search}.*", "$options": "i"}},
                        {"primary_details.basic_details.mobile_number": {"$regex": f".*{search}.*", "$options": "i"}}
                   ]
                }
            )
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        pipeline = [
            {
                "$match": {
                    f"{communication_type}_summary.transaction_id.created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                '$unwind': {
                    'path': f'${communication_type}_summary.transaction_id',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                "$match": {
                    f"{communication_type}_summary.transaction_id.created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            *([{"$match": match}] if match else []),
            {'$sort': {f'{communication_type}_summary.transaction_id.created_at': -1}},
            {
                '$lookup': {
                    'from': 'studentsPrimaryDetails',
                    'localField': 'student_id',
                    'foreignField': '_id',
                    'as': 'primary_details'
                }
            }, {
                '$unwind': {
                    'path': '$primary_details'
                }
            },
            *(
                [{
                    '$match': {
                        'primary_details.allocate_to_counselor.counselor_id': {
                            '$in': counselor_id
                        }
                    }
                }]
                if counselor_id else []
            ),
            *([{"$match": search_match}] if search_match else []),
            {
                '$lookup': {
                    'from': 'studentApplicationForms',
                    'localField': 'student_id',
                    'foreignField': 'student_id',
                    'as': 'application_details'
                }
            }, {
                '$unwind': {
                    'path': '$application_details'
                }
            },
            *([{"$match": last_match}] if last_match else []),
            {
                '$facet': {'totalCount': [{'$count': 'value'}
                                          ],
                           'pipelineResults': [
                               {'$skip': skip},
                               {'$limit': limit}
                           ]
                           }
            }, {
                '$unwind': '$pipelineResults'
            }, {
                '$unwind': '$totalCount'
            }, {
                '$replaceRoot': {
                    'newRoot': {
                        '$mergeObjects': [
                            '$pipelineResults', {
                                'totalCount': '$totalCount.value'
                            }
                        ]
                    }
                }
            },
            {
                '$lookup': {
                    'from': 'courses',
                    'localField': 'application_details.course_id',
                    'foreignField': '_id',
                    'as': 'course_details'
                }
            }, {
                '$unwind': {
                    'path': '$course_details'
                }
            }, {
                '$project': {
                    "_id": 0,
                    "totalCount": 1,
                    'student_id': {
                        '$toString': '$student_id'
                    },
                    'application_id': {
                        '$toString': '$application_details._id'
                    },
                    'student_name': {
                        '$concat': [
                            '$primary_details.basic_details.first_name', ' ', {
                                '$ifNull': [
                                    '$primary_details.basic_details.middle_name', ''
                                ]
                            }, {
                                '$cond': {
                                    'if': {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    '$primary_details.basic_details.middle_name', None
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$primary_details.basic_details.middle_name', ''
                                                ]
                                            }
                                        ]
                                    },
                                    'then': ' ',
                                    'else': ''
                                }
                            }, '$primary_details.basic_details.last_name'
                        ]
                    },
                    'custom_application_id': '$application_details.custom_application_id',
                    'template_id': {
                        '$toString': {
                            '$ifNull': [
                                f'${communication_type}_summary.transaction_id.template_id', 'None'
                            ]
                        }
                    },
                    'template_name': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": [f"${communication_type}_summary.transaction_id.template_name", None]},
                                    {"$eq": [f"${communication_type}_summary.transaction_id.template_name", ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else": f"${communication_type}_summary.transaction_id.template_name"
                        }
                    },
                    'delivered_at': {
                        '$cond': [
                            {
                                '$and': [
                                    {'$eq': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_delivered_time', None]}, None]},
                                    {'$ne': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_open_time', None]}, None]}
                                ]
                            },
                            f'${communication_type}_summary.transaction_id.{communication_type}_open_time',
                            {
                                '$cond': [
                                    {
                                        '$and': [
                                            {'$eq': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_delivered_time', None]}, None]},
                                            {'$eq': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_open_time', None]}, None]},
                                            {'$ne': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_click_time', None]}, None]}
                                        ]
                                    },
                                    f'${communication_type}_summary.transaction_id.{communication_type}_click_time',
                                    {
                                        '$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_delivered_time', "None"]
                                    }
                                ]
                            }
                        ]
                    },
                    'opened_at': {
                        '$cond': [
                            {
                                '$and': [
                                    {'$eq': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_open_time', None]}, None]},
                                    {'$eq': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_delivered_time', None]}, None]},
                                    {'$ne': [{'$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_click_time', None]}, None]}
                                ]
                            },
                            f'${communication_type}_summary.transaction_id.{communication_type}_click_time',
                            {
                                '$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_open_time', 'None']
                            }
                        ]
                    },
                    'clicked_at': {
                        '$ifNull': [f'${communication_type}_summary.transaction_id.{communication_type}_click_time', 'None']
                    },
                    'send_by_id': {
                          "$cond": {
                            "if": {
                              "$or": [
                                {"$eq": [f"${communication_type}_summary.transaction_id.user.id", None]},
                                {"$eq": [f"${communication_type}_summary.transaction_id.user.id", ""]}
                              ]
                            },
                            "then": "Transactional",
                            "else": f"${communication_type}_summary.transaction_id.user.id"
                          }
                    },
                    'send_by_profile': {
                        '$ifNull': [
                            f'${communication_type}_summary.transaction_id.user.role', 'None'
                        ]
                    },
                    'send_by_email': {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": [f'${communication_type}_summary.transaction_id.user.user_name', None]},
                                    {"$eq": [f'${communication_type}_summary.transaction_id.user.user_name', ""]}
                                ]
                            },
                            "then": "Transactional",
                            "else":  f'${communication_type}_summary.transaction_id.user.user_name'
                        }
                    },
                    'student_email': '$primary_details.user_name',
                    'student_phone': "$primary_details.basic_details.mobile_number",
                    'program_name': {"$cond": {
                        "if": {
                            "$eq": ["$application_details.spec_name1", None]},
                        "then": "$course_details.course_name",
                        "else": {"$cond": {
                            "if": {
                                "$in": [{"$toLower": "$course_details.course_name"},
                                        ["master", "bachelor"]]},
                            "then": {"$concat": [
                                "$course_details.course_name", " of ", "$application_details.spec_name1"]},
                            "else": {"$concat": [
                                "$course_details.course_name", " in ", "$application_details.spec_name1"]},
                        }}}},
                    'release_type': {
                        '$ifNull': [
                            f'${communication_type}_summary.transaction_id.release_type', 'Manual'
                        ]
                    },
                    'unsubscribe': {
                        '$ifNull': [
                            '$primary_details.unsubscribe.value', False
                        ]
                    },
                    'data_segment_name': {
                        '$ifNull': [
                            f'${communication_type}_summary.transaction_id.data_segment.name', 'None'
                        ]
                    }
                }
            }
        ]
        results = await DatabaseConfiguration().communication_log_collection.aggregate(pipeline).to_list(None)
        if download:
            return results, len(results)
        total_count = results[0].get("totalCount") if results else 0
        results = json.loads(json.dumps(results, default=str))
        return results, total_count


communication_performance_obj = CommunicationPerformanceHeader()
