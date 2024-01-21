from Executioners.AExecutioner import AExecutioner
import random

"""
Executes a plan step by step. 
The actions 'pickup' and 'stack' may fail with a set probability.
When an action fails a message is logged with the reason the action failed and the plan execution is stopped.
"""


class BlocksFailingExecutionerWithStateTracking(AExecutioner):
    failing_probability = None
    state = None

    def __init__(self, log_event_callback, failing_probability: float, initial_state, post_action_callback=None):
        super().__init__(log_event_callback, post_action_callback)
        self.failing_probability = failing_probability
        self.state = initial_state.copy()

    def get_current_state(self):
        return self.state.copy()

    def execute_plan(self, plan: list, log_state: bool = False):
        super().execute_plan(plan)

        number_of_actions = len(plan)
        self.log_event(f"The robot is now executing the plan. There are a total of {number_of_actions} actions to execute.")

        # Foreach action in the plan
        for index, action in enumerate(plan):
            action_success = self._execute_action(index, action)

            if log_state:
                self.state.display("Here is the state after the action was executed:")

            if not action_success:
                return

            self.on_post_action()

        self.log_event("The plan was executed correctly")

    def _execute_action(self, index, action) -> bool:
        action_failed = self._can_action_fail(action) and self._should_action_fail(action)
        self._update_state(action, action_failed)

        if action_failed:
            # Action failed
            self.log_event(f" {index + 1}. The action {action} failed to execute")
            self._fail_action(action)
            self.log_event("Plan execution stopped")
            return False
        else:
            # Action executed successfully
            self.log_event(f" {index + 1}. The action {action} was executed correctly")
            return True

    def _update_state(self, action, action_failed: bool):
        action_name = action[0]

        if action_name == 'pickup':
            self._domain_action_pickup(action[1], action_failed)
        elif action_name == 'unstack':
            self._domain_action_unstack(action[1], action[2])
        elif action_name == 'putdown':
            self._domain_action_putdown(action[1])
        elif action_name == 'stack':
            self._domain_action_stack(action[1], action[2], action_failed)
        else:
            raise Exception(f"Unknown action name {action_name}")



    def _can_action_fail(self, action):
        action_name = action[0]
        return action_name in ['pickup', 'stack']

    def _should_action_fail(self, action):
        random_number = random.random()  # number in [0, 1)
        return random_number < self.failing_probability

    def _fail_action(self, action):
        action_name = action[0]
        if action_name == 'pickup':
            # pickup action failed
            # let's pretend we noticed the robot's hand was empty after attempting to pick something up
            self.log_event("No object detected in the robot's hand after a pickup was executed")
        elif action_name == 'stack':
            # stack action failed
            # let's pretend we have a stack height sensor and it's giving us some wrong value
            self.log_event("Unexpected stack height value after a stack action. The stack height did not increase.")

    def _domain_action_pickup(self, x, action_failed: bool):
        # if the action fails the item will not move (state remains unchanged)
        if self.state.pos[x] == 'table' and self.state.clear[x] == True and self.state.holding['hand'] == False and not action_failed:
            self.state.pos[x] = 'hand'
            self.state.clear[x] = False
            self.state.holding['hand'] = x

    def _domain_action_unstack(self, b1, b2):
        if self.state.pos[b1] == b2 and b2 != 'table' and self.state.clear[b1] == True and self.state.holding['hand'] == False:
            self.state.pos[b1] = 'hand'
            self.state.clear[b1] = False
            self.state.holding['hand'] = b1
            self.state.clear[b2] = True

    def _domain_action_putdown(self, b1):
        if self.state.pos[b1] == 'hand':
            self.state.pos[b1] = 'table'
            self.state.clear[b1] = True
            self.state.holding['hand'] = False

    # put b1 on top of b2
    def _domain_action_stack(self, b1, b2, action_failed):
        # if the action fails, the object will be put in a different location
        if self.state.pos[b1] == 'hand' and self.state.clear[b2] is True:
            if action_failed:
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

    """
    Chooses a random block from the list of Clear blocks, excluding a specified block name
    If no clear block is found, 'table' is retuned
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

