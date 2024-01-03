""" Class to create speaker objects and a speaker wrangler.

    Written by: Travis M. Moore
    Created: June 9, 2022
    Last edited: January 02, 2024
"""

###########
# Imports #
###########
# Scientific
import numpy as np


###########
# Classes #
###########
class Speaker:
    """ Speaker object with position number, offset, and 
    calibrated(boolean) attributes.
    """
    def __init__(self, channel):
        self.channel = channel
        self.slm_level = None
        self.offset = None
        self.calibrated = False


class SpeakerWrangler:
    """ Class to handle Speaker objects. """
    def __init__(self):
        # Empty list to hold Speaker objects
        self.speaker_list = []

        # Reference level: channel 0 slm_level
        self.ref_level = None 


    def add_speaker(self, channel):
        """ Create new speaker obj and append to list."""
        speaker = Speaker(channel=channel)
        self.speaker_list.append(speaker)
        return speaker


    def calc_offset(self, channel, slm_level):
        """ Calculate and update offset. """
        if channel == 0:
            self.ref_level = slm_level

        # Calculate offset
        try:
            offset = np.round(self.ref_level - slm_level, 1)
        except TypeError:
            raise TypeError
        
        # Update Speaker attributes
        self.speaker_list[channel].slm_level = slm_level
        self.speaker_list[channel].offset = offset
        self.speaker_list[channel].calibrated = True


    def check_for_missing_offsets(self):
        """ Loop through each Speaker object and test whether the .calibrated
            attribute is set to True.
        """
        print(f"\nspeakermodel: Checking for missing offsets...")
        missing_offsets = []
        for speaker in self.speaker_list:
            if not speaker.calibrated:
                missing_offsets.append(speaker.channel)
                msg = "Missing offset for speaker "\
                    f"{speaker.channel}!"
                print("speakermodel: " + msg)
        print("speakermodel: Done")
        return missing_offsets


    def get_data(self):
        """ Return a dictionary of channels and offsets. """
        #channels = range(1, len(self.speaker_list))
        channels = [speaker.channel for speaker in self.speaker_list]
        offsets = [speaker.offset for speaker in self.speaker_list]
        
        return dict(zip(channels, offsets))
