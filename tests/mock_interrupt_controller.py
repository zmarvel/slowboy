

import slowboy.interrupts

class MockInterruptController(slowboy.interrupts.InterruptListener):
    def __init__(self):
        self.ie = 0
        self.last_interrupt = None

    def notify_interrupt(self, interrupt):
        self.last_interrupt = interrupt

    def acknowledge_interrupt(self, interrupt):
        pass
