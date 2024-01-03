""" Class to write data to .csv
"""

############
# IMPORTS  #
############
# GUI packages
from tkinter import filedialog

# System packages
import csv
from pathlib import Path
from datetime import datetime
import os


#########
# MODEL #
#########
class CSVModel:
    """ Write provided dictionary to .csv
    """
    def __init__(self, sessionpars):
        # Assign attribute values
        self.sessionpars = sessionpars


    def _create_file_name(self):
        """ Create the file name for saving offsets. """
        # Generate date stamp
        datestamp = datetime.now().strftime("%Y_%b_%d_%H%M")

        # Create file name
        return 'speaker_offsets_' + str(datestamp)


    def _get_save_path(self, file_name):
        """ Prompt user for save directory. """
        # # Get file path
        # file_path = filedialog.asksaveasfile(
        #     initialfile = file_name,
        #     defaultextension='.csv').name
        # print(file_path)
        # if not file_path:
        #     return

        # Get file path
        try:
            file_path = filedialog.asksaveasfile(
                initialfile = file_name,
                defaultextension='.csv').name
            print(file_path)
        except:
            return None

        # Create save path
        return Path(file_path)


    def _check_write_access(self, file_path):
        """ Check whether path and file are writeable.
        """
        # Check for write access to store csv
        file_exists = os.access(file_path, os.F_OK)
        parent_writable = os.access(file_path.parent, os.W_OK)
        file_writable = os.access(file_path, os.W_OK)
        if (
            (not file_exists and not parent_writable) or
            (file_exists and not file_writable)
        ):
            msg = (
                f"\ncsvmodel: Permission denied accessing "
                f"file: {file_path}"
            )
            raise PermissionError(msg)


    def save_record(self, data):
        """ Save a dictionary of data to .csv file 
        """
        # Create file name
        file_name = self._create_file_name()

        # Get directory for saving the file
        file_path = self._get_save_path(file_name=file_name)
        if not file_path:
            return

        # Check write access
        self._check_write_access(file_path)

        # Open new CSV in write mode
        with open(file_path, 'w', newline='') as csv_file:
            # Create a CSV writer object
            csvwriter = csv.writer(csv_file)

            # Write header
            csvwriter.writerow(["Channel", "Offset"])

            # Write key-value pairs vertically
            for key, value in data.items():
                csvwriter.writerow([key, value])

        print("\ncsvmodel: Record successfully saved!")
