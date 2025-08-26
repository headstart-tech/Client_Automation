"""
This file contain class and functions related to student application
"""
from bson import ObjectId

from app.core.log_config import get_logger
from app.core.utils import utility_obj, settings
from app.database.database_sync import DatabaseConfigurationSync
from app.helpers.report.pdf_configuration import PDFHelper

logger = get_logger(name=__name__)


class StudentApplicationActivity:
    """
    Contain functions related to student application activity
    """

    def section_divide_design_in_application_pdf(self, pdf):
        """
        Design for separate each section of pdf
        """
        y_points = [280, 390, 575, 810, 940, 1355, 2455]
        for y_point in y_points:
            PDFHelper().add_content_at_center_in_pdf(
                pdf=pdf, x_point=300, y_point=y_point, content="x---x---x"
            )

    def add_lines_in_application_pdf(self, pdf):
        """
        Add lines in the PDF
        """
        x1_points = [5, 95, 330, 400, 470, 50]
        y1_points = [65, 1990, 1990, 1990, 1990, 2035]
        x2_points = [605, 95, 330, 400, 470, 550]
        y2_points = [65, 2210, 2210, 2210, 2210, 2035]
        for x1_point, y1_point, x2_point, y2_point in zip(
                x1_points, y1_points, x2_points, y2_points
        ):
            PDFHelper().add_line_in_pdf(
                pdf=pdf,
                x1_point=x1_point,
                y1_point=y1_point,
                x2_point=x2_point,
                y2_point=y2_point,
            )

    def add_basic_details_in_application_pdf(self, pdf, application):
        """
        Add application basic details in the PDF
        """
        course = DatabaseConfigurationSync().course_collection.find_one(
            {"_id": ObjectId(str(application.get("course_id")))}
        )
        application_name = (
            f"{course.get('course_name')} in {application.get('spec_name1')}"
            if (application.get("spec_name1") != "" and application.get(
                "spec_name1"))
            else f"{course.get('course_name')} Program"
        )
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=95,
            section_heading="Basic Details",
            section_content_font_size=11,
        )
        basic_content = [
            f"Application ID : {str(application.get('_id'))}",
            f"Custom Application ID : {application.get('custom_application_id') if application.get('custom_application_id') else 'NA'}",
            f"Application Name : {application_name}",
            f"Application Fee : {course.get('fees') if course.get('fees') else 'NA'}",
            f"Application Payment Status : {'Paid' if application.get('payment_info', {}).get('status') == 'captured' else 'Not Paid'}",
            f"Application Submitted On : {utility_obj.get_local_time(application.get('last_updated_time'))}",
        ]
        y_points = [125, 150, 175, 200, 225, 250]
        for y_point, content in zip(y_points, basic_content):
            PDFHelper().add_content_in_pdf(pdf=pdf, x_point=80, y_point=y_point, content=content)

    def add_specialization_details_in_application_pdf(self, pdf, application):
        """
        Add course specialization details in the PDF
        """
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=310,
            section_heading="Specialization Details",
            section_content_font_size=11,
        )
        specialization_details = [
            f"Main Specialization : {application.get('spec_name1') if application.get('spec_name1') else 'NA'}",
            f"Secondary Specialization : {application.get('spec_name2') if application.get('spec_name2') else 'NA'}",
        ]
        y_points = [335, 360]
        for y_point, content in zip(y_points, specialization_details):
            PDFHelper().add_content_in_pdf(pdf=pdf, x_point=80, y_point=y_point, content=content)

    def add_student_basic_details_in_application_pdf(self, pdf, student):
        """
        Add student basic details in the PDF
        """
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=420,
            section_heading="Student Basic Details",
            section_content_font_size=11,
        )
        student_basic_details = [
            f"Name : {utility_obj.name_can(student.get('basic_details'))}",
            f"Email ID : {student.get('basic_details', {}).get('email')}",
            f"Mobile No : {student.get('basic_details', {}).get('mobile_number')}",
            "Birth Date : NA",
            "Admission Year : NA",
            "Gender : NA",
            "Nationality : NA",
            "Category : NA",
            "Is Disable? : NA",
            "Name of Disability : NA",
        ]
        x_points = [80, 350, 80, 350, 80, 350, 80, 350, 80, 350]
        y_points = [445, 445, 470, 470, 495, 495, 520, 520, 545, 545]
        for x_point, y_point, content in zip(x_points, y_points, student_basic_details):
            PDFHelper().add_content_in_pdf(
                pdf=pdf, x_point=x_point, y_point=y_point, content=content
            )

    def add_student_parent_details_in_application_pdf(self, pdf, student_secondary_details):
        """
        Add student parent details in the PDF
        """
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=605,
            section_heading="Student Parents Details",
            section_content_font_size=13,
        )
        PDFHelper().add_content_in_pdf(
            pdf=pdf,
            x_point=80,
            y_point=630,
            content=f"Family Annual Income : {student_secondary_details.get('family_annual_income')}",
        )
        PDFHelper().add_content_in_pdf(
            pdf=pdf, x_point=80, y_point=660, content="Father Details :"
        )
        PDFHelper().add_content_in_pdf(
            pdf=pdf, x_point=80, y_point=730, content="Mother Details :"
        )
        pdf.setFont("Helvetica", 11)
        student_parent_details = [
            f"Name : {student_secondary_details.get('parents_details', {}).get('father_details', {}).get('salutation')} {student_secondary_details.get('parents_details', {}).get('father_details', {}).get('name')}",
            f"Email ID : {student_secondary_details.get('parents_details', {}).get('father_details', {}).get('email') if student_secondary_details.get('parents_details', {}).get('father_details', {}).get('email') else 'NA'}",
            f"Mobile No : {student_secondary_details.get('parents_details', {}).get('father_details', {}).get('mobile_number') if student_secondary_details.get('parents_details', {}).get('father_details', {}).get('mobile_number') else 'NA'}",
            f"Name : {student_secondary_details.get('parents_details', {}).get('mother_details', {}).get('salutation')} {student_secondary_details.get('parents_details', {}).get('mother_details', {}).get('name')}",
            f"Email ID : {student_secondary_details.get('parents_details', {}).get('mother_details', {}).get('email') if student_secondary_details.get('parents_details', {}).get('mother_details', {}).get('email') else 'NA'}",
            f"Mobile No : {student_secondary_details.get('parents_details', {}).get('mother_details', {}).get('mobile_number') if student_secondary_details.get('parents_details', {}).get('mother_details', {}).get('mobile_number') else 'NA'}",
        ]
        x_points = [100, 100, 350, 100, 100, 350]
        y_points = [685, 705, 705, 755, 780, 780]
        for x_point, y_point, content in zip(x_points, y_points, student_parent_details):
            PDFHelper().add_content_in_pdf(
                pdf=pdf, x_point=x_point, y_point=y_point, content=content
            )

    def add_guardian_details_in_application_pdf(self, pdf, student_secondary_details):
        """
        Add guardian details in the PDF
        * :param pdf description="PDF object for configure pdf":
        * :param student_secondary_details description="Student secondary details":
        """
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=840,
            section_heading="Student Parent Details",
            section_content_font_size=11,
        )
        guardian_details = [
            f"Name : {student_secondary_details.get('guardian_details', {}).get('salutation')} {student_secondary_details.get('guardian_details', {}).get('name')}",
            f"Email ID : {student_secondary_details.get('guardian_details', {}).get('email')}",
            f"Mobile No : {student_secondary_details.get('guardian_details', {}).get('mobile_number')}",
            f"Occupation : {student_secondary_details.get('guardian_details', {}).get('occupation')}",
            f"Designation : {student_secondary_details.get('guardian_details', {}).get('designation')}",
            f"Relationship With Student : {student_secondary_details.get('guardian_details', {}).get('relationship_with_student')}",
        ]
        x_points = [80, 350, 80, 350, 80, 350]
        y_points = [865, 865, 890, 890, 910, 910]
        for x_point, y_point, content in zip(x_points, y_points, guardian_details):
            PDFHelper().add_content_in_pdf(
                pdf=pdf, x_point=x_point, y_point=y_point, content=content
            )

    def add_student_address_details_in_application_pdf(self, pdf, student):
        """
        Add student address details in the PDF
        * :param pdf description="PDF object for configure pdf":
        * :param student description="Student details":
        """
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=970,
            section_heading="Address Details",
            section_content_font_size=13,
        )
        PDFHelper().add_content_in_pdf(
            pdf=pdf, x_point=80, y_point=995, content="Communication Address :"
        )
        PDFHelper().add_content_in_pdf(
            pdf=pdf, x_point=80, y_point=1175, content="Permanent Address :"
        )
        pdf.setFont("Helvetica", 11)
        student_address_details = [
            f"Address Line 1 : {student.get('address_details', {}).get('communication_address', {}).get('address_line1')}",
            f"Address Line 2 : {student.get('address_details', {}).get('communication_address', {}).get('address_line2')}",
            f"Pin Code : {student.get('address_details', {}).get('communication_address', {}).get('pincode')}",
            f"City : {student.get('address_details', {}).get('communication_address', {}).get('city', {}).get('city_name')}",
            f"State : {student.get('address_details', {}).get('communication_address', {}).get('state', {}).get('state_name')}",
            f"Country : {student.get('address_details', {}).get('communication_address', {}).get('country', {}).get('country_name')}",
            f"Address Line 2 : {student.get('address_details', {}).get('permanent_address', {}).get('address_line1') if student.get('address_details', {}).get('permanent_address') else student.get('address_details', {}).get('communication_address', {}).get('address_line1')}",
            f"Address Line 2 : {student.get('address_details', {}).get('permanent_address', {}).get('address_line2') if student.get('address_details', {}).get('permanent_address') else student.get('address_details', {}).get('communication_address', {}).get('address_line2')}",
            f"Pin Code : {student.get('address_details', {}).get('permanent_address', {}).get('pincode') if student.get('address_details', {}).get('permanent_address') else student.get('address_details', {}).get('communication_address', {}).get('pincode')}",
            f"City : {student.get('address_details', {}).get('permanent_address', {}).get('city', {}).get('city_name') if student.get('address_details', {}).get('permanent_address') else student.get('address_details', {}).get('communication_address', {}).get('city', {}).get('city_name')}",
            f"State : {student.get('address_details', {}).get('permanent_address', {}).get('state', {}).get('state_name') if student.get('address_details', {}).get('permanent_address') else student.get('address_details', {}).get('communication_address', {}).get('state', {}).get('state_name')}",
            f"Country : {student.get('address_details', {}).get('permanent_address', {}).get('country', {}).get('country_name') if student.get('address_details', {}).get('permanent_address') else student.get('address_details', {}).get('communication_address', {}).get('country', {}).get('country_name')}",
        ]
        x_points = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        y_points = [1020, 1045, 1070, 1095, 1120, 1145, 1200, 1225, 1250, 1275, 1300, 1325]
        for x_point, y_point, content in zip(x_points, y_points, student_address_details):
            PDFHelper().add_content_in_pdf(
                pdf=pdf, x_point=x_point, y_point=y_point, content=content
            )

    def add_education_details_in_application_pdf(self, pdf, student_secondary_details):
        """
        Add student education details in the PDF
        * :param pdf description="PDF object for configure pdf":
        * :param student_secondary_details description="Student secondary details":
        """
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=1385,
            section_heading="Educational Details",
            section_content_font_size=13,
        )
        section_names = [
            "Tenth School Details :",
            "Tenth Subject Wise Details :",
            "Inter School Details :",
            "Inter Subject Wise Details :",
            "Graduation Details :",
        ]
        y_points = [1410, 1615, 1730, 1960, 2250]
        for y_point, content in zip(y_points, section_names):
            PDFHelper().add_content_in_pdf(pdf=pdf, x_point=80, y_point=y_point, content=content)
        pdf.setFont("Helvetica", 11)
        education_details = [
            f"School Name : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('school_name')}",
            f"Board Name : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('board')}",
            f"Year of Passing : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('year_of_passing')}",
            f"Marking Scheme : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('marking_scheme')}",
            f"Obtained CGPA : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('obtained_cgpa')}",
            f"Max Marks : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('max_marks')}",
            f"Registration Number : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_registration_number')}",
            f"English : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('english') if student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('english') else 'NA'}",
            f"Math : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('maths') if student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('maths') else 'NA'}",
            f"Science : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('science') if student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('science') else 'NA'}",
            f"Social Science : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('social_science') if student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('social_science') else 'NA'}",
            f"Language : {student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('language') if student_secondary_details.get('education_details', {}).get('tenth_school_details', {}).get('tenth_subject_wise_details', {}).get('language') else 'NA'}",
            f"School Name : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('school_name') if student_secondary_details.get('education_details', {}).get('inter_school_details') else 'NA'}",
            f"Board Name : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('board') if student_secondary_details.get('education_details', {}).get('inter_school_details') else 'NA'}",
            f"Stream : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('stream') if student_secondary_details.get('education_details', {}).get('inter_school_details', {}) else 'NA'}",
            f"Year of Passing : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('year_of_passing') if student_secondary_details.get('education_details', {}).get('inter_school_details') else 'NA'}",
            f"Marking Scheme : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('marking_scheme') if student_secondary_details.get('education_details', {}).get('inter_school_details') else 'NA'}",
            f"Obtained CGPA : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('obtained_cgpa') if student_secondary_details.get('education_details', {}).get('inter_school_details') else 'NA'}",
            f"Max Marks : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('max_mark') if student_secondary_details.get('education_details', {}).get('inter_school_details') else 'NA'}",
            f"Registration Number : {student_secondary_details.get('education_details', {}).get('inter_school_details', {}).get('inter_registration_number') if student_secondary_details.get('education_details', {}).get('inter_school_details') else 'NA'}",
            f"Institute Name : {student_secondary_details.get('education_details', {}).get('graduation_details', {}).get('name_of_institute') if student_secondary_details.get('education_details', {}).get('graduation_details') else 'NA'}",
            f"Course Name : {student_secondary_details.get('education_details', {}).get('graduation_details', {}).get('ug_course_name') if student_secondary_details.get('education_details', {}).get('graduation_details') else 'NA'}",
            f"Year of Completion : {student_secondary_details.get('education_details', {}).get('graduation_details', {}).get('year_of_passing') if student_secondary_details.get('education_details', {}).get('graduation_details') else 'NA'}",
            f"Marking Scheme : {student_secondary_details.get('education_details', {}).get('graduation_details', {}).get('marking_scheme') if student_secondary_details.get('education_details', {}).get('graduation_details') else 'NA'}",
            f"Obtained Cgpa : {str(student_secondary_details.get('education_details', {}).get('graduation_details', {}).get('obtained_cgpa')) if student_secondary_details.get('education_details', {}).get('graduation_details') else 'NA'}",
            f"Aggregate Marks : {student_secondary_details.get('education_details', {}).get('graduation_details', {}).get('aggregate_mark') if student_secondary_details.get('education_details', {}).get('graduation_details') else 'NA'}",
            f"Registration Number : {student_secondary_details.get('education_details', {}).get('graduation_details', {}).get('ug_registration_number') if student_secondary_details.get('education_details', {}).get('graduation_details') else 'NA'}",
        ]
        x_points = [
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            250,
            400,
            100,
            250,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
        ]
        y_points = [
            1435,
            1460,
            1485,
            1510,
            1535,
            1560,
            1585,
            1645,
            1645,
            1645,
            1670,
            1670,
            1755,
            1780,
            1805,
            1830,
            1855,
            1880,
            1905,
            1930,
            2275,
            2300,
            2325,
            2350,
            2375,
            2400,
            2425,
        ]
        for x_point, y_point, content in zip(x_points, y_points, education_details):
            PDFHelper().add_content_in_pdf(
                pdf=pdf, x_point=x_point, y_point=y_point, content=content
            )

        pdf.roundRect(50, 1990, 500, 220, 10)
        table_data = [
            "S.No.",
            "Subject Name",
            "Max",
            "Marks",
            "Obtained",
            "Marks",
            "Percentage",
            "1",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}])[0].get("subject_name")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}])[0].get("max_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}])[0].get("obtained_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}])[0].get("percentage")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            "2",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}])[1].get("subject_name")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}])[1].get("max_marks")
            if student_secondary_details.get("education_details")
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}])[1].get("obtained_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}])[1].get("percentage")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            "3",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}])[2].get("subject_name")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}])[2]["max_marks"]
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}])[2].get("obtained_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}])[2].get("percentage")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            "4",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}])[3].get("subject_name")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}])[3].get("max_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}])[3].get("obtained_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}])[3].get("percentage")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            "5",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}, {}])[4].get("subject_name")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}, {}])[4].get("max_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}, {}])[4].get("obtained_marks")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
            student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details", [{}, {}, {}, {}, {}])[4].get("percentage")
            if student_secondary_details.get("education_details", {})
            .get("inter_school_details", {})
            .get("inter_subject_wise_details")
            else "NA",
        ]
        x_points = [
            75,
            210,
            360,
            360,
            430,
            430,
            510,
            75,
            210,
            360,
            430,
            510,
            75,
            210,
            360,
            430,
            510,
            75,
            210,
            360,
            430,
            510,
            75,
            210,
            360,
            430,
            510,
            75,
            210,
            360,
            430,
            510,
        ]
        y_points = [
            2010,
            2010,
            2010,
            2025,
            2010,
            2025,
            2010,
            2060,
            2060,
            2060,
            2060,
            2060,
            2090,
            2090,
            2090,
            2090,
            2090,
            2120,
            2120,
            2120,
            2120,
            2120,
            2150,
            2150,
            2150,
            2150,
            2150,
            2180,
            2180,
            2180,
            2180,
            2180,
        ]

        for x_point, y_point, content in zip(x_points, y_points, table_data):
            if content is None:
                content = "NA"
            PDFHelper().add_content_at_center_in_pdf(
                pdf=pdf, x_point=x_point, y_point=y_point, content=content
            )

    def add_attachment_details_in_application_pdf(self, pdf, student_secondary_details):
        """
        Add student attached document details in the application PDF
        """
        season_year = utility_obj.get_year_based_on_season()
        PDFHelper().set_section_heading_and_its_content_font_and_color(
            pdf=pdf,
            section_heading_font_size=17,
            x_point=300,
            y_point=2485,
            section_heading="Attachment Details",
            section_content_font_size=13,
        )
        section_names = [
            "Tenth Attachment :",
            "Inter Attachment :",
            "Graduation Attachment :",
        ]
        y_points = [2525, 2580, 2635]
        for y_point, content in zip(y_points, section_names):
            PDFHelper().add_content_in_pdf(pdf=pdf, x_point=80, y_point=y_point, content=content)
        pdf.setFont("Helvetica", 7)
        attachments = student_secondary_details.get("attachments", {})
        attachment_details = [
            "UPLOADED"
            if attachments.get("tenth", {}).get('file_s3_url')
            else "NOT-UPLOADED",
            "UPLOADED"
            if attachments.get("inter", {}).get('file_s3_url')
            else "NOT-UPLOADED",
            "UPLOADED"
            if attachments.get("graduation", {}).get('file_s3_url')
            else "NOT-UPLOADED",
        ]
        y_points = [2550, 2605, 2660]
        for y_point, content in zip(y_points, attachment_details):
            PDFHelper().add_content_in_pdf(pdf=pdf, x_point=50, y_point=y_point, content=content)
