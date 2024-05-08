"""
Utility functions for helping with preprocessing files
"""

import chardet
import csv
import os
import shutil

# Constant for where data will be stored
DATA_PATH = "data/"


def upload(file, id):
    """
    Upload a file to the server.
    """
    # First, create a folder for the id
    try:
        folder_path = DATA_PATH + id
        os.mkdir(folder_path)

        # Then, save file there
        file_path = folder_path + "/" + str(file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    # Return exception if unsuccessful
    except Exception as e:
        return e


def get_header(file_path):
    """
    Get the header of the CSV file.
    """
    # First, get the encoding by reading a small chunk of the file
    try:
        detected_encoding = None
        with open(file_path, "rb") as file:
            raw_data = file.read(10000)
            detected_encoding = chardet.detect(raw_data)["encoding"]

        # Actually read in file and open with correct encoding
        with open(file_path, "r", newline="", encoding=detected_encoding) as file:
            reader = csv.reader(file)
            header = next(reader)
            return header, detected_encoding

    # Return exception if unsuccessful
    except Exception as e:
        return e
