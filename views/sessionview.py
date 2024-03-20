""" Settings dialog. """

###########
# Imports #
###########
# Import GUI packages
import tkinter as tk
from tkinter import ttk


#########
# BEGIN #
#########
class SessionDialog(tk.Toplevel):
    """ Dialog for setting session parameters
    """
    def __init__(self, parent, settings, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.settings = settings

        self.withdraw()
        self.resizable(False, False)
        self.title("Settings")
        self.grab_set()


        #################
        # Create Frames #
        #################
        # Shared frame settings
        frame_options = {'padx': 10, 'pady': 10}
        widget_options = {'padx': 5, 'pady': 5}

        # Session info frame
        frm_session = ttk.Labelframe(self, text='Settings')
        frm_session.grid(row=5, column=5, **frame_options, sticky='nsew')

        # # Session options frame
        # frm_options = ttk.Labelframe(self, text='Stimulus Options')
        # frm_options.grid(row=10, column=5, **frame_options, sticky='nsew')

        # # Audio file browser frame
        # frm_audiopath = ttk.Labelframe(self, text="Audio File Directory")
        # frm_audiopath.grid(row=15, column=5, **frame_options, ipadx=5, 
        #     ipady=5)

        # # Matrix file browser frame
        # frm_matrixpath = ttk.Labelframe(self, text='Matrix File Path')
        # frm_matrixpath.grid(row=20, column=5, **frame_options, ipadx=5, 
        #     ipady=5)


        ################
        # Draw Widgets #
        ################
        # Number of speakers
        ttk.Label(frm_session, text="Number of Speakers:",
            ).grid(row=5, column=5, sticky='e', **widget_options)
        ttk.Entry(frm_session, width=6, 
            textvariable=self.settings['num_speakers']
            ).grid(row=5, column=10, sticky='w')
        ttk.Label(frm_session, text="(Requires restart)"
            ).grid(row=5, column=15, sticky='w', padx=5)


        # ###################
        # # Audio Directory #
        # ###################
        # # Descriptive label
        # ttk.Label(frm_audiopath, text="Path:"
        #     ).grid(row=20, column=5, sticky='e', **widget_options)

        # # Retrieve and truncate previous audio directory
        # short_audio_path = general.truncate_path(
        #     self.settings['audio_files_dir'].get()
        # )

        # # Create textvariable
        # self.audio_var = tk.StringVar(value=short_audio_path)

        # # Audio directory label
        # ttk.Label(frm_audiopath, textvariable=self.audio_var, 
        #     borderwidth=2, relief="solid", width=60
        #     ).grid(row=20, column=10, sticky='w')
        # ttk.Button(frm_audiopath, text="Browse", 
        #     command=self._get_audio_directory,
        #     ).grid(row=25, column=10, sticky='w', pady=(0, 10))


        # Submit button
        btn_submit = ttk.Button(self, text="Submit", command=self._on_submit)
        btn_submit.grid(row=40, column=5, columnspan=2, pady=(0, 10))

        # Center the session dialog window
        self.center_window()


    #############
    # Functions #
    #############
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


    def _on_submit(self):
        """ Check number of presentations != 0.
            Send submit event to controller.
        """
        print("\nsessionview: Sending save event...")
        self.parent.event_generate('<<SessionSubmit>>')
        self.destroy()
