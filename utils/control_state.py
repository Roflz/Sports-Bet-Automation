# control_state.py
control_flags = {
    "pause": False,
    "bet_changed": False,
    "log_event": False
}

class ControlState:
    def __init__(self):
        self.web_interactor_bet365 = None

    def set_web_interactor_bet365(self, instance):
        self.web_interactor_bet365 = instance

    def get_web_interactor_bet365(self):
        return self.web_interactor_bet365


control_state = ControlState()