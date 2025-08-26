"""
This file contain functions and class related to database
"""
import inspect
import json
import re
from pathlib import Path, PurePath
import pandas as pd
from bson import json_util
from fastapi.exceptions import HTTPException


def read_mongoextjson_file(filename):
    """
    Reads a MongoDB Extended JSON file and converts it to a Python dictionary.

    :param filename: The path to the MongoDB Extended JSON file.
    :return: A Python dictionary containing the data from the file.
    """
    # Read the contents of the file and convert to a JSON string
    bsondata = json.dumps(filename)

    # Convert TenGen JSON to Strict JSON by replacing ObjectId with "$oid"
    # and Date with "$date"
    jsondata = re.sub(r"ObjectId\s*\(\s*\"(\S+)\"\s*\)", r'{"$oid": "\1"}',
                      bsondata)

    # Parse the JSON string and use MongoDB's object_hook function to get
    # Python objects for ObjectId and Date

    data = json.loads(jsondata, object_hook=json_util.object_hook)

    return data


class Upload_file:

    def __init__(self):
        self.collection_name = [
            "courses",
            "studentsPrimaryDetails",
            "loginActivity",
            "studentSecondaryDetails",
            "studentApplicationForms",
            "studentTimeline",
            "lead_details",
            "leadsFollowUp",
            "payments",
            "counselor_management",
            "tag_list",
            "queries",
            "queryCategories",
            "boardDetails",
            "templates",
            "activity_email",
            "application_payment_invoices",
            "reports",
            "raw_data",
            "meeting",
            "exam_schedules",
            "template_gallery",
            "promocode",
            "questions",
            "activity_download_request",
            "checkInOutLog",
            "offline_data",
            "notifications",
            "sms_template",
            "sms_activity",
            "automation",
            "campaign",
            "campaign_rule",
            "rule",
            "automation_activity",
            "otpTemplates",
            "componentCharges",
            "call_activity",
            "healthScienceCourses",
            "events",
            "FieldMapping",
            "interviewSelectionProcedure",
            "interviewLists",
            "panels",
            "slots",
            "interviewLists",
            "call_activity",
            "vouchers",
            "userUpdates",
            "scripts",
            "template_merge_fields",
            "advanceFilterFields"
        ]
        self.master_collections = [
            "users",
            "colleges",
            "refreshToken",
            "advanceFilterFields",
            "template_merge_fields"
        ]

    def upload_data(self, master_database, season_database):
        path = Path(inspect.getfile(inspect.currentframe())).resolve()
        path = PurePath(path).parent.parent
        path = PurePath(path, Path(r"tests/file_json"))
        file = Path(path).iterdir()
        files = [PurePath(i).stem for i in file]
        path = str(path)
        for col in files:
            full_path = PurePath(path, Path(rf"{col}.json"))
            data = pd.read_json(str(full_path))
            payload = json.loads(data.to_json(orient="records"))
            payload = read_mongoextjson_file(payload)
            if col in self.master_collections:
                cl = master_database[col]
            else:
                cl = season_database[col]
            try:
                cl.insert_many(payload)
            except Exception:
                raise HTTPException(
                    status_code=409, detail="conflict with the inserted data"
                )
