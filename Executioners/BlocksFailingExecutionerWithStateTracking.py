from Executioners.AExecutioner import AExecutioner
import random

from Executioners.ExecutionExceptions import *

"""
Executes a plan step by step. 
The actions 'pickup' and 'stack' may fail with a set probability.
When an action fails a message is logged with the reason the action failed and the plan execution is stopped.
"""


class BlocksFailingExecutionerWithStateTracking(AExecutioner):
    failing_probability = None
    state = None
    failed_plan_counter: int = 0

    def __init__(self, log_event_callback, failing_probability: float, initial_state, post_action_callback=None):
        super().__init__(log_event_callback, post_action_callback)
        self.failing_probability = failing_probability
        self.state = initial_state.copy()

    def get_current_state(self):
        return self.state.copy()

    def execute_plan(self, plan: list, log_state: bool = False) -> bool:
        """
        Executes the given plan.
        Returns True if the execution was successful, False if it failed
        """
        super().execute_plan(plan)

        number_of_actions = len(plan)
        self.log_event(f"The robot is now executing the plan. There are a total of {number_of_actions} actions to execute.")

        # Foreach action in the plan
        for index, action in enumerate(plan):
            action_success = self._execute_action(index, action)
            self.state.__name__ = f"{self.failed_plan_counter}-state_after_action_{index + 1}"

            if log_state:
                self.state.display("Here is the state after the action was executed:")

            if not action_success:
                self.failed_plan_counter += 1
                return False

            self.on_post_action()

        self.log_event("The plan was executed correctly")
        return True

    def _execute_action(self, index, action) -> bool:
        action_name = action[0]
        fail_reason: str = ""

        try:
            if action_name == 'pickup':
                self._domain_action_pickup(action[1])
            elif action_name == 'unstack':
                self._domain_action_unstack(action[1], action[2])
            elif action_name == 'putdown':
                self._domain_action_putdown(action[1])
            elif action_name == 'stack':
                self._domain_action_stack(action[1], action[2])
            else:
                raise Exception(f"Unknown action name {action_name}")

            self.log_event(f" {index + 1}. The action {action} was executed correctly")
            return True
        except PreconditionsNotMetException as exc:
            fail_reason = f"Preconditions are not met: {str(exc)}"
        except ExecutionFailedException as exc:
            fail_reason = f"Action execution failed: {str(exc)}"

        self.log_event(f" {index + 1}. The action {action} failed to execute. Reason: {fail_reason}")
        self.log_event("Plan execution stopped")
        return False

    def _can_action_fail(self, action):
        action_name = action[0]
        return action_name in ['pickup', 'stack']

    def _should_action_fail(self):
        random_number = random.random()  # number in [0, 1)
        return random_number < self.failing_probability

    def _domain_action_pickup(self, x):
        PreconditionsNotMetException.check_predicate(self.state.pos[x] == 'table', f"Block '{x}' is not on the table")
        PreconditionsNotMetException.check_predicate(self.state.clear[x] is True, f"Block '{x}' is not clear")
        PreconditionsNotMetException.check_predicate(self.state.holding['hand'] is False, f"Block '{x}' is not being held in the hand")

        # if the action fails the item will not move (state remains unchanged)
        if self._should_action_fail():
            # let's pretend we noticed the robot's hand was empty after attempting to pick something up
            raise ExecutionFailedException(f"No object detected in the robot's hand after a pickup for block '{x}' was executed")

        self.state.pos[x] = 'hand'
        self.state.clear[x] = False
        self.state.holding['hand'] = x

    def _domain_action_unstack(self, b1, b2):
        PreconditionsNotMetException.check_predicate(self.state.pos[b1] == b2, f"Block '{b1}' is not on top of block '{b2}'")
        PreconditionsNotMetException.check_predicate(b2 != 'table', f"Block {b2} is the table")
        PreconditionsNotMetException.check_predicate(self.state.clear[b1] is True, f"Block '{b1}' is not clear and can't be picked up")
        PreconditionsNotMetException.check_predicate(self.state.holding['hand'] is False, f"The robot's hand is not free")

        self.state.pos[b1] = 'hand'
        self.state.clear[b1] = False
        self.state.holding['hand'] = b1
        self.state.clear[b2] = True

    def _domain_action_putdown(self, b1):
        PreconditionsNotMetException.check_predicate(self.state.pos[b1] == 'hand', f"Block '{b1}' is not in the robot's hand")

        self.state.pos[b1] = 'table'
        self.state.clear[b1] = True
        self.state.holding['hand'] = False

    # put b1 on top of b2
    def _domain_action_stack(self, b1, b2):
        PreconditionsNotMetException.check_predicate(self.state.pos[b1] == 'hand', f"Block '{b1}' is not in the robot's hand")
        PreconditionsNotMetException.check_predicate(self.state.clear[b2] is True, f"Block '{b2}' is not clear and thus it's not accessible")

        # if the action fails, the object will be put in a different location
        if self._should_action_fail():
            # if the action fails, put the block down on a wrong spot
            # choose the spot randomly from the available ones except b2
            # if no clear block is found, than 'table' is returned
            wrong_spot = self._find_random_available_spot(block_to_exclude=b2)
            print(f" ###> Action 'stack' failed, putting '{b1}' on top of '{wrong_spot}' instead of '{b2}'")
            b2 = wrong_spot

            self.state.pos[b1] = b2
            self.state.clear[b1] = True
            self.state.holding['hand'] = False
            self.state.clear[b2] = False

            # let's pretend we have a stack height sensor, and it's giving us some wrong value
            raise ExecutionFailedException("Unexpected stack height value after a stack action. The stack height did not increase.")
        else:
            self.state.pos[b1] = b2
            self.state.clear[b1] = True
            self.state.holding['hand'] = False
            self.state.clear[b2] = False

    """
    Chooses a random block from the list of Clear blocks, excluding a specified block name
    If no clear block is found, 'table' is returned
    """
    def _find_random_available_spot(self, block_to_exclude) -> str:
        # choose blocks that are Clear and that are not equal to 'block_to_exclude'
        clear_items_dictionary = self.state.clear
        clear_blocks = [block_name for block_name, block_is_clear in clear_items_dictionary.items()
                        if block_is_clear is True and block_name != block_to_exclude]

        if len(clear_blocks) == 0:
            # no blocks available, return the table
            return 'table'
        else:
            # return a random block from the ones that are clear
            return random.choice(clear_blocks)

