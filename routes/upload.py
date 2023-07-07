import io
import re, base64

import PyPDF2

from flask import request, jsonify, Blueprint

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/', methods=['POST'])
def upload_file():
    uid = request.args.get('uid')
    raw_data = request.get_data(as_text=True)
    try:
        (name, stream, type) = extract_file_data(raw_data)
        if stream:

            text = extract_text_from_pdf_stream(stream)

            # Process the data and file as needed
            # load_data_from_pdf(uid, file)
            print(text)
            print("Total Size:", len(text))

            return jsonify({'message': 'Data processed successfully'}), 200

        return jsonify({'message': 'UID and File data not found'}), 400
    except Exception as e:
        print(e)
        return jsonify({'message': 'Invalid request data'}), 400


def extract_uid(raw_data):
    uid_start = raw_data.find('name="uid"\r\n\r\n') + len('name="uid"\r\n\r\n')
    uid_end = raw_data.find('\r\n', uid_start)
    return raw_data[uid_start:uid_end]


def extract_file_data(raw_data):
    filename_pattern = r'Content-Disposition: form-data; name="file"; filename="(.*?)"'
    filetype_pattern = r'Content-Type: "(.*?)"'

    filename_match = re.search(filename_pattern, raw_data, re.DOTALL)
    filetype_match = re.search(filetype_pattern, raw_data, re.DOTALL)

    stream_pattern = r'stream\n((.*?)%%EOF)'
    stream_match = re.search(stream_pattern, raw_data, re.DOTALL)

    if filename_match:
        file_name = filename_match.group(1)
        file_type = None  # filetype_match.group(1)
        file_stream = stream_match.group(1)

        # if file_type == 'application/pdf':
        # Decode and save the PDF file
        decoded_file = base64.b64decode(file_stream.encode())

        with open(file_name, 'wb') as f:
            f.write(decoded_file)

        # Extracted values
        print("File Name:", file_name)
        print("File Type:", file_type)
        # print("File Stream:", file_stream)
        # print(file_stream)

        return file_name, file_stream, file_type
    else:
        return None


def extract_text_from_pdf_stream(stream):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(stream.encode()))

    text = ''
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()

    return text
