

class InterruptHandler():
    def __init__(self):
        self.enabled = True
        self._if = 0

    @property
    def if_(self):
        return self._if

    @if_.setter
    def if_(self, value):
        self._if = value

    def ei(self):
        self.enabled = True

    def di(self):
        self.enabled = False

    def has_interrupt(self) -> bool:
        return False
