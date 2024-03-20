""" Automated tests for the speakermodel of the Speaker Balancer. """

###########
# Imports #
###########
# Testing
import pytest

# System
import sys

# Custom
sys.path.append("..")
from models.speakermodel import Speaker
from models.speakermodel import SpeakerWrangler


############
# Fixtures #
############
@pytest.fixture
def speaker5():
    speaker1 = Speaker(channel=5)
    speaker1.slm_level = 75
    speaker1.offset = -5
    speaker1.calibrated = True
    return speaker1

@pytest.fixture
def wrangler3():
    sw = SpeakerWrangler()
    for ii in range(0, 3):
        sw.add_speaker(ii)
    return sw

@pytest.fixture
def wrangler3_full(wrangler3):
    wrangler3.calc_offset(channel=0, slm_level=70)
    wrangler3.calc_offset(channel=1, slm_level=75)
    wrangler3.calc_offset(channel=2, slm_level=68)
    return wrangler3


##############
# Unit Tests #
##############
class Test_Speaker:
    """ Tests for the Speaker class. """
    def test_speaker_class_init_chan0(self):
        # Arrange
        s = Speaker(channel=0)

        # Assert
        assert s.channel == 0
        assert s.slm_level == None
        assert s.offset == None
        assert s.calibrated == False


    def test_speaker_class_init_chan5(self):
        # Arrange
        s = Speaker(channel=5)

        # Assert
        assert s.channel == 5
        assert s.slm_level == None
        assert s.offset == None
        assert s.calibrated == False


    def test_speaker_with_values(self, speaker5):
        # Assert
        assert speaker5.channel == 5
        assert speaker5.slm_level == 75
        assert speaker5.offset == -5
        assert speaker5.calibrated == True


class Test_SpeakerWrangler:
    """ Tests for the SpeakerWrangler class. """
    def test_wrangler_init_empty(self):
        # Arrange
        sw = SpeakerWrangler()

        # Assert
        assert sw.speaker_list == []
        assert sw.ref_level == None


    def test_wrangler_add_speaker(self):
        # Arrange
        sw = SpeakerWrangler()
        sw.add_speaker(0)

        # Assert
        assert isinstance(sw.speaker_list, list)
        assert len(sw.speaker_list) == 1
        assert isinstance(sw.speaker_list[0], Speaker)
        assert sw.speaker_list[0].channel == 0
        assert sw.speaker_list[0].slm_level == None
        assert sw.speaker_list[0].offset == None
        assert sw.speaker_list[0].calibrated == False


    def test_wrangler_three_speakers(self):
        # Arrange
        sw = SpeakerWrangler()
        # Add three speakers
        for ii in range(0, 3):
            sw.add_speaker(ii)

        # Assert: Speaker List
        assert len(sw.speaker_list) == 3
        assert isinstance(sw.speaker_list[0], Speaker)
        assert isinstance(sw.speaker_list[1], Speaker)
        assert isinstance(sw.speaker_list[2], Speaker)

        # Assert: Speaker 0
        assert sw.speaker_list[0].channel == 0
        assert sw.speaker_list[0].slm_level == None
        assert sw.speaker_list[0].offset == None
        assert sw.speaker_list[0].calibrated == False

        # Assert: Speaker 1
        assert sw.speaker_list[1].channel == 1
        assert sw.speaker_list[1].slm_level == None
        assert sw.speaker_list[1].offset == None
        assert sw.speaker_list[1].calibrated == False

        # Assert: Speaker 2
        assert sw.speaker_list[2].channel == 2
        assert sw.speaker_list[2].slm_level == None
        assert sw.speaker_list[2].offset == None
        assert sw.speaker_list[2].calibrated == False


    def test_calc_offset_no_reference(self, wrangler3):
        with pytest.raises(TypeError) as e:
            wrangler3.calc_offset(channel=1, slm_level=75)


    def test_calc_offset_with_reference_only(self, wrangler3):
        # Arrange
        wrangler3.calc_offset(channel=0, slm_level=70)

        # Assert
        assert wrangler3.speaker_list[0].channel == 0
        assert wrangler3.speaker_list[0].slm_level == 70
        assert wrangler3.speaker_list[0].offset == 0.0
        assert wrangler3.speaker_list[0].calibrated == True


    def test_calc_offset_successful(self, wrangler3_full):
        # Assert: Speaker 0
        assert wrangler3_full.speaker_list[0].channel == 0
        assert wrangler3_full.speaker_list[0].slm_level == 70
        assert wrangler3_full.speaker_list[0].offset == 0.0
        assert wrangler3_full.speaker_list[0].calibrated == True

        # Assert: Speaker 1
        assert wrangler3_full.speaker_list[1].channel == 1
        assert wrangler3_full.speaker_list[1].slm_level == 75
        assert wrangler3_full.speaker_list[1].offset == -5.0
        assert wrangler3_full.speaker_list[1].calibrated == True

        # Assert: Speaker 2
        assert wrangler3_full.speaker_list[2].channel == 2
        assert wrangler3_full.speaker_list[2].slm_level == 68
        assert wrangler3_full.speaker_list[2].offset == 2.0
        assert wrangler3_full.speaker_list[2].calibrated == True


    def test_check_for_missing_offsets_none(self, wrangler3_full):
        # Assert
        assert wrangler3_full.check_for_missing_offsets() == []


    def test_check_for_missing_offsets_missing_1(self, wrangler3):
        # Arrange
        wrangler3.calc_offset(channel=0, slm_level=70)
        wrangler3.calc_offset(channel=2, slm_level=68)

        # Assert
        assert wrangler3.check_for_missing_offsets() == [1]


    def test_get_data_empty(self, wrangler3):
        assert type(wrangler3.get_data()) == dict
        assert wrangler3.get_data() == {0: None, 1: None, 2: None}


    def test_get_data_full(self, wrangler3_full):
        assert type(wrangler3_full.get_data()) == dict
        assert wrangler3_full.get_data() == {0: 0.0, 1: -5, 2: 2}
