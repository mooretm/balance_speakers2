import os, sys
from importlib import reload


sys.path.append(os.environ['TMPY'])
import tmgui
reload(tmgui)
from tmgui.shared_models import filehandler3 as fh
reload(fh)


import pytest
from unittest.mock import patch, mock_open



############
# Fixtures #
############
test_file_path = "/path/to/test/file.csv"

test_data = {
    "test1": 4,
    "test2": 5,
    "test3": 6,
}    


@pytest.fixture
def csv_file_instance(mocker):
    return fh.CSVFile(test_file_path, test_data)
    #return mocker.MagicMock(spec=fh.CSVFile)


##############
# Unit Tests #
##############
def test_csv_file_write(csv_file_instance, mocker):
    # Call the _write method
    csv_file_instance._write(test_data)

    # Assert that the save method is called once
    assert csv_file_instance._write.called_once

    # Assert that the save method is called with the test data
    csv_file_instance._write.assert_called_once_with(test_data)


def test_write_to_file(csv_file_instance, tmp_path):
    file = tmp_path / 'output.csv'
    test_data = "hello"
    open_mock = mock_open()
    with patch("tmgui.shared_models.filehandler3.open", open_mock, create=True):
        csv_file_instance.save(file, test_data)

    
    open_mock.assert_called_with("output.csv", "a")
    open_mock.return_value.write.assert_called_once_with(test_data)
