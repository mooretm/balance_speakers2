import unittest
from unittest.mock import patch, mock_open

from pathlib import Path

import os, sys
sys.path.append(os.environ['TMPY'])
from tmgui.shared_models.filehandler3 import CSVFile


class TestFileHandler(unittest.TestCase):
    def test_file_writer(self):
        test_file_path = "/path/to/test/file.csv"

        test_data = {
            "test1": 4,
            "test2": 5,
            "test3": 6,
        }    

        with patch('tmgui.shared_models.filehandler3.open', mock_open()) as mocked_file:
            CSVFile(test_file_path, test_data)

            mocked_file.assert_called_once_with(Path(test_file_path), 'a', newline='')

            mocked_file().write.assert_called_once_with('4,5,6\r\n')

        del test_file_path
