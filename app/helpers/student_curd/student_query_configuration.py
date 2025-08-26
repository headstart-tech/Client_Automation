"""
This file contain class and functions related to student query
"""
import datetime
from app.core.utils import utility_obj, settings
from app.helpers.report.pdf_configuration import PDFHelper
import pathlib
from app.database.database_sync import DatabaseConfigurationSync


class QueryHelper:
    """
    Contain functions related to student query configuration
    """

    def query_helper(self, query_details):
        """
        Get student query details
        """
        course_name = query_details.get("course_name")
        spec_name = query_details.get("specialization_name")
        application = DatabaseConfigurationSync().studentApplicationForms.\
            find_one({"student_id": query_details.get("student_id")})
        if query_details.get("application_id"):
            app_id = str(query_details.get("application_id"))
        else:
            if course_name not in ["", None]:
                course = DatabaseConfigurationSync().course_collection.\
                    find_one({"course_name": course_name})
                if not course:
                    course = {}
                app = DatabaseConfigurationSync().studentApplicationForms.\
                find_one({"student_id": query_details.get("student_id"),
                          "course_id": course.get('_id')})
                if not app:
                    app = {}
                app_id = str(app.get("_id")) if app else str(
                    application.get("_id")) if application else None
            else:
                app_id = str(application.get("_id")) if application else None
        created = query_details.get("created_at", datetime.datetime.utcnow())
        updated_at = query_details.get("updated_at", None)
        status = query_details.get("status")
        time_diff = ""
        if updated_at and status.lower() == "done":
            created_str = created.strftime("%d %b %Y %I:%M:%S %p")
            created = datetime.datetime.strptime(created_str, "%d %b %Y %I:%M:%S %p")
            updated_str = updated_at.strftime("%d %b %Y %I:%M:%S %p")
            updated = datetime.datetime.strptime(updated_str, "%d %b %Y %I:%M:%S %p")
            time_diff = utility_obj.calculate_time_diff(created, updated, req_hrs=True)
        else:
            updated_at = ""
        return {
            "_id": str(query_details.get("_id")),
            "ticket_id": query_details.get("ticket_id"),
            "course_name": course_name,
            "specialization_name": spec_name,
            "student_id": str(query_details.get("student_id")),
            "student_name": query_details.get("student_name"),
            "student_email_id": query_details.get("student_email_id"),
            "category_id": str(query_details.get("category_id")),
            "category_name": query_details.get("category_name"),
            "title": query_details.get("title"),
            "description": query_details.get("description"),
            "status": status,
            "replies": (
                {
                    "user_id": str(reply.get("user_id", "")),
                    "user_name": settings.university_name if reply.get(
                        "is_replied_by_student") is False and
                                                             settings.university_name == "The Apollo University" else reply.get(
                        "user_name"),
                    "is_replied_by_student": reply.get(
                        "is_replied_by_student"),
                    "message": reply.get("message"),
                    "timestamp": utility_obj.get_local_time(
                        reply.get("timestamp", datetime.datetime.utcnow())),
                }
                for reply in query_details.get("replies")
            )
            if query_details.get("replies")
            else None,
            "attachments": query_details.get("attachments"),
            "assigned_counselor_id": str(query_details.get("assigned_counselor_id")),
            "assigned_counselor_name": query_details.get("assigned_counselor_name"),
            "created_at": utility_obj.get_local_time(query_details.get("created_at", datetime.datetime.utcnow())),
            "updated_at": utility_obj.get_local_time(updated_at) if
                                                     updated_at else None,
            "application_id": app_id,
            "resolution_time": time_diff
        }

    def query_replies(self, query_replies):
        """
        Get query replies details
        """
        return {
            "timestamp": utility_obj.get_local_time(query_replies.get("timestamp")),
            "message": query_replies.get("message"),
            "user_id": str(query_replies.get("user_id")),
            "user_name": query_replies.get("user_name"),
            "is_replied_by_student": query_replies.get("is_replied_by_student"),
        }

    async def get_student_program_queries_pdf(self, data: list):
        """
        Get student program-wise queries pdf link.

        Params:
            data (list): A list which contains student program-wise queries
                in a dictionary format.

        Returns:
            dict: A dictionary which contains student program-wise queries
                pdf link.
        """
        pdf = PDFHelper().pdf_initial_configuration()
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=20,
            x_point=300,
            y_point=50,
            section_heading="Program queries",
            section_content_font_size=12
        )
        start_y_point, count = 100, 1
        for query_doc in data:
            basic_content = [
                f"Ticket ID : {query_doc.get('ticket_id')}",
                f"Category Name : {query_doc.get('category_name')}",
                f"Title : {query_doc.get('title')}",
                f"Description : {query_doc.get('description')}",
                f"Status : {query_doc.get('status')}",
                f"Assigned Counselor Name : "
                f"{query_doc.get('assigned_counselor_name')}",
                f"Created At : {query_doc.get('created_at')}",
                f"Updated At : {query_doc.get('updated_at')}"
            ]
            y_points = [start_y_point, start_y_point + 20, start_y_point + 40,
                        start_y_point + 60, start_y_point + 80,
                        start_y_point + 100, start_y_point + 120,
                        start_y_point + 140]
            PDFHelper().add_content_in_pdf(
                pdf=pdf, x_point=60, y_point=start_y_point,
                content=f"{count}.")
            for y_point, content in zip(y_points, basic_content):
                PDFHelper().add_content_in_pdf(
                    pdf=pdf, x_point=80, y_point=y_point, content=content)
            start_y_point += 190
            if count % 3 == 0:
                pdf.showPage()
                start_y_point = 50
            count += 1
        PDFHelper().save_pdf(pdf=pdf)
        unique_filename = utility_obj.create_unique_filename(extension=".pdf")
        s3 = settings.s3_client
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        path = f"{utility_obj.get_university_name_s3_folder()}/{settings.s3_download_bucket_name}/{unique_filename}"
        with open("info.pdf", "rb") as f:
            s3.upload_fileobj(f, base_bucket,
                              path)
        rem_file = pathlib.Path("info.pdf")
        rem_file.unlink()
        s3.put_object_acl(
            ACL="public-read",
            Bucket=base_bucket,
            Key="%s" % path,
        )
        return {
            "pdf_url": f"https://{base_bucket}"
                       f".s3.{settings.region_name}.amazonaws.com/"
                       f"{path}"}
