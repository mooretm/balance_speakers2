""" Main view for Speaker Balancer. """

###########
# Imports #
###########
# Import GUI packages
import tkinter as tk
from tkinter import ttk


#########
# BEGIN #
#########
class MainFrame(ttk.Frame):
    def __init__(self, parent, settings, _vars, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Assign variables
        self.parent = parent
        self.settings = settings
        self._vars = _vars
        self._num_speakers = settings['num_speakers'].get()

        # Populate frame with widgets
        self.draw_widgets()


    def draw_widgets(self):
        """ Populate the main view with all widgets. """
        ##########
        # Styles #
        ##########
        # Font sizes
        self.style = ttk.Style(self)
        self.style.configure('Heading.TLabel', font=('TkDefaultFont', 16))
        self.style.configure('Big.TLabel', font=('TkDefaultFont', 15))
        self.style.configure('Medium.TLabel', font=('TkDefaultFont', 12))
        self.style.configure('TLabel', font=('TkDefaultFont', 10))
        self.style.configure('Big.TButton', font=('TKDefaultFont', 15))

        # Colors
        custom_color = 'DeepSkyBlue' # 'SystemWindow' 'DeepSkyBlue'


        ##########
        # Header #
        ##########
        # Heading
        tk.Label(self, text="Speaker Balancer", bg=custom_color,
                 font=('TkDefaultFont', 20), 
                 #borderwidth=0.5, 
                 #relief='groove'
                 ).grid(row=5, column=5, sticky='nsew')

        # ttk.Separator(self, orient='horizontal').grid(row=10, column=5, 
        #     columnspan=30, sticky='we')


        #################
        # Create frames #
        #################
        options = {'padx':10, 'pady':10}
        options_small = {'padx':5, 'pady':5}
        
        # Main frame
        frm_main = ttk.Frame(self)
        frm_main.grid(column=5, row=15, **options)

        # Top container
        lfrm_top = ttk.LabelFrame(frm_main, text="Controls")
        lfrm_top.grid(column=5, row=5, **options)

        # Playback controls frame
        lfrm_playback = ttk.LabelFrame(lfrm_top, text="Playback")
        lfrm_playback.grid(column=5, row=5, rowspan=30, **options, 
                           sticky='n')

        # SLM measured value frame
        lfrm_slm = ttk.LabelFrame(lfrm_top, text="Offsets")
        lfrm_slm.grid(column=10, row=5, **options, sticky='nsew')

        # Offset button frame
        lfrm_make_file = ttk.LabelFrame(lfrm_top, text="Save Offsets")
        lfrm_make_file.grid(column=10, columnspan=30, row=10, padx=10, 
                            sticky='nsew')
        lfrm_make_file.columnconfigure(5, weight=1)

        # SEPARATOR
        ttk.Separator(frm_main, orient='horizontal').grid(row=10, column=5, 
            columnspan=30, **options, sticky='we')

        # Speaker frame
        self.lfrm_speakers = ttk.LabelFrame(frm_main, text="Speaker Number")
        self.lfrm_speakers.grid(column=5, columnspan=20, row=15, 
                           **options, sticky='nsew')

        # Offset frame
        lfrm_offsets = ttk.LabelFrame(frm_main, text="Offsets")
        lfrm_offsets.grid(column=15, row=5, 
                          **options, sticky='nsew')


        #########################
        # Presentation Controls #
        #########################
        # Duration
        ttk.Label(lfrm_playback, text="Duration (s):").grid(
            column=5, row=5, sticky='e', **options_small)
        ent_dur = ttk.Entry(lfrm_playback, 
            textvariable=self.settings['duration'], width=6)
        ent_dur.grid(column=10, row=5, sticky='w', **options_small)

        # Level
        ttk.Label(lfrm_playback, text="Level (dB):").grid(
            column=5, row=10, sticky='e', **options_small)
        ent_slm = ttk.Entry(lfrm_playback, 
            textvariable=self.settings['level'], width=6)
        ent_slm.grid(column=10, row=10, sticky='w', **options_small)
 
        # Play stimulus
        btn_play = ttk.Button(lfrm_playback, text="Play", 
            command=self._on_play)
        btn_play.grid(column=5, row=15, columnspan=6, sticky='ew', 
            **options_small)

        # Stop stimulus
        btn_stop = ttk.Button(lfrm_playback, text="Stop", 
            command=self._on_stop)
        btn_stop.grid(column=5, row=20, columnspan=6, sticky='ew', 
            **options_small)


        ##########################
        # Measured Level Widgets #
        ##########################
        # SLM reading entry box
        ttk.Label(lfrm_slm, text="SLM Reading (dB):").grid(
            column=5, row=15, sticky='e', **options_small)
        self.ent_slm = ttk.Entry(lfrm_slm, 
            textvariable=self._vars['slm_reading'],
            width=6)
        self.ent_slm.grid(column=10, row=15, sticky='w', **options_small)   

        # Submit button
        self.btn_submit = ttk.Button(lfrm_slm, text="Calculate Offset", 
            command=self._on_submit)
        self.btn_submit.grid(column=5, columnspan=10, row=20, sticky='nsew', 
            **options_small)


        #################
        # Offset Button #
        #################
        ttk.Button(lfrm_make_file, text="Make Offset File", 
            command=self._on_save).grid(row=5, column=5, columnspan=20, 
            padx=5, pady=5, sticky='nswe'
        )


        #########################
        # Speaker Radio Buttons #
        #########################
        self.radio_list = []
        self.label_list = []
        self.offset_labels = []
        # Create offset labels and speaker buttons
        for channel in range(0, self._num_speakers):
            # Offset labels: vertical Labels to display offsets
            lbl_speaker_offset = ttk.Label(
                lfrm_offsets, text=f"{channel+1}: -")
            lbl_speaker_offset.grid(
                column=5, row=channel, sticky='w', padx=5)
            self.offset_labels.append(lbl_speaker_offset)

            # Speaker number labels: speaker LabelFrame
            lbl_speaker_num = ttk.Label(
                self.lfrm_speakers, text=channel+1)
            lbl_speaker_num.grid(
                column=channel, row=5, sticky='w', padx=(5,0))
            self.label_list.append(lbl_speaker_num)
            # Speaker number radiobuttons" speaker LabelFrame
            rad_speaker_num = ttk.Radiobutton(
                self.lfrm_speakers,
                text='',
                takefocus=0,
                value=channel,
                variable=self._vars['selected_speaker']
            )
            rad_speaker_num.grid(column=channel, row=10, padx=2)
            self.radio_list.append(rad_speaker_num)

        # Select first speaker
        self._vars['selected_speaker'].set(0)


    #############
    # Functions #
    #############
    def _next_speaker(self):
        """ Calculate next speaker to advance to. """
        next_speaker = self._vars['selected_speaker'].get() + 1
        if next_speaker >= self.settings['num_speakers'].get():
            next_speaker = 0
        self._vars['selected_speaker'].set(next_speaker)
        return next_speaker


    def _on_submit(self):
        """ Send submit event to controller. """
        self.event_generate('<<MainSubmit>>')

        # Select next speaker
        self._next_speaker()


    def update_offset_labels(self, channel, offset):
        """ Display calculated offset in offset label frame. """
        self.offset_labels[channel].configure(text=f"{channel+1}: {offset}")


    def _update_speaker_frame_label(self, text):
        """ Update the LabelFrame text containing the speaker radio 
            buttons. 
        """
        # Configure LabelFrame text with provided text
        self.lfrm_speakers.configure(text=text)


    def _update_all_speaker_buttons_state(self, state):
        """ Change status of all radio buttons to STATUS
            ('enabled' or 'disabled').
        """
        # Update status for each speaker radio button in list
        for btn in self.radio_list:
            btn.configure(state=state)

        # Update status for each speaker label in list
        for btn in self.label_list:
            btn.configure(state=state)


    def start_auto_test(self):
        """ Update GUI for automated test protocol. """
        # Disable all speaker radio buttons
        self._update_all_speaker_buttons_state(state='disabled')

        # Update speaker button frame text
        self.lfrm_speakers.configure(text="Test in Progress...")


    def end_auto_test(self):
        """ Update GUI for automated test protocol. """
        # Enable all speaker radio buttons
        self._update_all_speaker_buttons_state(state='enabled')

        # Update speaker button frame text
        self.lfrm_speakers.configure(text="Speaker Number")


    def _update_single_speaker_button_state(self, speaker_num, state):
        """ Change status of the specified radio button
            to STATUS ('enabled' or 'disabled').
        """
        # Update status for each radio button in list
        self.radio_list[speaker_num].configure(state=state)
        self.label_list[speaker_num].configure(state=state)


    def _on_save(self):
        """ Send save event to controller. """
        self.event_generate('<<MainSave>>')


    def _on_play(self):
        """ Send start audio playback event to controller. """
        self.settings['channel_routing'].set(
            self._vars['selected_speaker'].get()+1)
        self.event_generate('<<MainPlay>>')


    def _on_stop(self):
        """ Send stop audio playback event to controller. """
        self.event_generate('<<MainStop>>')
