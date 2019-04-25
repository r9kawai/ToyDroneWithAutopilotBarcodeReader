# This source code is only ring a beep sound.

import threading
import subprocess

class Beep:
    def __init__(self):
        self.cmd = 'aplay beep.wav'

    def __del__(self):
        if hasattr(self, 'threadhdl'):
            del self.threadhdl

    def on(self):
        if hasattr(self, 'threadhdl'):
            del self.threadhdl
        self.threadhdl = threading.Thread(target = self._threadfunc)
        self.threadhdl.start()

    def _threadfunc(self):
        subprocess.call(self.cmd.split())

#eof
