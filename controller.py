""" Speaker Balancer. App to balance lab speakers.

    Written by: Travis M. Moore
    Created: June 09, 2022
"""

###########
# Imports #
###########
# Import GUI packages
import tkinter as tk
from tkinter import messagebox

# Import data science packages
import numpy as np
import random

# Import system packages
from pathlib import Path
import time
import asyncio

# Import misc packages
import webbrowser
import markdown

# Import custom modules
# Menu imports
from menus import mainmenu
# Exception imports
from exceptions import audio_exceptions
# Model imports
from models import sessionmodel
from models import versionmodel
from models import audiomodel
from models import calmodel
from models import csvmodel
from models import speakermodel
# View imports
from views import mainview
from views import sessionview
from views import audioview
from views import calibrationview
# Image imports
from app_assets import images
# Help imports
from app_assets import README


#########
# BEGIN #
#########
class Application(tk.Tk):
    """ Application root window
    """
    def __init__(self, async_loop, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.async_loop = async_loop

        #############
        # Constants #
        #############
        self.NAME = 'Speaker Balancer'
        self.VERSION = '2.0.0'
        self.EDITED = 'January 02, 2024'

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
        self.sessionpars_model = sessionmodel.SessionParsModel(self._app_info)
        self._load_sessionpars()

        # Create SpeakerWrangler object
        self.speakers = self._create_speakerwrangler()

        # Load CSV writer model
        self.csvmodel = csvmodel.CSVModel(self.sessionpars)

        # Load calibration model
        self.calmodel = calmodel.CalModel(self.sessionpars)

        # Load main view
        self.main_frame = mainview.MainFrame(self, self.sessionpars, self._vars)
        self.main_frame.grid(row=5, column=5)

        # Load menus
        self.menu = mainmenu.MainMenu(self, self._app_info)
        self.config(menu=self.menu)

        # Create callback dictionary
        event_callbacks = {
            # File menu
            '<<FileSession>>': lambda _: self._show_session_dialog(),
            #'<<FileTestOffsets>>': lambda _: self._on_test_offsets(),
            '<<FileQuit>>': lambda _: self._quit(),

            # Tools menu
            '<<ToolsAudioSettings>>': lambda _: self._show_audio_dialog(),
            '<<ToolsCalibration>>': lambda _: self._show_calibration_dialog(),
            '<<ToolsTestOffsets>>': lambda _: self._on_test_offsets(),

            # Help menu
            '<<HelpREADME>>': lambda _: self._show_help(),
            '<<HelpChangelog>>': lambda _: self._show_changelog(),

            # Session dialog commands
            '<<SessionSubmit>>': lambda _: self._save_sessionpars(),

            # Calibration dialog commands
            '<<CalPlay>>': lambda _: self.play_calibration_file(),
            '<<CalStop>>': lambda _: self.stop_audio(),
            '<<CalibrationSubmit>>': lambda _: self._calc_offset(),

            # Audio dialog commands
            '<<AudioDialogSubmit>>': lambda _: self._save_sessionpars(),

            # Main View commands
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
        if (self.sessionpars['check_for_updates'].get() == 'yes') and\
        (self.sessionpars['config_file_status'].get() == 1):
            _filepath = self.sessionpars['version_lib_path'].get()
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
        """ Center the root window 
        """
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
        x = screen_width/2 - size[0]/2
        y = screen_height/2 - size[1]/2
        self.geometry("+%d+%d" % (x, y))
        self.deiconify()


    def _create_speakerwrangler(self):
        """ Instantiate a SpeakerWrangler object and populate it with
            the specified number of speakers.
        """
        # Get specified number of speakers
        num_speakers = self.sessionpars['num_speakers'].get()

        # Instantiate and populate SpeakerWrangler
        sw = speakermodel.SpeakerWrangler()
        for ii in range(0,num_speakers):
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
    def _show_session_dialog(self):
        """ Show session parameter dialog. """
        print("\ncontroller: Calling session dialog...")
        x = sessionview.SessionDialog(self, self.sessionpars)


    ########################
    # Main View Functions #
    ########################
    def _on_play(self):
        """ Generate and present WGN. """
        # Save latest duration and level values
        self._save_sessionpars()

        # Generate WGN
        FS = 48000
        _wgn = self.wgn(dur=self.sessionpars['duration'].get(), fs=FS)

        # Present WGN
        self.present_audio(
            audio=_wgn, 
            pres_level=self.sessionpars['level'].get(),
            sampling_rate=FS
        )


    def _on_submit(self):
        """ Save SLM Reading value and update Speaker object."""
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
            msg = "You must start with channel 1 to create a reference level!"
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
            Send dictionary to csvmodel. 
        """
        # Create offsets dictionary
        offset_dict = self.speakers.get_data()

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
  
        # Call csvmodel save function
        try:
            self.csvmodel.save_record(offset_dict)
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


    ############################
    # Session Dialog Functions #
    ############################
    def _load_sessionpars(self):
        """ Load parameters into self.sessionpars dict 
        """
        vartypes = {
        'bool': tk.BooleanVar,
        'str': tk.StringVar,
        'int': tk.IntVar,
        'float': tk.DoubleVar
        }

        # Create runtime dict from session model fields
        self.sessionpars = dict()
        for key, data in self.sessionpars_model.fields.items():
            vartype = vartypes.get(data['type'], tk.StringVar)
            self.sessionpars[key] = vartype(value=data['value'])
        print("\ncontroller: Loaded sessionpars model fields into " +
            "running sessionpars dict")


    def _save_sessionpars(self, *_):
        """ Save current runtime parameters to file 
        """
        print("\ncontroller: Calling sessionpars model set and save funcs")
        for key, variable in self.sessionpars.items():
            self.sessionpars_model.set(key, variable.get())
            self.sessionpars_model.save()


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
            self._show_session_dialog()
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
                device_id=self.sessionpars['audio_device'].get(),
                routing=self._format_routing(
                    self.sessionpars['channel_routing'].get())
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


    ########################
    # Tools Menu Functions #
    ########################
    def _on_test_offsets(self):
        """ Start automated offset test thread."""
        #Thread(target=self._on_test_offsets_thread).start()
        self.async_loop.run_until_complete(self._on_test_offsets_thread())


    async def _on_test_offsets_thread(self):
        """ Automatically step through all speakers to verify
            offsets are correct.
        """
        # Get number of speakers/channels
        num_speakers = self.sessionpars['num_speakers'].get()

        # Update mainview: START TEST
        self.main_frame.start_auto_test()

        # Present WGN to each speaker for the specified duration
        for ii in range(0, num_speakers):
            # Force select a speaker radio button
            self._vars['selected_speaker'].set(ii)

            # Enable the current speaker radio button
            self.main_frame._update_single_speaker_button_state(ii, 'enabled')

            # Assign channel based on speaker
            # Routing from the audioview is saved as a space-separated string
            chan=str(ii+1)
            self.sessionpars['channel_routing'].set(chan)

            # Present audio
            self._on_play()
            time.sleep(self.sessionpars['duration'].get())

            # Disable speaker radio button
            self.main_frame._update_single_speaker_button_state(ii, 'disabled')

        # Update mainview: END TEST
        self.main_frame.end_auto_test()


    def _show_audio_dialog(self):
        """ Show audio settings dialog
        """
        print("\ncontroller: Calling audio dialog...")
        audioview.AudioDialog(self, self.sessionpars)


    def _show_calibration_dialog(self):
        """ Display the calibration dialog window
        """
        print("\ncontroller: Calling calibration dialog...")
        calibrationview.CalibrationDialog(self, self.sessionpars)


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
            pres_level=self.sessionpars['cal_level_dB'].get()
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
        """ Create html help file and display in default browser
        """
        print(f"\ncontroller: Calling CHANGELOG file (will open in browser)")
        # Read markdown file and convert to html
        with open(README.CHANGELOG_MD, 'r') as f:
            text = f.read()
            html = markdown.markdown(text)

        # Create html file for display
        with open(README.CHANGELOG_HTML, 'w') as f:
            f.write(html)

        # Open README in default web browser
        webbrowser.open(README.CHANGELOG_HTML)


if __name__ == "__main__":
    # Create an asynchronous loop
    async_loop = asyncio.new_event_loop()

    # Instantiate an instance of Application and 
    # pass the asynchronous loop
    app = Application(async_loop)
    app.mainloop()
