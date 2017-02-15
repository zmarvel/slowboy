

class InterruptHandler():
    def __init__(self):
        self.enabled = True

    def ei(self):
        self.enabled = True

    def di(self):
        self.enabled = False

    def has_interrupt(self) -> bool:
        return False
