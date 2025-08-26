"""
This file contain class and functions of counselor route
"""
from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation


class SourceHelper:
    """
    Contain functions related to source
    """

    async def source_lead_performing(self):
        """
        Get the details of leads on the basis of source
        """
        result = DatabaseConfiguration().studentsPrimaryDetails.aggregate(
            [
                {
                    "$project": {
                        "_id": 1,
                        "source": 1,
                        "is_verify": 1
                    }
                },
                {
                    "$group": {
                        "_id": "$_id",
                        "student": {
                            "$push": {
                                "lead_type": "$source.primary_source.lead_type",
                                "primary_source": {
                                    "$sum": {
                                        "$cond": [
                                            "$source.primary_source."
                                            "utm_source", 1, 0]}
                                },
                                "secondary_source": {
                                    "$sum": {
                                        "$cond": ["$source.secondary_source"
                                                  ".utm_source", 1, 0]
                                    }
                                },
                                "tertiary_source": {
                                    "$sum": {"$cond": [
                                        "$source.tertiary_source.utm_source",
                                        1, 0]}
                                },
                                "verify_leads": {
                                    "$sum": {
                                        "$cond": [
                                            {"$eq": ["$is_verify", True]},
                                            1, 0]
                                    }
                                },
                                "un_verify_leads": {
                                    "$sum": {
                                        "$cond": [
                                            {"$eq": ["$is_verify", False]},
                                            1, 0]
                                    }
                                },
                            }
                        },
                    }
                },
                {"$unwind": {
                    "path": "$student",
                    "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": "studentApplicationForms",
                        "let": {"student_id": "$_id"},
                        "pipeline": [
                            {"$match": {"$expr": {
                                "$eq": ["$student_id", "$$student_id"]}}},
                            {"$project": {"_id": 1, "current_stage": 1,
                                          "payment_info": 1}},
                            {
                                "$group": {
                                    "_id": "",
                                    "form_initialize": {
                                        "$sum": {
                                            "$cond": [{"$gte": [
                                                "$current_stage", 2]}, 1, 0]
                                        }
                                    },
                                    "payment_approved": {
                                        "$sum": {
                                            "$cond": [
                                                {
                                                    "$eq": [
                                                        "$payment_info.status",
                                                        "captured",
                                                    ]
                                                },
                                                1,
                                                0,
                                            ]
                                        }
                                    },
                                }
                            },
                        ],
                        "as": "student_application",
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_application",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$lookup": {
                        "from": "leadsFollowUp",
                        "let": {"student_id": "$_id"},
                        "pipeline": [
                            {"$match": {
                                "$expr": {"$eq": ["$_id", "$$student_id"]}}},
                            {
                                "$project": {
                                    "_id": 0,
                                    "lead_stage": 1,
                                }
                            },
                            {
                                "$group": {
                                    "_id": "",
                                    "lead_stage": {
                                        "$sum": {
                                            "$cond": [
                                                {"$eq": ["$lead_stage",
                                                         "Interested"]},
                                                1,
                                                0,
                                            ]
                                        }
                                    },
                                }
                            },
                        ],
                        "as": "student_lead_stage",
                    }
                },
                {
                    "$unwind": {
                        "path": "$student_lead_stage",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$group": {
                        "_id": "$student.lead_type",
                        "count": {"$sum": 1},
                        "result": {
                            "$push": {
                                "student": "$student",
                                "student_application": "$student_application",
                                "student_primary": "$student_primary",
                                "student_lead_stage": "$student_lead_stage",
                            }
                        },
                    }
                },
                {
                    "$project": {
                        "_id": "$_id",
                        "total_lead_type_leads": "$count",
                        "primary_source": {
                            "$sum": "$result.student.primary_source"},
                        "secondary_source": {
                            "$sum": "$result.student.secondary_source"},
                        "tertiary_source": {
                            "$sum": "$result.student.tertiary_source"},
                        "verify_leads": {
                            "$sum": "$result.student_primary.verify_leads"},
                        "un_verify_leads": {
                            "$sum": "$result.student_primary.un_verify_leads"
                        },
                        "form_initialize": {
                            "$sum": "$result.student_application.form_initialize"
                        },
                        "payment_approved": {
                            "$sum": "$result.student_application.payment_approved"
                        },
                        "interested_lead": {
                            "$sum": "$student_lead_stage.lead_stage"},
                    }
                },
            ]
        )
        (total_primary_source, total_secondary_source,
         total_tertiary_source, final_leads, temp) = 0, 0, 0, {}, []
        async for lead in result:
            total_primary_source += lead.get("primary_source")
            total_secondary_source += lead.get("secondary_source")
            total_tertiary_source += lead.get("tertiary_source")
            if lead.get("_id") is None:
                continue
            data = {
                "lead_type": lead.get("_id"),
                "primary_source": lead.get("primary_source"),
                "secondary_source": lead.get("secondary_source"),
                "tertiary_source": lead.get("tertiary_source"),
                "verify_leads": lead.get("verify_leads"),
                "un_verify_leads": lead.get("un_verify_leads"),
                "form_initialize": lead.get("form_initialize"),
                "payment_approved": lead.get("payment_approved"),
                "interested_lead": lead.get("interested_lead"),
                "total_lead_type": lead.get("total_lead_type_leads"),
            }
            temp.append(data)
        verified_leads = await (DatabaseConfiguration().
        studentsPrimaryDetails.count_documents(
            {"is_verify": True}))
        total_leads = await (DatabaseConfiguration().
        studentsPrimaryDetails.count_documents(
            {}))
        unverified_leads = total_leads - verified_leads
        final_leads.update({"source_wise_performance": temp, "total_leads": {
            "total_leads": total_leads,
            "total_verify_leads": verified_leads,
            "total_un_verify_leads": unverified_leads,
            "total_primary_source": total_primary_source,
            "total_secondary_source": total_secondary_source,
            "total_tertiary_source": total_tertiary_source,
        }})
        return final_leads

    async def counselor_helper(self, counselor_id, course_name):
        """
        Course assign counselor
        """
        user = await DatabaseConfiguration().user_collection.find_one(
            {"_id": ObjectId(counselor_id)})
        if await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counselor_id),
                 "course_assign": {"$exists": True}}) is not None:
            course_assign = user.get("course_assign")
            if course_name not in course_assign:
                course_assign.append(course_name)
        else:
            course_assign = [course_name]
        await DatabaseConfiguration().user_collection.update_one(
            {"_id": ObjectId(counselor_id)},
            {"$set": {"course_assign": course_assign}})
        await cache_invalidation(api_updated="updated_user", user_id=user.get('email') if user else None)

    async def course_assign_counselor(self, counselor_id, course_name,
                                      college_id):
        """
        Assign counselor to course
        """
        try:
            user = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(counselor_id)})
        except Exception:
            raise HTTPException(status_code=404, detail="counselor not found")
        for stream in course_name:
            if (
                    course_detail := await DatabaseConfiguration().course_collection.find_one(
                        {"course_name": stream,
                         "college_id": {
                             "$in": college_id}})) is None:
                raise HTTPException(status_code=404, detail="course not found")
            if (
                    course := await DatabaseConfiguration().course_collection.find_one(
                    {"course_name": stream, "college_id": {"$in": college_id},
                     "course_counselor": {"$exists": True}})) is not None:
                course_counselor = course.get("course_counselor")
                if ObjectId(counselor_id) not in course_counselor:
                    course_counselor.append(ObjectId(counselor_id))
            else:
                course_counselor = [ObjectId(counselor_id)]
            await DatabaseConfiguration().course_collection.update_one(
                {"_id": ObjectId(course_detail.get("_id"))},
                {"$set": {"course_counselor": course_counselor}})
            await self.counselor_helper(counselor_id=counselor_id,
                                        course_name=stream)
        return True, user
