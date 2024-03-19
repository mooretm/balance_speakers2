
import tkinter as tk
from tkinter import ttk

import numpy as np

import importlib

import random
import threading



class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geometry("250x250")

        ttk.Button(self, text="Play Audio", command=self.play_audio).grid()

        self.import_flag = True


    def wgn(self, dur, fs):
        """ Function to generate white Gaussian noise.
        """
        r = int(dur * fs)
        random.seed(4)
        wgn = [random.gauss(0.0, 1.0) for i in range(r)]
        wgn -= np.mean(wgn) # Remove DC offset
        wgn = wgn / np.max(abs(wgn)) # Normalize
        return wgn


    def play_audio(self):
        # Delete thread object
        try:
            del self.t
        except AttributeError:
            pass

        # Create and call Thread object
        try:
            self.t = threading.Thread(target=self.play_audio_thread)
            self.t.start()
        except:
            print("\nfailed to start Thread!")


    def play_audio_thread(self):
        import sounddevice
        id = 12
        fs = 44100
        dur = 2
        sounddevice.default.device = id
        print(f"audio device: {sounddevice.query_devices(sounddevice.default.device)['name']}")

        _wgn = self.wgn(dur, fs)
        _wgn = _wgn * 0.2

        for ii in range(0,2):
            try:
                print(f"\nIteration: {ii}")
                sounddevice.play(_wgn, fs)
                sounddevice.wait(dur)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    app = Application()
    app.mainloop()
