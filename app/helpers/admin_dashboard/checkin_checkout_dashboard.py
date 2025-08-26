"""
Check In Check Out Module data helper.
"""
import datetime
import json

from fastapi import HTTPException

from app.database.configuration import DatabaseConfiguration
from app.core.utils import utility_obj, settings
from bson.objectid import ObjectId

from app.dependencies.oauth import cache_invalidation, get_redis_client


class CheckINCheckOUTHelper:
    """
    All related functions of Checkin Checkout
    """

    async def get_top_header(self, role_ids: list, college_id: str) -> dict:
        """
        Retrieve header details based on role IDs and college ID.
        This method fetches header-related data for the given role IDs and associated college.
        Params:
            role_ids (str): Comma-separated role IDs for which the header details are required.
            college_id (str): The unique identifier of the college.

        Returns:
            dict: A dictionary containing header details specific to the roles and college.
        """
        users_pipeline = [
            {
                "$match": {
                    "associated_colleges": {"$in": [ObjectId(college_id)]}
                }
            },
            {
                '$group': {
                    '_id': '$is_activated',
                    'count': {
                        '$sum': 1
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'status': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$_id', True
                                ]
                            },
                            'then': 'active',
                            'else': 'inactive'
                        }
                    },
                    'count': 1
                }
            }, {
                '$group': {
                    '_id': None,
                    'result': {
                        '$push': {
                            'k': '$status',
                            'v': '$count'
                        }
                    }
                }
            }, {
                '$replaceRoot': {
                    'newRoot': {
                        '$arrayToObject': '$result'
                    }
                }
            }
        ]
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        pipeline = [
            {
                "$match": {
                    "date": today_date
                }
            },
            {
                '$group': {
                    '_id': '$current_stage',
                    'count': {
                        '$sum': 1
                    }
                }
            }, {
                '$match': {
                    '_id': {
                        '$ne': None
                    }
                }
            }, {
                '$group': {
                    '_id': None,
                    'result': {
                        '$push': {
                            'k': {
                                '$toString': '$_id'
                            },
                            'v': '$count'
                        }
                    }
                }
            }, {
                '$replaceRoot': {
                    'newRoot': {
                        '$arrayToObject': '$result'
                    }
                }
            }
        ]
        if role_ids:
            users_pipeline[0].get("$match", {}).update({"role.role_name": {"$in": role_ids}})
            pipeline[0].get("$match", {}).update({"user_details.role_name": {"$in": role_ids}})
        active_details = await DatabaseConfiguration().user_collection.aggregate(users_pipeline).to_list(None)
        result_dict = active_details[0] if active_details else {}
        login_details = await DatabaseConfiguration().checkincheckout.aggregate(pipeline).to_list(None)
        login_details = login_details[0] if login_details else {}
        login, logout, checkin, checkout = (login_details.get("LogIn", 0), login_details.get("LogOut", 0),
                                            login_details.get("CheckIn", 0), login_details.get("CheckOut", 0))
        result_dict.update({
            "Login": login,
            "Logout": logout,
            "Checkin": checkin,
            "Checkout": checkout,
            "total_active": login + logout,
            "total_login": checkin + checkout,
            "total_users": result_dict.get("active", 0) + result_dict.get("inactive", 0),
            "message": "CheckIn CheckOut Top Headers"
        })
        result_dict["total_active"] = result_dict.get("Login", 0) + result_dict.get("Logout", 0)
        result_dict["total_login"] = result_dict.get("CheckIn", 0) + result_dict.get("CheckOut", 0)
        return result_dict

    async def get_manage_sessions(self, role_ids: list, user_ids: list, date: str) -> list:
        """
            Retrieve and manage user sessions based on roles, users, and date.

            Params:
                role_ids (list): List of role IDs to filter sessions by user roles.
                user_ids (list): List of user IDs to filter sessions.
                date (str): Date string (in 'YYYY-MM-DD' format) to filter sessions for a specific day.

            Returns:
                dict: A dictionary containing session details filtered by roles, users, and date.
        """
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if date:
            today_date = date
        pipeline = [
            {
                "$match": {
                    "date": today_date
                }
            }, {
                '$addFields': {
                    'computerloginhourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$computer_login_details.timestamp',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'computerloginminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$computer_login_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'computerloginsecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$computer_login_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'mobileloginhourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$mobile_login_details.timestamp',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'mobileloginminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$mobile_login_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'mobileloginsecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$mobile_login_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'checkinloginhourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$first_checkin',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'checkinloginminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$first_checkin',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'checkinloginsecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$first_checkin',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'checkouthourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$last_checkout',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'checkoutminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$last_checkout',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'checkoutsecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$last_logout',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'mobilelogouthourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$mobile_logout_details.timestamp',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'mobilelogoutminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$mobile_logout_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'mobilelogoutsecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$mobile_logout_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'computerlogouthourIST': {
                        '$add': [
                            {
                                '$hour': {
                                    'date': '$computer_logout_details.timestamp',
                                    'timezone': 'Asia/Kolkata'
                                }
                            }, 0
                        ]
                    },
                    'computerlogoutminuteIST': {
                        '$dateToString': {
                            'format': '%M',
                            'date': '$computer_logout_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    },
                    'computerlogoutsecondIST': {
                        '$dateToString': {
                            'format': '%S',
                            'date': '$computer_logout_details.timestamp',
                            'timezone': 'Asia/Kolkata'
                        }
                    }
                }
            }, {
                '$addFields': {
                    'computerloginformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$computerloginhourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$computerloginhourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$computerloginhourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'computerloginAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$computerloginhourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    },
                    'mobileloginformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$mobileloginhourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$mobileloginhourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$mobileloginhourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'mobileloginAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$mobileloginhourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    },
                    'checkinloginformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$checkinloginhourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$checkinloginhourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$checkinloginhourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'checkinloginAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$checkinloginhourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    },
                    'checkoutformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$checkouthourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$checkouthourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$checkouthourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'checkoutAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$checkouthourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    },
                    'mobilelogoutformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$mobilelogouthourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$mobilelogouthourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$mobilelogouthourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'mobilelogoutAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$mobilelogouthourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    },
                    'computerlogoutformatted_hour': {
                        '$cond': {
                            'if': {
                                '$eq': [
                                    '$computerlogouthourIST', 0
                                ]
                            },
                            'then': 12,
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$eq': [
                                            '$computerlogouthourIST', 12
                                        ]
                                    },
                                    'then': 12,
                                    'else': {
                                        '$mod': [
                                            '$computerlogouthourIST', 12
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    'computerlogoutAMPM': {
                        '$cond': [
                            {
                                '$lt': [
                                    '$computerlogouthourIST', 12
                                ]
                            }, 'AM', 'PM'
                        ]
                    }
                }
            }, {
                '$addFields': {
                    'mobile_login': {
                        '$concat': [
                            {
                                '$toString': '$mobilelogoutformatted_hour'
                            }, ':', '$mobilelogoutminuteIST', ':', '$mobilelogoutsecondIST', ' ', '$mobilelogoutAMPM'
                        ]
                    },
                    'computer_login': {
                        '$concat': [
                            {
                                '$toString': '$computerloginformatted_hour'
                            }, ':', '$computerloginminuteIST', ':', '$computerloginsecondIST', ' ', '$computerloginAMPM'
                        ]
                    },
                    'checkin': {
                        '$concat': [
                            {
                                '$toString': '$checkinloginformatted_hour'
                            }, ':', '$checkinloginminuteIST', ':', '$checkinloginsecondIST', ' ', '$checkinloginAMPM'
                        ]
                    },
                    'checkout': {
                        '$concat': [
                            {
                                '$toString': '$checkoutformatted_hour'
                            }, ':', '$checkoutminuteIST', ':', '$checkoutsecondIST', ' ', '$checkoutAMPM'
                        ]
                    },
                    'mobile_logout': {
                        '$concat': [
                            {
                                '$toString': '$mobilelogoutformatted_hour'
                            }, ':', '$mobilelogoutminuteIST', ':', '$mobilelogoutsecondIST', ' ', '$mobilelogoutAMPM'
                        ]
                    },
                    'computer_logout': {
                        '$concat': [
                            {
                                '$toString': '$computerlogoutformatted_hour'
                            }, ':', '$computerlogoutminuteIST', ':', '$computerlogoutsecondIST', ' ', '$computerlogoutAMPM'
                        ]
                    },
                    'login_hrs': {
                        '$cond': [
                            {
                                '$not': '$first_login'
                            }, None, {
                                '$let': {
                                    'vars': {
                                        'startTime': '$first_login',
                                        'endTime': {
                                            '$ifNull': [
                                                '$last_logout', {
                                                    '$toDate': '$$NOW'
                                                }
                                            ]
                                        }
                                    },
                                    'in': {
                                        '$let': {
                                            'vars': {
                                                'durationInMinutes': {
                                                    '$trunc': {
                                                        '$divide': [
                                                            {
                                                                '$subtract': [
                                                                    '$$endTime', '$$startTime'
                                                                ]
                                                            }, 60000
                                                        ]
                                                    }
                                                }
                                            },
                                            'in': {
                                                '$concat': [
                                                    {
                                                        '$toString': {
                                                            '$trunc': {
                                                                '$divide': [
                                                                    '$$durationInMinutes', 60
                                                                ]
                                                            }
                                                        }
                                                    }, ' hrs ', {
                                                        '$toString': {
                                                            '$mod': [
                                                                '$$durationInMinutes', 60
                                                            ]
                                                        }
                                                    }, ' min'
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    },
                    'totalCheckInMinutes': {
                        '$let': {
                            'vars': {
                                'lastCheckIn': {
                                    '$arrayElemAt': [
                                        '$check_in_details', -1
                                    ]
                                },
                                'summedMinutes': {
                                    '$sum': '$check_in_details.total_mins'
                                }
                            },
                            'in': {
                                '$add': [
                                    '$$summedMinutes', {
                                        '$cond': [
                                            {
                                                '$not': '$$lastCheckIn.check_out'
                                            }, {
                                                '$trunc': {
                                                    '$divide': [
                                                        {
                                                            '$subtract': [
                                                                {
                                                                    '$toDate': '$$NOW'
                                                                }, '$$lastCheckIn.check_in'
                                                            ]
                                                        }, 60000
                                                    ]
                                                }
                                            }, 0
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }, {
                '$addFields': {
                    'checkin_hrs': {
                        '$let': {
                            'vars': {
                                'totalMinutes': '$totalCheckInMinutes'
                            },
                            'in': {
                                '$concat': [
                                    {
                                        '$toString': {
                                            '$trunc': {
                                                '$divide': [
                                                    '$$totalMinutes', 60
                                                ]
                                            }
                                        }
                                    }, ' hrs ', {
                                        '$toString': {
                                            '$mod': [
                                                '$$totalMinutes', 60
                                            ]
                                        }
                                    }, ' min'
                                ]
                            }
                        }
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'user_id': {
                        '$toString': '$user_details.user_id'
                    },
                    'name': '$user_details.name',
                    'profile': '$user_details.role_name',
                    'email': '$user_details.user_name',
                    'mobile_login': '$mobile_login',
                    'computer_login': '$computer_login',
                    'checkin': '$checkin',
                    'login_hrs': '$login_hrs',
                    'checkin_hrs': '$checkin_hrs',
                    'checkout': '$checkout',
                    'mobile_logout': '$mobile_logout',
                    'computer_logout': '$computer_logout',
                    'mobile_login_ip_address': '$mobile_login_details.ip_address',
                    'computer_login_ip_address': '$computer_login_details.ip_address',
                    'mobile_logout_ip_address': '$mobile_logout_details.ip_address',
                    'computer_logout_ip_address': '$computer_logout_details.ip_address',
                    'mobile_device_info': '$mobile_login_details.ip_address',
                    'computer_device_info': '$computer_login_details.device_info',
                    'current_stage': '$current_stage',
                    'live_on_computer': {
                        '$ifNull': [
                            '$live_on_computer', None
                        ]
                    },
                    'live_on_mobile': {
                        '$ifNull': [
                            '$live_on_mobile', None
                        ]
                    }
                }
            }
        ]
        if role_ids:
            pipeline[0].get("$match", {}).update({
                "user_details.role_name": {"$in": role_ids}
            })
        if user_ids:
            user_ids = [ObjectId(id) for id in user_ids if ObjectId.is_valid(id)]
            pipeline[0].get("$match", {}).update({
                "user_details.user_id": {"$in": user_ids}
            })
        return await DatabaseConfiguration().checkincheckout.aggregate(pipeline).to_list(None)

    async def get_bench_marking(self, date: str) -> list:
        """
        Retrieves benchmarking data for the given date.

        Params:
            date (str): The date for which benchmarking data is requested.

        Returns:
            list: A list containing benchmarking data.
        """
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if date:
            today_date = date
        pipeline = [
            {
                "$match": {
                    "date": today_date
                }
            },
            {
                '$addFields': {
                    'login_hrs': {
                        '$cond': [
                            {
                                '$not': '$first_login'
                            }, None, {
                                '$let': {
                                    'vars': {
                                        'startTime': '$first_login',
                                        'endTime': {
                                            '$ifNull': [
                                                '$last_logout', {
                                                    '$toDate': '$$NOW'
                                                }
                                            ]
                                        }
                                    },
                                    'in': {
                                        '$let': {
                                            'vars': {
                                                'durationInMinutes': {
                                                    '$trunc': {
                                                        '$divide': [
                                                            {
                                                                '$subtract': [
                                                                    '$$endTime', '$$startTime'
                                                                ]
                                                            }, 60000
                                                        ]
                                                    }
                                                }
                                            },
                                            'in': {
                                                '$concat': [
                                                    {
                                                        '$toString': {
                                                            '$trunc': {
                                                                '$divide': [
                                                                    '$$durationInMinutes', 60
                                                                ]
                                                            }
                                                        }
                                                    }, ' hrs ', {
                                                        '$toString': {
                                                            '$mod': [
                                                                '$$durationInMinutes', 60
                                                            ]
                                                        }
                                                    }, ' min'
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    },
                    'totalCheckInMinutes': {
                        '$let': {
                            'vars': {
                                'lastCheckIn': {
                                    '$arrayElemAt': [
                                        '$check_in_details', -1
                                    ]
                                },
                                'summedMinutes': {
                                    '$sum': '$check_in_details.total_mins'
                                }
                            },
                            'in': {
                                '$add': [
                                    '$$summedMinutes', {
                                        '$cond': [
                                            {
                                                '$not': '$$lastCheckIn.check_out'
                                            }, {
                                                '$trunc': {
                                                    '$divide': [
                                                        {
                                                            '$subtract': [
                                                                {
                                                                    '$toDate': '$$NOW'
                                                                }, '$$lastCheckIn.check_in'
                                                            ]
                                                        }, 60000
                                                    ]
                                                }
                                            }, 0
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }, {
            '$addFields': {
                'checkin_hrs': {
                    '$let': {
                        'vars': {
                            'totalMinutes': '$totalCheckInMinutes'
                        },
                        'in': {
                            '$concat': [
                                {
                                    '$toString': {
                                        '$trunc': {
                                            '$divide': [
                                                '$$totalMinutes', 60
                                            ]
                                        }
                                    }
                                }, ' hrs ', {
                                    '$toString': {
                                        '$mod': [
                                            '$$totalMinutes', 60
                                        ]
                                    }
                                }, ' min'
                            ]
                        }
                    }
                }
            }
            }, {
                '$lookup': {
                    'from': 'counselor_management',
                    'localField': 'user_id',
                    'foreignField': 'counselor_id',
                    'as': 'management'
                }
            }, {
                '$unwind': {
                    'path': '$management',
                    'preserveNullAndEmptyArrays': True
                }
            }, {
                '$addFields': {
                    'datesInCurrentMonth': {
                        '$filter': {
                            'input': {
                                '$map': {
                                    'input': {
                                        '$ifNull': [
                                            '$management.no_allocation_date', []
                                        ]
                                    },
                                    'as': 'date',
                                    'in': {
                                        '$dateFromString': {
                                            'dateString': '$$date',
                                            'format': '%Y-%m-%d'
                                        }
                                    }
                                }
                            },
                            'as': 'convertedDate',
                            'cond': {
                                '$and': [
                                    {
                                        '$eq': [
                                            {
                                                '$year': '$$convertedDate'
                                            }, {
                                                '$year': '$$NOW'
                                            }
                                        ]
                                    }, {
                                        '$eq': [
                                            {
                                                '$month': '$$convertedDate'
                                            }, {
                                                '$month': '$$NOW'
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }, {
                '$addFields': {
                    'daysInCurrentMonth': {
                        '$size': {
                            '$ifNull': [
                                '$datesInCurrentMonth', []
                            ]
                        }
                    }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'user_id': {"$toString": "$_id"},
                    'user_name': '$user_details.user_name',
                    'name': '$user_details.name',
                    'profile': '$user_details.role_name',
                    'login_hrs': '$login_hrs',
                    'checkin_hrs': '$checkin_hrs',
                    'leaves': '$daysInCurrentMonth'
                }
            }
        ]
        result = await DatabaseConfiguration().checkincheckout.aggregate(pipeline).to_list(None)
        return result

    async def update_status(self, user_id: str, action: str, user: dict) -> bool:
        """
        Updates the status of a user based on the specified action.

        Params:
            user_id (str): The unique identifier of the user whose status needs to be updated.
            action (UpdateAction): The action to be performed on the user's status. Possible actions include:
            user (dict): Details of user
        Returns:
            Bool: A response indicating the success or failure of the update operation.
        """
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if (counselor_data := await DatabaseConfiguration().user_collection.find_one({
            "_id": ObjectId(user_id)
        })) is None:
            raise HTTPException(status_code=404, detail="User not found!")
        if (user_data := await DatabaseConfiguration().checkincheckout.find_one({
            "user_id": ObjectId(user_id),
            "date": today_date
        })) is None:
            raise HTTPException(status_code=404, detail="User didn't Login yet!")
        present_status = user_data.get("current_stage")
        present_time = datetime.datetime.utcnow()
        if present_status == action:
            raise HTTPException(status_code=422, detail=f"User is already {action}")
        flag = False
        if action == "CheckOut" or "LogOut":
            check_in_details = user_data.get("check_in_details", [])
            for i in range(len(check_in_details) - 1, -1, -1):
                if check_in_details[i].get("check_in") and not check_in_details[i].get("check_out", None):
                    check_in_time = check_in_details[i].get("check_in")
                    total_mins = int((present_time - check_in_time).total_seconds() // 60)
                    DatabaseConfiguration().checkincheckout.update_one({
                        "user_id": ObjectId(user_id),
                        "date": today_date,
                        f"check_in_details.{i}.check_out": {"$exists": False},
                    }, {
                        "$set": {
                            f"check_in_details.{i}.check_out": present_time,
                            f"check_in_details.{i}.total_mins": total_mins,
                            "current_stage": "CheckOut",
                            "last_checkout": present_time,
                        }
                    })
                    await DatabaseConfiguration().user_collection.update_one({"_id": ObjectId(user_id)},
                                                                             {"$set": {"status_active": False}})
                    await cache_invalidation(api_updated="updated_user", user_id=counselor_data.get("email"))
                    redis_client = get_redis_client()
                    if redis_client:
                        data = {
                            "status": False,
                            "name": utility_obj.name_can(counselor_data),
                            "mobile_number": counselor_data.get("mobile_number")
                        }
                        redis_key = f"{settings.aws_env}/{utility_obj.get_university_name_s3_folder()}/{str(counselor_data.get('_id'))}/check_in_status"
                        await redis_client.set(redis_key, json.dumps(data))
                        await redis_client.publish(redis_key, json.dumps(data))
                    flag = True
                    break
        if action == "LogOut":
            login_details = user_data.get("login_details", [])
            for i in range(len(login_details) - 1, -1, -1):
                if login_details[i].get("login") and not login_details[i].get("logout", None):
                    check_in_time = login_details[i].get("login")
                    total_mins = int((present_time - check_in_time).total_seconds() // 60)
                    DatabaseConfiguration().checkincheckout.update_one({
                        "user_id": ObjectId(user_id),
                        "date": today_date,
                        f"login_details.{i}.logout": {"$exists": False},
                    }, {
                        "$set": {
                            f"login_details.{i}.logout": present_time,
                            f"login_details.{i}.total_mins": total_mins,
                            f"computer_logout_details.timestamp": present_time,
                            "current_stage": "LogOut",
                            "last_logout": present_time,
                            "live_on_computer": False,
                            "live_on_mobile": False
                        }
                    })
                    flag = True
        return flag

checkincheckout_obj = CheckINCheckOUTHelper()
