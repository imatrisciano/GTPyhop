from llm_module import LLMModule
import gtpyhop
from Executioners.GenericRandomFailingExecutioner import GenericRandomFailingExecutioner

the_domain = gtpyhop.Domain(__package__)  # must be defined before importing any actions

from Examples.blocks_htn.methods import *
from Examples.blocks_htn.actions import *

llm = LLMModule(
    model_path="../../models/solar-10.7b-instruct-v1.0.Q5_K_M.gguf",
    n_threads=16,
    context_size=16 * 1024)


def main():
    setup_llm()
    plan = generate_plan()

    executioner = GenericRandomFailingExecutioner(log_event_callback=llm.log_event, post_action_callback=ask_question, failing_probability=1/6)
    executioner.execute_plan(plan)

    """
    #  Here is the plan: [('unstack', 'a', 'b'), ('putdown', 'a'), ('pickup', 'b'), ('stack', 'b', 'a'), ('pickup', 'c'), ('stack', 'c', 'b')]
    llm.log_event("\nThe executioner is now executing the plan")

    llm.log_event(" 1. action ('unstack', 'a', 'b') executed successfully", print_event=True)
    llm.log_event(" 2. action ('putdown', 'a') executed successfully", print_event=True)
    llm.log_event(" 3. action ('pickup', 'b') executed successfully", print_event=True)
    llm.log_event(" 4. action ('stack', 'b', 'a') executed successfully", print_event=True)
    llm.log_event(" 5. action ('pickup', 'c') failed execution", print_event=True)
    # llm.log_event("Could not find object 'c' in scene", print_event=True)
    #llm.log_event(" 5. action ('pickup', 'c') executed successfully", print_event=True)
    #llm.log_event(" 6. action ('stack', 'c', 'b') executed successfully", print_event=True)
    """

    ask_question()
    print("Execution completed. Now exiting.")


def ask_question():
    while True:
        print("===================================================")
        print(" ## Enter a question or leave empty to continue ## ")
        question = input(" > Question: ")  # Example: "What is the current goal? Can you please describe the plan?"

        if len(question) == 0:
            return  # exit the loop

        print("Generating the answer...")
        llm.prompt(question, max_tokens=8192)

        print()
        print()


def setup_llm() -> None:
    llm.load()
    gtpyhop.event_callback = llm.log_event


def generate_plan() -> list:
    # gtpyhop.print_domain()  # this will also inform the LLM about the domain

    state1 = gtpyhop.State(state_name='state1')
    state1.pos = {
        'a': 'b',  # 'a' is on 'b'
        'b': 'table',  # 'b' is on the table
        'c': 'table'  # 'c' is on the table
    }
    state1.clear = {
        'c': True,  # 'c' is clear
        'b': False,  # 'b' is not clear ('a' is on top)
        'a': True  # 'a' is clear
    }
    state1.holding = {
        'hand': False
    }

    # displaying the state will also inform the LLM
    state1.display(heading="Here is the description for the initial state named")

    goal1a = gtpyhop.Multigoal(multigoal_name='goal1a')
    goal1a.pos = {
        'c': 'b',  # 'c' on 'b'
        'b': 'a',  # 'b' on 'a'
        'a': 'table'  # 'a' on the table
    }

    # displaying the goal will also inform the LLM
    goal1a.display(heading="Here is a description of the goal named")

    # find_plan will also inform the LLM
    plan = gtpyhop.find_plan(state=state1, todo_list=[('achieve', goal1a)])
    return plan


if __name__ == "__main__":
    main()
