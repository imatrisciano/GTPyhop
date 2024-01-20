from Executioners.AExecutioner import AExecutioner
import random

"""
Executes a plan step by step. 
The actions 'pickup' and 'putdown' may fail with a set probability.
When an action fails a message is logged with the reason the action failed and the plan execution is stopped.
"""


class BlocksFailingExecutioner(AExecutioner):
    failing_probability = None

    def __init__(self, log_event_callback, failing_probability: float, post_action_callback=None):
        super().__init__(log_event_callback, post_action_callback)
        self.failing_probability = failing_probability

    def execute_plan(self, plan: list):
        super().execute_plan(plan)

        number_of_actions = len(plan)
        self.log_event(f"The robot is now executing the plan. There are a total of {number_of_actions} actions to execute.")

        # Foreach action in the plan
        for index, action in enumerate(plan):
            if self._can_action_fail(action) and self._should_action_fail(action):
                # Action failed
                self.log_event(f" {index+1}. The action {action} failed to execute")
                self._fail_action(action)
                self.log_event("Plan execution stopped")
                return
            else:
                # Action executed successfully
                self.log_event(f" {index+1}. The action {action} was executed correctly")

            self.on_post_action()

        self.log_event("The plan was executed correctly")

    def _can_action_fail(self, action):
        action_name = action[0]
        return action_name in ['pickup', 'putdown']

    def _should_action_fail(self, action):
        random_number = random.random() # number in [0, 1)
        return random_number < self.failing_probability

    def _fail_action(self, action):
        action_name = action[0]
        if action_name == 'pickup':
            # pickup action failed
            # let's pretend we noticed the robot's hand was empty after attempting to pick something up
            self.log_event("No object detected in the robot's hand after a pickup was executed")
        elif action_name == 'putdown':
            # putdown action failed
            # let's pretend we have a stack height sensor and it's giving us some wrong value
            self.log_event("Unexpected stack height value after a putdown action. The stack height did not increase.")
