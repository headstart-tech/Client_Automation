"""
This file contain class and functions related to pdf configuration
"""
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


class PDFHelper:
    """
    Contain functions related to pdf configuration
    """

    def pdf_initial_configuration(self, pagesize=None):
        """
        PDF Initial Configuration
        * :param pagesize description="Dimension of pdf page" example=(x, y):
        * :return pdf object:
        """
        pdf = canvas.Canvas("info.pdf", pagesize=pagesize, bottomup=0)
        pdf.setFillColorRGB(1, 0, 0)
        return pdf

    def set_pdf_heading(self, pdf, heading_font_size, x_point, y_point, page_heading):
        """
        Set Heading of PDF Page
        * :param pdf description="PDF object for configure pdf":
        * :param heading_font_size description="Font size of paf page heading":
        * :param x_point description="X-axis co-ordinate point":
        * :param y_point description="Y-axis co-ordinate point":
        * :param page_heading description="Page heading of pdf":
        * :return Write heading in pdf page and add horizontal line below heading for divide heading and content section:
        """
        pdf.setFont("Helvetica-Bold", heading_font_size)
        pdf.drawCentredString(x_point, y_point, page_heading)

    def set_section_heading_and_its_content_font_and_color(
            self, pdf,
            section_heading_font_size,
            x_point,
            y_point,
            section_heading,
            section_content_font_size,
    ):
        """
        Set Font and Color for Section of PDF Page
        * :param pdf description="PDF object for configure pdf":
        * :param section_heading_font_size description="Font size of section heading":
        * :param x_point description="X-axis co-ordinate point":
        * :param y_point description="Y-axis co-ordinate point":
        * :param section_heading description="Name of section heading":
        * :param section_content_font_size description="Font size of section content":
        * :return Write section heading:
        """
        pdf.setFont("Helvetica", section_heading_font_size)
        pdf.setFillColor(HexColor("#FF8C00"))
        pdf.drawCentredString(x_point, y_point, section_heading)
        pdf.setFont("Helvetica", section_content_font_size)
        pdf.setFillColorRGB(0, 0, 0)

    def add_content_in_pdf(self, pdf, x_point, y_point, content):
        """
        Add Content in PDF
        * :param pdf description="PDF object for configure pdf":
        * :param x_point description="X-axis co-ordinate point":
        * :param y_point description="Y-axis co-ordinate point":
        * :param content description="Content which we want to add in pdf":
        """
        pdf.drawString(x_point, y_point, content)

    def add_content_at_center_in_pdf(self, pdf, x_point, y_point, content):
        """
        Add Content at Center in PDF
        * :param pdf description="PDF object for configure pdf":
        * :param x_point description="X-axis co-ordinate point":
        * :param y_point description="Y-axis co-ordinate point":
        * :param content description="Content which we want to add in pdf":
        """
        pdf.drawCentredString(x_point, y_point, content)

    def add_line_in_pdf(self, pdf, x1_point, y1_point, x2_point, y2_point):
        """
        Add line in pdf draw from (x1,y1) to (x2,y2) (with color, thickness and other attributes determined by the current graphics state)
        """
        pdf.line(x1_point, y1_point, x2_point, y2_point)

    def save_pdf(self, pdf):
        """
        Save PDF
        * :param pdf description="PDF object for configure pdf":
        """
        pdf.showPage()
        pdf.save()
