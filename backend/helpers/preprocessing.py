"""
Utility functions for helping with preprocessing files
"""
import csv
import shutil

def upload(file):
    """
    Upload a file to the server. 
    """
    # Save file to a location on the server
    try:
        file_path = "data/" + str(file.filename)
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
    # Read the first row
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file)
            header = next(reader)
            return header

    # Return exception if unsuccessful
    except Exception as e:
        return e
    
