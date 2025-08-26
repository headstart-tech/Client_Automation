"""
This file contain class and functions for start teamcity build to generate report
"""
import json
import requests
from app.core.log_config import get_logger
from app.core.utils import settings

logger = get_logger(name=__name__)

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {settings.teamcity_token}",
}


class TeamcityConfig:
    """
    Contain function related to teamcity build
    """

    async def generate_report_using_teamcity(
            self, report_type, report_format, start_date, end_date, payload
    ):
        """
        Generate report using teamcity build
        """
        payload = json.dumps(
            {
                "buildType": {"id": settings.teamcity_build_type},
                "tags": {
                    "tag": [
                        {"name": "user_id", "private": False},
                        {"name": "report_type", "private": False},
                    ]
                },
                "properties": {
                    "property": [
                        {"name": "env.PAYLOAD", "value": json.dumps(payload)},
                        {"name": "env.START_DATE", "value": start_date},
                        {"name": "env.END_DATE", "value": end_date},
                        {"name": "env.REPORT_TYPE", "value": report_type},
                        {"name": "env.REPORT_FORMAT", "value": report_format}
                    ]
                },
            }
        )
        try:
            response = requests.request(
                "POST",
                f"{settings.teamcity_base_path}/app/rest/buildQueue",
                headers=headers,
                data=payload,
            )
            if response.status_code != 200:
                logger.error(response.text)
                return
            return response
        except Exception as e:
            logger.error(f"Something went wrong. {str(e.args)}")
