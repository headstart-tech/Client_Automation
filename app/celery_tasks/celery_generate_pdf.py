"""
This class implements the following methods to create a pdf file
"""

import pathlib
from datetime import datetime

from bson import ObjectId

from app.background_task.student_application import StudentApplicationActivity
from app.core.celery_app import celery_app
from app.core.reset_credentials import Reset_the_settings
from app.core.utils import utility_obj, settings, logger
from app.database.database_sync import DatabaseConfigurationSync
from app.helpers.report.pdf_configuration import PDFHelper


class generate_pdf_config:
    """A class to generate PDF configuration files for a given project"""

    @staticmethod
    @celery_app.task(ignore_result=True)
    def generate_application_pdf(student, application, season=None, college_id=None):
        """
        Generate PDF which contain application details
        """
        if college_id is not None:
            Reset_the_settings().check_college_mapped(college_id=college_id)
        season_year = utility_obj.get_year_based_on_season(season)
        student_secondary_details = (
            DatabaseConfigurationSync().studentSecondaryDetails.find_one(
                {"student_id": ObjectId(str(student.get("_id")))}
            )
        )
        pdf = PDFHelper().pdf_initial_configuration(pagesize=(610, 2700))
        PDFHelper().set_pdf_heading(
            pdf=pdf,
            heading_font_size=20,
            x_point=300,
            y_point=50,
            page_heading="Application Form Details",
        )
        pdf.setFont("Helvetica", 10)
        pdf.setFillColorRGB(0, 0, 0)
        PDFHelper().add_content_in_pdf(
            pdf=pdf,
            x_point=380,
            y_point=20,
            content=f"Report Generated on : "
            f"{utility_obj.get_local_time(datetime.utcnow())}",
        )
        StudentApplicationActivity().add_basic_details_in_application_pdf(
            pdf=pdf, application=application
        )
        StudentApplicationActivity().add_specialization_details_in_application_pdf(
            pdf=pdf, application=application
        )
        StudentApplicationActivity().add_student_basic_details_in_application_pdf(
            pdf=pdf, student=student
        )
        StudentApplicationActivity().add_student_parent_details_in_application_pdf(
            pdf=pdf, student_secondary_details=student_secondary_details
        )
        StudentApplicationActivity().add_guardian_details_in_application_pdf(
            pdf=pdf, student_secondary_details=student_secondary_details
        )
        StudentApplicationActivity().add_student_address_details_in_application_pdf(
            pdf=pdf, student=student
        )
        StudentApplicationActivity().add_education_details_in_application_pdf(
            pdf=pdf, student_secondary_details=student_secondary_details
        )
        StudentApplicationActivity().add_attachment_details_in_application_pdf(
            pdf=pdf, student_secondary_details=student_secondary_details
        )
        StudentApplicationActivity().add_lines_in_application_pdf(pdf=pdf)
        pdf.setFont("Helvetica", 11)
        StudentApplicationActivity().section_divide_design_in_application_pdf(pdf=pdf)
        PDFHelper().save_pdf(pdf=pdf)
        path = f"{utility_obj.get_university_name_s3_folder()}/{season_year}/{settings.s3_student_documents_bucket_name}/{student.get('_id')}/application/"
        unique_filename = utility_obj.create_unique_filename(extension=".pdf")
        s3 = settings.s3_client
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        with open("info.pdf", "rb") as f:
            s3.upload_fileobj(f, base_bucket, f"{path}{unique_filename}")
        rem_file = pathlib.Path("info.pdf")
        rem_file.unlink()
        s3.put_object_acl(
            ACL="public-read",
            Bucket=base_bucket,
            Key= f"{path}{unique_filename}"
        )
        DatabaseConfigurationSync().studentApplicationForms.update_one(
            {"_id": ObjectId(str(application.get("_id")))},
            {
                "$set": {
                    "application_download_url": f"https://{base_bucket}.s3."
                    f"{settings.region_name}.amazonaws.com/"
                    f"{path}{unique_filename}"
                }
            },
        )
