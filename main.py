from llm_module import LLMModule
import gtpyhop
from Executioners.GenericRandomFailingExecutioner import GenericRandomFailingExecutioner
from Executioners.BlocksFailingExecutioner import BlocksFailingExecutioner
from Executioners.BlocksFailingExecutionerWithStateTracking import BlocksFailingExecutionerWithStateTracking

the_domain = gtpyhop.Domain(__package__)  # must be defined before importing any actions

from Examples.blocks_htn.methods import *
from Examples.blocks_htn.actions import *

llm = LLMModule(
    model_path="../../models/solar-10.7b-instruct-v1.0.Q5_K_M.gguf",
    n_threads=16,
    context_size=16 * 1024)


class Colours:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def print_coloured(text: str, colour):
        print(colour + text + Colours.ENDC)

    @staticmethod
    def set_colour(colour):
        print(colour, end='')

    @staticmethod
    def reset():
        print(Colours.ENDC, end='')


def main():
    initial_state = generate_initial_state()
    setup_llm()
    plan = generate_plan(initial_state)

    #executioner = GenericRandomFailingExecutioner(log_event_callback=llm.log_event, post_action_callback=ask_question, failing_probability=1/6)
    #executioner = BlocksFailingExecutioner(log_event_callback=llm.log_event, post_action_callback=ask_question, failing_probability=1/6)
    executioner = BlocksFailingExecutionerWithStateTracking(log_event_callback=llm.log_event, initial_state=initial_state,
                                                            post_action_callback=ask_question, failing_probability=1/2)

    executioner.execute_plan(plan, log_state=True)

    ask_question()
    print("Execution completed. Now exiting.")


def generate_initial_state():
    initial_state = gtpyhop.State(state_name='state1')
    initial_state.pos = {
        'a': 'b',  # 'a' is on 'b'
        'b': 'table',  # 'b' is on the table
        'c': 'table'  # 'c' is on the table
    }
    initial_state.clear = {
        'c': True,  # 'c' is clear
        'b': False,  # 'b' is not clear ('a' is on top)
        'a': True  # 'a' is clear
    }
    initial_state.holding = {
        'hand': False  # the hand is clear
    }
    return initial_state


def ask_question():
    while True:
        Colours.set_colour(Colours.HEADER)
        print("===================================================")
        print(" ## Enter a question or leave empty to continue ## ")
        Colours.set_colour(Colours.OKBLUE)
        question = input(" > Question: ")  # Example: "What is the current goal? Can you please describe the plan?"

        if len(question.strip()) == 0:
            Colours.reset()
            return  # exit the loop

        Colours.print_coloured("Generating the answer...", Colours.HEADER)
        Colours.set_colour(Colours.OKCYAN)
        llm.prompt(question, max_tokens=8192, memorize_message=True)
        Colours.reset()
        print()
        print()


def setup_llm() -> None:
    llm.load()
    gtpyhop.event_callback = llm.log_event


def generate_plan(initial_state) -> list:
    # gtpyhop.print_domain()  # this will also inform the LLM about the domain

    # displaying the state will also inform the LLM
    initial_state.display(heading="Here is the description for the initial state named")

    goal1a = gtpyhop.Multigoal(multigoal_name='goal1a')
    goal1a.pos = {
        'c': 'b',  # 'c' on 'b'
        'b': 'a',  # 'b' on 'a'
        'a': 'table'  # 'a' on the table
    }

    # displaying the goal will also inform the LLM
    goal1a.display(heading="Here is a description of the goal named")

    # find_plan will also inform the LLM
    plan = gtpyhop.find_plan(state=initial_state, todo_list=[('achieve', goal1a)])
    return plan


if __name__ == "__main__":
    main()
