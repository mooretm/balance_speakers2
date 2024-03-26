""" Speaker Balancer. 

    App to balance lab speakers using a sound level meter.

    Written by: Travis M. Moore
    Created: June 09, 2022
"""

###########
# Imports #
###########
# GUI
import tkinter as tk
from tkinter import messagebox

# Data
import numpy as np
import random

# System
import datetime
import os
from pathlib import Path
import sys
from threading import Thread
import time

# Web
import webbrowser, markdown

# Custom
sys.path.append(os.environ['TMPY'])
# Menus
from menus import mainmenu
# Exceptions
from tmgui.shared_exceptions import audio_exceptions
# Models
from tmgui.shared_models import versionmodel
from tmgui.shared_models import audiomodel
from tmgui.shared_models import filehandler as fh
from tmgui.shared_models import calmodel
from models import settingsmodel
from models import speakermodel
# Views
from views import mainview
from views import settingsview
from tmgui.shared_views import audioview
from tmgui.shared_views import calibrationview
# Images
from tmgui.shared_assets import images
# Help
from app_assets import README
from app_assets import CHANGELOG


#########
# BEGIN #
#########
class Application(tk.Tk):
    """ Application root window. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #############
        # Constants #
        #############
        self.NAME = 'Speaker Balancer'
        self.VERSION = '3.0.0'
        self.EDITED = 'March 25, 2024'

        # Create menu settings dictionary
        self._app_info = {
            'name': self.NAME,
            'version': self.VERSION,
            'last_edited': self.EDITED
        }

        ######################################
        # Initialize Models, Menus and Views #
        ######################################
        # Setup main window
        self.withdraw() # Hide window during setup
        self.resizable(False, False)
        self.title(self.NAME)
        self.taskbar_icon = tk.PhotoImage(
            file=images.LOGO_FULL_PNG
            )
        self.iconphoto(True, self.taskbar_icon)

        # Assign special quit function on window close
        # Used to close Vulcan session cleanly even if 
        # user closes window via "X"
        self.protocol('WM_DELETE_WINDOW', self._quit)

        # Create variable dictionary
        self._vars = {
            'selected_speaker': tk.IntVar(value=None),
            'slm_reading': tk.DoubleVar(value=None),
        }

        # Load current session parameters from file
        # or load defaults if file does not exist yet
        # Check for version updates and destroy if mandatory
        self.settings_model = settingsmodel.SettingsModel(self._app_info)
        self._load_settings()

        # Create SpeakerWrangler object
        self.speakers = self._create_speakerwrangler()

        # Load calibration model
        self.calmodel = calmodel.CalModel(self.settings)

        # Load main view
        self.main_frame = mainview.MainFrame(self, self.settings, self._vars)
        self.main_frame.grid(row=5, column=5)

        # Load menus
        self.menu = mainmenu.MainMenu(self, self._app_info)
        self.config(menu=self.menu)

        # Create callback dictionary
        event_callbacks = {
            # File menu
            '<<FileSession>>': lambda _: self._show_settings_dialog(),
            '<<FileQuit>>': lambda _: self._quit(),

            # Tools menu
            '<<ToolsAudioSettings>>': lambda _: self._show_audio_dialog(),
            '<<ToolsCalibration>>': lambda _: self._show_calibration_dialog(),
            '<<ToolsTestOffsets>>': lambda _: self._on_test_offsets(),

            # Help menu
            '<<HelpREADME>>': lambda _: self._show_help(),
            '<<HelpChangelog>>': lambda _: self._show_changelog(),

            # Settings window
            '<<SessionSubmit>>': lambda _: self._save_sessionpars(),

            # Calibration window
            '<<CalPlay>>': lambda _: self.play_calibration_file(),
            '<<CalStop>>': lambda _: self.stop_audio(),
            '<<CalibrationSubmit>>': lambda _: self._calc_offset(),

            # Audio settings window
            '<<AudioDialogSubmit>>': lambda _: self._save_sessionpars(),

            # Main View
            '<<MainPlay>>': lambda _: self._on_play(),
            '<<MainStop>>': lambda _: self.stop_audio(),
            '<<MainSubmit>>': lambda _: self._on_submit(),
            '<<MainSave>>': lambda _: self._on_save(),
        }

        # Bind callbacks to sequences
        for sequence, callback in event_callbacks.items():
            self.bind(sequence, callback)

        # Center main window
        self.center_window()

        # Check for updates
        if (self.settings['check_for_updates'].get() == 'yes') and\
        (self.settings['config_file_status'].get() == 1):
            _filepath = self.settings['version_lib_path'].get()
            u = versionmodel.VersionChecker(_filepath, self.NAME, self.VERSION)
            if u.status == 'mandatory':
                messagebox.showerror(
                    title="New Version Available",
                    message="A mandatory update is available. Please install " +
                        f"version {u.new_version} to continue.",
                    detail=f"You are using version {u.app_version}, but " +
                        f"version {u.new_version} is available."
                )
                self.destroy()
            elif u.status == 'optional':
                messagebox.showwarning(
                    title="New Version Available",
                    message="An update is available.",
                    detail=f"You are using version {u.app_version}, but " +
                        f"version {u.new_version} is available."
                )
            elif u.status == 'current':
                pass
            elif u.status == 'app_not_found':
                messagebox.showerror(
                    title="Update Check Failed",
                    message="Cannot retrieve version number!",
                    detail=f"'{self.NAME}' does not exist in the version library."
                 )
            elif u.status == 'library_inaccessible':
                messagebox.showerror(
                    title="Update Check Failed",
                    message="The version library is unreachable!",
                    detail="Please check that you have access to Starfile."
                )


    #####################
    # General Functions #
    #####################
    def center_window(self):
        """ Center the root window. """
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
        x = screen_width/2 - size[0]/2
        y = screen_height/2 - size[1]/2
        self.geometry("+%d+%d" % (x, y))
        self.deiconify()


    def _create_filename(self):
        """ Create file name and path. """
        datestamp = datetime.datetime.now().strftime("%Y_%b_%d_%H%M")
        self.filename = "speaker_offsets_" + datestamp + ".csv"


    def _create_speakerwrangler(self):
        """ Instantiate a SpeakerWrangler object and populate it with
            the specified number of speakers.
        """
        # Get specified number of speakers
        num_speakers = self.settings['num_speakers'].get()

        # Instantiate and populate SpeakerWrangler
        sw = speakermodel.SpeakerWrangler()
        for ii in range(0, num_speakers):
            sw.add_speaker(ii)
        return sw


    def wgn(self, dur, fs):
        """ Function to generate white Gaussian noise. """
        r = int(dur * fs)
        random.seed(4)
        wgn = [random.gauss(0.0, 1.0) for i in range(r)]
        wgn -= np.mean(wgn) # Remove DC offset
        wgn = wgn / np.max(abs(wgn)) # Normalize
        return wgn


    def _quit(self):
        """ Exit the application. """
        self.destroy()


    ###################
    # File Menu Funcs #
    ###################
    def _show_settings_dialog(self):
        """ Show session parameter dialog. """
        print("\ncontroller: Calling session dialog...")
        settingsview.SessionDialog(self, self.settings)


    ########################
    # Main View Functions #
    ########################
    def _on_play(self):
        """ Generate and present WGN. """
        # Save latest duration and level values
        self._save_sessionpars()

        # Generate WGN
        FS = 48000
        _wgn = self.wgn(dur=self.settings['duration'].get(), fs=FS)

        # Present WGN
        self.present_audio(
            audio=_wgn, 
            pres_level=self.settings['level'].get(),
            sampling_rate=FS
        )


    def _on_submit(self):
        """ Save SLM Reading value and update Speaker object. """
        # Get current values
        current_speaker = self._vars['selected_speaker'].get()
        slm_level = self._vars['slm_reading'].get()

        # Calculate speaker offset
        try:
            self.speakers.calc_offset(
                channel=current_speaker, 
                slm_level=slm_level
            )
            self.main_frame.update_offset_labels(
                channel=current_speaker,
                offset=self.speakers.speaker_list[current_speaker].offset
            )
        except TypeError as e:
            msg = "Please start with channel 1 to create a reference level!"
            print("\ncontroller: " + msg)
            messagebox.showwarning(
                title="Invalid Reference Level",
                message=msg,
                detail=e
            )
        
        # Print feedback to console
        print(f"controller:"\
              f"{self.speakers.speaker_list[current_speaker].__dict__}")


    def _on_save(self):
        """ Create dictionary with channels and offsets.
            Save dictionary to CSV. 
        """
        # Check for missing offsets (i.e., speakers that weren't balanced)
        missing_offsets = self.speakers.check_for_missing_offsets()
        if missing_offsets:
            missing = [int(val)+1 for val in missing_offsets]
            missing = str(missing)[1:-1]
            resp = messagebox.askyesno(
                title="Missing Value",
                message="Do you want to proceed with missing offsets?",
                detail=f"Speakers with missing offsets: {missing}"
            )
            if not resp:
                return
  
        # Create offsets dictionary
        offset_dict = self.speakers.get_data()
        print(offset_dict)

        # Create file name
        self._create_filename()

        # Call filehandler save function
        try:
            #_filepath = os.path.join("Data", self.filename)
            self.mycsv = fh.CSVFile(
                filepath=self.filename, 
                data=offset_dict, 
                file_browser=True
            )
        except PermissionError as e:
            print(e)
            messagebox.showerror(
                title="Access Denied",
                message="Data not saved! Cannot write to file!",
                detail=e
            )
            return
        except OSError as e:
            print(e)
            messagebox.showerror(
                title="File Not Found",
                message="Cannot find file or directory!",
                detail=e
            )
            return


    #############################
    # Settings Dialog Functions #
    #############################
    def _load_settings(self):
        """ Load parameters into self.settings dict. """
        # Variable types
        vartypes = {
        'bool': tk.BooleanVar,
        'str': tk.StringVar,
        'int': tk.IntVar,
        'float': tk.DoubleVar
        }

        # Create runtime dict from settingsmodel fields
        self.settings = dict()
        for key, data in self.settings_model.fields.items():
            vartype = vartypes.get(data['type'], tk.StringVar)
            self.settings[key] = vartype(value=data['value'])
        print("\ncontroller: Loaded sessionpars model fields into " +
            "running sessionpars dict")


    def _save_sessionpars(self, *_):
        """ Save current runtime parameters to file 
        """
        print("\ncontroller: Calling sessionpars model set and save funcs")
        for key, variable in self.settings.items():
            self.settings_model.set(key, variable.get())
            self.settings_model.save()


    ########################
    # Tools Menu Functions #
    ########################
    def _on_test_offsets(self):
        """ Start automated offset test thread. """
        # Delete existig instances of thread object
        try:
            del self.t
        except AttributeError:
            pass

        # Create and call Thread instance
        try:
            self.t = Thread(target=self._on_test_offsets_thread)
            self.t.start()
        except:
            print("\ncontroller: Failed to start audio thread.")
            return


    def _on_test_offsets_thread(self):
        """ Automatically step through all speakers. """
        # Get number of speakers/channels
        num_speakers = self.settings['num_speakers'].get()

        # Update mainview: START TEST
        self.main_frame.start_auto_test()

        # Present WGN to each speaker for the specified duration
        for ii in range(0, num_speakers):
            # Select speaker number
            self._vars['selected_speaker'].set(ii)

            # Enable current speaker button on mainframe
            self.main_frame._update_single_speaker_button_state(ii, 'enabled')

            # Routing from the audioview is saved as a string
            chan=str(ii+1)
            self.settings['channel_routing'].set(chan)

            # Start audio playback
            self._on_play()

            # Sleep for duration of playback
            time.sleep(self.settings['duration'].get())

            # Disable current speaker button
            self.main_frame._update_single_speaker_button_state(ii, 'disabled')

        # Update mainview: END TEST
        self.main_frame.end_auto_test()


    def _show_audio_dialog(self):
        """ Show audio settings dialog. """
        print("\ncontroller: Calling audio dialog...")
        audioview.AudioDialog(self, self.settings)


    def _show_calibration_dialog(self):
        """ Display the calibration dialog window. """
        print("\ncontroller: Calling calibration dialog...")
        calibrationview.CalibrationDialog(self, self.settings)


    ################################
    # Calibration Dialog Functions #
    ################################
    def play_calibration_file(self):
        """ Load calibration file and present
        """
        # Get calibration file
        try:
            self.calmodel.get_cal_file()
        except AttributeError:
            messagebox.showerror(
                title="File Not Found",
                message="Cannot find internal calibration file!",
                detail="Please use a custom calibration file."
            )
        # Present calibration signal
        self.present_audio(
            audio=Path(self.calmodel.cal_file), 
            pres_level=self.settings['cal_level_dB'].get()
        )


    def _calc_offset(self):
        """ Calculate offset based on SLM reading.
        """
        # Calculate new presentation level
        self.calmodel.calc_offset()
        # Save level - this must be called here!
        self._save_sessionpars()


    def _calc_level(self, desired_spl):
        """ Calculate new dB FS level using slm_offset.
        """
        # Calculate new presentation level
        self.calmodel.calc_level(desired_spl)
        # Save level - this must be called here!
        self._save_sessionpars()


    #######################
    # Help Menu Functions #
    #######################
    def _show_help(self):
        """ Create html help file and display in default browser
        """
        print(f"\ncontroller: Calling README file (will open in browser)")
        # Read markdown file and convert to html
        with open(README.README_MD, 'r') as f:
            text = f.read()
            html = markdown.markdown(text)

        # Create html file for display
        with open(README.README_HTML, 'w') as f:
            f.write(html)

        # Open README in default web browser
        webbrowser.open(README.README_HTML)


    def _show_changelog(self):
        """ Create html CHANGELOG file and display in default browser
        """
        print(f"\ncontroller: Calling CHANGELOG file (will open in browser)")
        # Read markdown file and convert to html
        with open(CHANGELOG.CHANGELOG_MD, 'r') as f:
            text = f.read()
            html = markdown.markdown(text)

        # Create html file for display
        with open(CHANGELOG.CHANGELOG_HTML, 'w') as f:
            f.write(html)

        # Open CHANGELOG in default web browser
        webbrowser.open(CHANGELOG.CHANGELOG_HTML)


    ###################
    # Audio Functions #
    ###################
    def _create_audio_object(self, audio, **kwargs):
        # Create audio object
        try:
            self.a = audiomodel.Audio(
                audio=audio,
                **kwargs
            )
        except FileNotFoundError:
            messagebox.showerror(
                title="File Not Found",
                message="Cannot find the audio file!",
                detail="Go to File>Session to specify a valid audio path."
            )
            self._show_settings_dialog()
            return
        except audio_exceptions.InvalidAudioType:
            raise
        except audio_exceptions.MissingSamplingRate:
            raise


    def present_audio(self, audio, pres_level, **kwargs):
        # Load audio
        try:
            self._create_audio_object(audio, **kwargs)
        except audio_exceptions.InvalidAudioType as e:
            messagebox.showerror(
                title="Invalid Audio Type",
                message="The audio type is invalid!",
                detail=f"{e} Please provide a Path or ndarray object."
            )
            return
        except audio_exceptions.MissingSamplingRate as e:
            messagebox.showerror(
                title="Missing Sampling Rate",
                message="No sampling rate was provided!",
                detail=f"{e} Please provide a Path or ndarray object."
            )
            return

        # Play audio
        self._play(pres_level)


    def _play(self, pres_level):
        """ Format channel routing, present audio and catch 
            exceptions.
        """
        # Attempt to present audio
        try:
            self.a.play(
                level=pres_level,
                device_id=self.settings['audio_device'].get(),
                routing=self._format_routing(
                    self.settings['channel_routing'].get())
            )
        except audio_exceptions.InvalidAudioDevice as e:
            print(e)
            messagebox.showerror(
                title="Invalid Device",
                message="Invalid audio device! Go to Tools>Audio Settings " +
                    "to select a valid audio device.",
                detail = e
            )
            # Open Audio Settings window
            self._show_audio_dialog()
        except audio_exceptions.InvalidRouting as e:
            print(e)
            messagebox.showerror(
                title="Invalid Routing",
                message="Speaker routing must correspond with the " +
                    "number of channels in the audio file! Go to " +
                    "Tools>Audio Settings to update the routing.",
                detail=e
            )
            # Open Audio Settings window
            self._show_audio_dialog()
        except audio_exceptions.Clipping:
            print("controller: Clipping has occurred! Aborting!")
            messagebox.showerror(
                title="Clipping",
                message="The level is too high and caused clipping.",
                detail="The waveform will be plotted when this message is " +
                    "closed for visual inspection."
            )
            self.a.plot_waveform("Clipped Waveform")


    def stop_audio(self):
        try:
            self.a.stop()
        except AttributeError:
            print("\ncontroller: Stop called, but there is no audio object!")


    def _format_routing(self, routing):
        """ Convert space-separated string to list of ints
            for speaker routing.
        """
        routing = routing.split()
        routing = [int(x) for x in routing]

        return routing


if __name__ == "__main__":
    app = Application()
    app.mainloop()
