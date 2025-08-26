"""
This file is used to extract document information using amazon textract
"""
import datetime
import re
from collections import defaultdict
from pathlib import Path
from pathlib import PurePath

import boto3
from bson import ObjectId
from word2number import w2n

from app.core.celery_app import celery_app
from app.core.log_config import get_logger
from app.core.utils import Utility, utility_obj
from app.core.utils import settings
from app.database.database_sync import DatabaseConfigurationSync

logger = get_logger(name=__name__)


def get_subjects(student_id, document_name):
    """
        get subjects the student given in the application form

        Params:
            student_id ( string) : Unique id of student
            document_name ( string) : Document name like inter,grad,tenth

        Returns:
            None if no subjects are found
            Subjects (list) : if subjects are found
    """
    stu_doc = DatabaseConfigurationSync().studentSecondaryDetails.find_one(
        {'student_id': ObjectId(student_id)})
    if (edu := stu_doc.get("education_details")) is None:
        return None
    if (school := edu.get(f"{document_name}_school_details")) is None:
        return None
    if (marks := school.get(f"{document_name}_subject_wise_details")) is None:
        return None
    marks = list(marks)
    return [sub.get("subject_name", "").upper() for sub in marks]


def custom_sort(item):
    """
        This function is used to custom sort the given list. If list contains both string and numbers
        first, it will sort strings and then sort the numbers

        Params:
            item(int/str)

        Returns:
            0 if str
            1 if int
        """
    if isinstance(item, int):
        return 1, item
    else:
        return 0, item


def marks_from_list(sub_marks):
    """
    from the given list of all subjects select the correct mark ignoring max marks

    Params:
        sub_marks(dicts) : here the key is subject name and the value is list of
        list of possible marks and list of their confidence.

    Returns:
        sub_marks(dict) : here the key is subject name and value is (int) mark
        confidence_sub(dict) : here  the key is the subject name and value is (int) confidence
    """

    confidence_sub = {}
    for subject, values in sub_marks.items():
        marks = values[0]
        confidence = values[1]
        marks_length = len(marks)
        sorted_indices = sorted(range(marks_length),
                                key=lambda i: custom_sort(marks[i]))
        marks = [marks[i] for i in sorted_indices]
        confidence = [confidence[i] for i in sorted_indices]
        if marks is None:
            sub_marks[subject] = ""
            confidence_sub.update({subject: ""})
        elif marks[marks_length - 1] in [50, 75]:
            sub_marks[subject] = ""
            confidence_sub.update({subject: ""})
        elif marks[marks_length - 1] != 100:
            sub_marks[subject] = marks[marks_length - 1]
            confidence_sub.update({subject: confidence[marks_length - 1]})
        else:
            if marks[marks_length - 1] == 100:
                try:
                    sub_marks[subject] = marks[marks_length - 2]
                    confidence_sub.update(
                        {subject: confidence[marks_length - 2]})
                except IndexError:
                    sub_marks[subject] = marks[marks_length - 1]
                    confidence_sub.update(
                        {subject: confidence[marks_length - 1]})

    return sub_marks, confidence_sub


def extract_marks_from_table(response, student_id, document_name):
    """
        extract list of possible marks of each subject from given response

        Params:
             response (dict) : the response generated from aws textract
             student_id (str) : unique student id
             document_name (str) : document name like tenth,inter,grad

        Returns:
            marks (dict) : marks of the student
            confidence (dict) : confidence of the marks extracted
    """
    subject_marks = {}
    blocks_dict = {block['Id']: block for block in response['Blocks']}
    subjects = get_subjects(student_id, document_name)
    current_subject = None
    current_values = []
    confidence_values = []
    row_end = False
    marks = {}
    confidence = {}

    if subjects:
        for table in response['Blocks']:
            if table['BlockType'] == 'TABLE':
                max_column_index = -1
                for relationship in table['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for cell_id in relationship['Ids']:
                            cell = blocks_dict[cell_id]
                            if 'ColumnIndex' in cell:
                                column_index = cell['ColumnIndex']
                                max_column_index = max(max_column_index,
                                                       column_index)

                            if 'Relationships' in cell:
                                for cell_relation in cell['Relationships']:
                                    if cell_relation['Type'] == 'CHILD':
                                        for cell_child_id in cell_relation[
                                            'Ids']:
                                            cell_child = blocks_dict[
                                                cell_child_id]
                                            if cell_child[
                                                'BlockType'] == 'WORD':
                                                text = cell_child[
                                                    'Text'].strip().upper()
                                                confidence = cell_child[
                                                    'Confidence']
                                                if text in subjects:
                                                    row_end = False
                                                    if current_subject:
                                                        subject_marks[
                                                            current_subject] = [
                                                            current_values,
                                                            confidence_values]
                                                        current_values = []
                                                        confidence_values = []
                                                    current_subject = text
                                                elif text and current_subject and not row_end:
                                                    try:
                                                        value = int(text)
                                                        current_values.append(
                                                            value)
                                                        confidence_values.append(
                                                            int(confidence))
                                                    except ValueError:
                                                        if len(text) == 2:
                                                            current_values.append(
                                                                text)
                                                            confidence_values.append(
                                                                int(confidence))
                                                    if column_index == max_column_index:
                                                        row_end = True

        if current_subject:
            subject_marks[current_subject] = [current_values,
                                              confidence_values]
        marks, confidence = marks_from_list(subject_marks)
    return marks, confidence


def get_map(file_name):
    """
    gets keys and values pairs in the function

    Params:
        file_name(string): Name of the file to extract the information

    Returns:
        key_map (dict): dict of all keys,
        value_map (dict): dict of all keys,
        block_map (dict): dict of all blocks in document,
        top_heading (str) : heading of the document,
        heading_confidence (int) : Accuracy of heading,
        year (int) : issue year of uploaded document,
        year_confidence (int) : Accuracy of year
    """
    try:
        with open(file_name, 'rb') as file:
            img_test = file.read()
            document_bytes = bytearray(img_test)
        client = boto3.client('textract',
                              region_name=settings.textract_aws_region_name,
                              aws_access_key_id=settings.textract_aws_access_key_id,
                              aws_secret_access_key=settings.textract_aws_secret_access_key)
        response = client.analyze_document(Document={'Bytes': document_bytes},
                                           FeatureTypes=['FORMS', 'TABLES'])
        blocks = response['Blocks']
        key_map = {}
        value_map = {}
        block_map = {}
        for block in blocks:
            block_id = block['Id']
            block_map[block_id] = block
            if block['BlockType'] == "KEY_VALUE_SET":
                if 'KEY' in block['EntityTypes']:
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block
        top_heading = ''
        heading_found = False
        heading_confidence = "N/A"
        year_confidence = "N/A"
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE' and 'Text' in item and item[
                'Confidence'] >= 90 and item['Text'].isascii() \
                    and not any(char.isdigit() for char in item['Text']):
                if not heading_found:
                    top_heading = item['Text']
                    heading_found = True
                else:
                    if item['Geometry']['BoundingBox']['Top'] - \
                            item['Geometry']['BoundingBox']['Height'] > 0.02:
                        break
                    top_heading += ' ' + item['Text']
                heading_confidence = item['Confidence']
        top_heading = top_heading.strip()
        year = ""
        pattern = r"\b\d{4}\b"
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE' and 'Text' in item and item[
                'Text'].isascii():
                match = re.search(pattern, item['Text'])
                if match:
                    year = match.group()
                    year_confidence = item['Confidence']
                    break
        return key_map, value_map, block_map, top_heading, \
            int(heading_confidence), year, int(year_confidence), response
    except Exception:
        raise Exception


def get_relationship(key_map, value_map, block_map):
    """
        gives relation between keys and values

        Params:
            key_map (dict) : all key items
            value_map(dict) : all value items,
            block_map(dict): all blocks of extracted data

        Returns:
            kvs (dict): key value pairs,
            confidence (dict): key confidence pairs
        """
    kvs = defaultdict(list)
    confidence = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key, key_confidence = get_text(key_block, block_map)
        val, val_confidence = get_text(value_block, block_map)
        kvs[key].append(val)
        confidence[key].append(val_confidence)
    return kvs, confidence


def find_value_block(key_block, value_map):
    """
        this is used to find the value block

        Params:
            key_block (dict) :keys list
            value_map (dict): values list

        Returns:
            value_block
        """
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block


def get_text(result, blocks_map):
    """
            gives text and confidence of given block

            Params:
                result (dict) :the text extracted
                blocks_map (dict) : all the blocks extracted

            Returns:
                text (str) : text of particular block,
                confidence (str) : confidence of particular block
            """
    text = ''
    confidence = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text = text + " " + word['Text']
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += ' X '
                    confidence = int(word['Confidence'])
    return text, confidence


def search_value(kvs, search_key):
    """
        to search the particular key in dictionary of key value fields

        Params:
            kvs (dict) : dict of keys and values
            search_key (str): key to be searched

        Returns:
            value (str) :value of particular key
    """
    for key, value in kvs.items():
        if re.search(search_key, key, re.IGNORECASE):
            return value[0]
    return None


def confidence_value(confidence, search_key):
    """
        to search the particular key in dictionary of key confidence dictionary

        Params:
            confidence (dict) :dict of keys and their confidence
            search_key (str) :  the key to be searched

        Returns:
            value (int) : confidence value of given key
    """
    for key, value in confidence.items():
        if re.search(search_key, key, re.IGNORECASE):
            return value[0]
    return None


def candidate(kvs, confidencelist):
    """
        this is used to get the name from document

        Params:
            kvs (dict) : dict of key and values,
            confidencelist (dict) : dict of key and their confidence

        Returns:
            confidence , val:  confidence and val of name field
    """
    confidence = "N/A"
    for field_name in ["candidate", "certify", "certify that", "certified", "certified to", "name"]:
        val = search_value(kvs, field_name)
        if val is not None:
            confidence = confidence_value(confidencelist, field_name)
            return confidence, val
    return confidence, val


def markingsceme(result):
    """
        this is used to get the marking scheme

        Params:
            result (str) : the result of student is passed

        Returns:
            confidence , val:  confidence and val of marking scheme
    """
    try:
        if result is None:
            pass
        else:
            result = result.strip()
        if result is None:
            return "N/A", "null"
        elif result.isalpha():
            return 99, "Grades"
        elif float(result) <= 10.0:
            return 99, "CGPA"
        elif 100 > float(result) > 25:
            return 99, "Percentage"
        elif int(result) < 100 and int(result) > 25:
            return 99, "Percentage"
        else:
            return "N/A", "N/A"
    except TypeError as e:
        return "N/A", "null"
    except Exception as e:
        return "N/A", "null"


def points(kvs, confidencelist):
    """
        this is used to get the result from document

        Params:
            kvs (dict) : dict of key and values,
            confidencelist (dict) : dict of key and their confidence

        Returns:
            confidence , val:  confidence and val of result field
    """
    try:
        confidence = "N/A"
        for field_name in ["percent", "percentage", "points", "cgpa", "total",
                           "grade", "aggregate", "marks", "result"]:
            val = search_value(kvs, field_name)
            if val is not None:
                confidence = confidence_value(confidencelist, field_name)
                return confidence, val
    except Exception as e:
        return "N/A", "N/A"
    return confidence, val


def rollno(kvs, confidencelist):
    """
        this is used to get the roll_no from document

        Params:
            kvs (dict) : dict of key and values,
            confidencelist (dict) : dict of key and their confidence

        Returns:
            confidence , val:  confidence and val of rollno field
    """
    confidence = "N/A"
    for field_name in ["Register No", "Roll number", "RollNumber", "Roll No.",
                       "Roll", "id", "Unique"]:
        val = search_value(kvs, field_name)
        if val is not None:
            confidence = confidence_value(confidencelist, field_name)
            return confidence, val
    return confidence, val


def dob(kvs, confidencelist):
    """
        this is used to get the date of birth from document

        Params:
            kvs (dict) : dict of key and values,
            confidencelist (dict) : dict of key and their confidence

        Returns:
            confidence , val:  confidence and val of date of birth field
    """
    confidence = "N/A"
    val = search_value(kvs, "DOB")
    if val is not None:
        confidence = confidence_value(confidencelist, "DOB")
        return confidence, val
    val = search_value(kvs, "Date of birth")
    if val is not None:
        confidence = confidence_value(confidencelist, "Date of birth")
        return confidence, val
    val = search_value(kvs, "Dateofbirth")
    if val is not None:
        confidence = confidence_value(confidencelist, "Dateofbirth")
        return confidence, val
    return confidence, val


def calculate_accuracy(confidences):
    """
        this is used to calculate the average accuracy of extracted information

        Params:
            confidences (dict) : list of all accuracies

        Returns:
            average_confidence (int) : average accuracy
     """
    valid_confidences = [c for c in confidences if
                         c is not None and c != 'N/A' and c != ""]
    if valid_confidences:
        average_confidence = sum(valid_confidences) / len(confidences)
        return round(average_confidence, 2)
    else:
        return "N/A"


def update_extracted_document_data(file_name, student_id, document_name,
                                         field_name):
    """
    Update extracted details of a document in the DB.

    Params:
        file_name (str): A name of a file.
        student_id (ObjectId): An unique id of a student.
        document_name (str): Name of a document.
        field_name (str): Name of a field.

    Returns: None
    """
    student = DatabaseConfigurationSync().studentSecondaryDetails.find_one(
        {'student_id': student_id})
    document = student.get("document_analysis", {})
    count = 0
    if document:
        doc = document.get(f"{field_name}_analysis")
        if doc:
            count = doc.get("count") + 1
    if count <= 3:
        DatabaseConfigurationSync().studentSecondaryDetails.update_one(
            {'student_id': student_id},
            {"$set": {f"document_analysis.{field_name}_analysis":
                          { "status": "In Progress",
                           "process_started_on": datetime.datetime.utcnow(),
                           "count": count
                           }}})
        try:
            key_map, value_map, block_map, heading, \
                heading_confidence, issueyear, issueyear_confidence, response = get_map(
                file_name)
        except Exception as e:
            DatabaseConfigurationSync().studentSecondaryDetails.update_one(
                {'student_id': student_id},
                {"$set": {f"document_analysis.{field_name}_analysis":
                              {"status": "Failed",
                               "process_finished_on": datetime.datetime.utcnow(),
                               "count": count
                               }}})
            logger.error(f"Error in text extraction: {e}")
            return {"error": f"An error occurred while extracting the text "
                             f"info {e} "}

        kvs, confidence = get_relationship(key_map, value_map, block_map)
        year = issueyear
        result_confidence, result = points(kvs, confidence)
        name_confidence, name = candidate(kvs, confidence)
        roll_confidence, roll = rollno(kvs, confidence)
        if result is not None:
            if ("/" in result):
                result = result.split("/")[0]
            if ((bool(re.match(r"(?=.*[a-zA-Z])[a-zA-Z0-9\s]+", result)))):
                match = re.search(r"\b\d+\b", result)
                if match:
                    result = match.group()
                else:
                    try:
                        number = w2n.word_to_num(result)
                        result = number
                    except ValueError:
                        result = None
        scheme_confidence, scheme = markingsceme(result)
        utility = Utility()
        result = utility.normalize_score(scheme, result)
        dateob_confidence, dateob = dob(kvs, confidence)
        if dateob is not None:
            match = re.search(r"\d{2}/\d{2}/\d{4}", dateob)
            if match:
                dateob = match.group()
        caste = search_value(kvs, "caste")
        caste_confidence = confidence_value(confidence, "caste")
        accuracy = calculate_accuracy(
            [heading_confidence, issueyear_confidence, scheme_confidence,
             result_confidence,
             roll_confidence, dateob_confidence, caste_confidence])
        updated_data = {"name": name,
                        "board": heading,
                        "year_of_passing": year,
                        "marking_scheme": scheme,
                        "obtained_cgpa": result,
                        "registration_number": roll,
                        "date_of_birth": dateob,
                        "caste": caste,
                        "name_accuracy": name_confidence,
                        "board_accuracy": heading_confidence,
                        "year_of_passing_accuracy": issueyear_confidence,
                        "marking_scheme_accuracy": scheme_confidence,
                        "obtained_cgpa_accuracy": result_confidence,
                        "registration_number_accuracy": roll_confidence,
                        "date_of_birth_accuracy": dateob_confidence,
                        "caste_accuracy": caste_confidence}
        if document_name == "inter":
            marks, marks_confidence = extract_marks_from_table(response,
                                                                     student_id,
                                                                     document_name)
            updated_data.update({"subject_wise_marks": marks,
                                 "subject_wise_confidence": marks_confidence
                                 })
        metadata = {
            "accuracy": accuracy,
            "processed_date":
                str(datetime.datetime.utcnow()).split(" ")[0],
            "processed_by": "AWS Textract"}
        DatabaseConfigurationSync().studentSecondaryDetails.find_one_and_update(
            {'student_id': student_id},
            {
                "$set": {
                    f"document_analysis.{field_name}_analysis.data": updated_data,
                    f"document_analysis.{field_name}_analysis.metadata": metadata,
                    f"document_analysis.{field_name}_analysis.status": "Completed",
                    f"document_analysis.{field_name}_analysis.process_finished_on": datetime.datetime.utcnow()
                }
            }
        )


class DocExtraction:
    """
        This is the main class  to extract the details from document

    """

    @staticmethod
    @celery_app.task
    def text_extraction(student_id=None):
        """
            this is used for text_extraction

            Params:
                student_id : the id of student whose documents are to be extracted
        """
        from app.database.database_sync import DatabaseConfigurationSync
        student_id = ObjectId(student_id)
        s3_res = boto3.resource(
            "s3", aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.region_name)
        student = DatabaseConfigurationSync().studentSecondaryDetails.find_one(
            {"student_id": student_id})
        aws_env = settings.aws_env
        base_bucket = getattr(settings, f"s3_{aws_env}_base_bucket")
        try:
            for document_name in ["tenth", "inter", "graduation"]:
                if document_name in student.get('attachments', {}):
                    file = student['attachments'][document_name]['file_s3_url']
                    file_name = PurePath(file).name
                    file_path = Path(file_name)
                    try:
                        season = utility_obj.get_year_based_on_season()
                        object_key = f"{utility_obj.get_university_name_s3_folder()}/{season}/{settings.s3_student_documents_bucket_name}/{student_id}/{document_name}/{file_name}"
                        s3_res.Bucket(base_bucket).download_file(
                            object_key, file_name
                        )
                        field_name = "high_school" if document_name == "tenth" else "senior_school" if document_name == "inter" else "graduation"
                        update_extracted_document_data(file_name,
                                                             student_id,
                                                             document_name,
                                                             field_name)
                    except Exception as e:
                        logger.error(f"Error in text extraction: {e}")
                    finally:
                        if file_path.is_file():
                            file_path.unlink()
        except AttributeError as e:
            pass
