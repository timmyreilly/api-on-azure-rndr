"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, Flask, request 
from FlaskWebProject import app

import httplib
import hashlib
import mimetypes
import hmac
import base64
from email.utils import formatdate
import sys
import json
import os

# Vuforia Related Scripts

def compute_md5_hex(data):
    """Return the hex MD5 of the data"""
    h = hashlib.md5()
    h.update(data)
    return h.hexdigest()


def compute_hmac_base64(key, data):
    """Return the Base64 encoded HMAC-SHA1 using the provide key"""
    h = hmac.new(key, None, hashlib.sha1)
    h.update(data)
    return base64.b64encode(h.digest())


def authorization_header_for_request(access_key, secret_key, method, content, content_type, date, request_path):
    """Return the value of the Authorization header for the request parameters"""
    components_to_sign = list()
    components_to_sign.append(method)
    components_to_sign.append(str(compute_md5_hex(content)))
    components_to_sign.append(str(content_type))
    components_to_sign.append(str(date))
    components_to_sign.append(str(request_path))
    string_to_sign = "\n".join(components_to_sign)
    signature = compute_hmac_base64(secret_key, string_to_sign)
    auth_header = "VWS %s:%s" % (access_key, signature)
    return auth_header


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """

    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    lines = []
    for (key, value) in fields:
        lines.append('--' + BOUNDARY)
        lines.append('Content-Disposition: form-data; name="%s"' % key)
        lines.append('')
        lines.append(value)
    for (key, filename, value) in files:
        lines.append('--' + BOUNDARY)
        lines.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        lines.append('Content-Type: %s' % get_content_type(filename))
        lines.append('')
        lines.append(value)
    lines.append('--' + BOUNDARY + '--')
    lines.append('')
    body = CRLF.join(lines)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def send_custom_query(access_key, secret_key, target_id, new_metadata):
    http_method = 'PUT'
    date = formatdate(None, localtime=False, usegmt=True)

    endpoint = "vws.vuforia.com"
    path = "/targets/" + target_id

    request_body = '{"application_metadata" : "' + new_metadata + '"}'
    content_type_bare = 'application/json'

    # Sign the request and get the Authorization header
    auth_header = authorization_header_for_request(access_key, secret_key, http_method, request_body, content_type_bare,
                                                   date, path)

    request_headers = {
        'Accept': 'application/json',
        'Authorization': auth_header,
        'Content-Type': content_type_bare,
        'Date': date
    }

    # Make the request over HTTPS on port 443
    http = httplib.HTTPSConnection(endpoint, 443)
    http.request(http_method, path, request_body, request_headers)

    response = http.getresponse()
    response_body = response.read()
    return response.status, response_body


# API Endpoints

ACCESS_KEY = os.environ.get('ACCESS_KEY', '')
SECRET_KEY = os.environ.get('SECRET_KEY', '')

@app.route("/target", methods=['POST'])
def update_target():
    data = request.data
    if type(data) == str:
        data = json.loads(data)
    target_id = data['id']
    new_metadata = base64.b64encode(data['metadata'])
    if new_metadata:
        status, body = send_custom_query(ACCESS_KEY, SECRET_KEY, target_id, new_metadata)
        return body, status
    else:
        return 'No new metadata passed', 400
