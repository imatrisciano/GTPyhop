from abc import ABC, abstractmethod


class AExecutioner(ABC):
    log_event_callback = None
    post_action_callback = None

    @abstractmethod
    def __init__(self, log_event_callback, post_action_callback=None):
        self.log_event_callback = log_event_callback
        self.post_action_callback = post_action_callback
        pass

    @abstractmethod
    def execute_plan(self, plan: list):
        pass

    def log_event(self, event: str, print_to_console: bool = True):
        if self.log_event_callback is not None:
            self.log_event_callback(event)

        if print_to_console:
            print(event)

    def on_post_action(self):
        if self.post_action_callback is not None:
            self.post_action_callback()
