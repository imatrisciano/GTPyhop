from Executioners.AExecutioner import AExecutioner
import random

"""
Executes a plan step by step. Each action fails with a set probability, stopping the plan execution.
"""


class GenericRandomFailingExecutioner(AExecutioner):
    failing_probability = None

    def __init__(self, log_event_callback, failing_probability: float, post_action_callback=None):
        super().__init__(log_event_callback, post_action_callback)
        self.failing_probability = failing_probability

    def execute_plan(self, plan: list) -> bool:
        """ Executes the given plan.
        Returns True if the execution was successful, False if it failed"""
        super().execute_plan(plan)

        number_of_actions = len(plan)
        self.log_event(f"The robot is now executing the plan. There are a total of {number_of_actions} actions to execute.")

        # Foreach action in the plan
        for index, action in enumerate(plan):
            if self._should_action_fail():
                # Action failed
                self.log_event(f" {index+1}. The action {action} failed to execute")
                self.log_event("Plan execution stopped")
                return False
            else:
                # Action executed successfully
                self.log_event(f" {index+1}. The action {action} was executed correctly")

            self.on_post_action()

        self.log_event("The plan was executed correctly")
        return True

    def _should_action_fail(self):
        random_number = random.random() # number in [0, 1)
        return random_number < self.failing_probability
