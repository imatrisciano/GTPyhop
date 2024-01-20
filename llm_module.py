import os
from llama_cpp import Llama


class LLMModule:
    SYSTEM_MESSAGE_FILE_PATH: str = "system_message.txt"
    model_path: str
    context_size: int
    n_threads: int
    messages_history: list

    _llm = None
    _system_message: str = ""
    _event_log: str = ""

    def __init__(self, model_path: str, n_threads: int = 0, context_size: int = 16384):
        self.model_path = model_path
        self.n_threads = n_threads
        self.context_size = context_size
        self.messages_history = []

    def load(self) -> None:
        print("Loading LLM module...")
        self._llm = Llama(
            model_path=self.model_path,
            n_threads=self.n_threads,
            n_ctx=self.context_size,
            n_gpu_layers=-1)

        if self._llm is not None:
            print("Model loaded")
        else:
            print("Model loading failed")

        self._load_system_message()

    # Loads the system prompt from file
    def _load_system_message(self) -> None:
        print(f"Loading system prompt from file: {self.SYSTEM_MESSAGE_FILE_PATH}")

        # check if the file exists
        if os.path.exists(self.SYSTEM_MESSAGE_FILE_PATH):
            # open and read the file
            with open(self.SYSTEM_MESSAGE_FILE_PATH, encoding="utf-8") as f:
                self._system_message = f.read()
            print("System prompt loaded")
        else:
            # use an empty prompt
            self._system_message = ""
            print("System prompt file does not exist, using empty prompt")

    # Adds a new event to the event log
    def log_event(self, event: str, print_event: bool = False) -> None:
        self._event_log += event + "\n"
        if (print_event):
            print(event)

    # Generates the system prompt concatenating the system message and the event log
    def _generate_complete_system_prompt(self):
        return f"{self._system_message}\n{self._event_log}"

    # Generates a SYSTEM+USER+ASSISTANT prompt
    # # The format must be compatible with the current model
    def _generate_complete_prompt(self, question: str):
        return (
                "### System:\n" +
                self._generate_complete_system_prompt() +
                self._get_messages_history() +
                "\n\n### User:\n"
                + question +
                "\n\n### Assistant:\n")

    def _get_messages_history(self) -> str:
        text = ""
        for message in self.messages_history:
            question = message["question"]
            answer = message["answer"]
            text += f"\n\n### User:\n{question}\n\n### Assistant:\n{answer}"
        return text

    # Prompts the LLM and prints the output
    def prompt(self, question: str, max_tokens=128, memorize_message=False) -> None:
        # generate the prompt
        prompt: str = self._generate_complete_prompt(question)

        # check if the context fits in the context size
        if len(prompt) > self.context_size:
            print("WARN: current log is bigger than the specified context length, answer will be sub-optimal")

        message = {
            "question": question,
            "answer": ""
        }

        # generate a streamed output
        model_output = self._llm.create_completion(prompt, stream=True, max_tokens=max_tokens)

        # print the streamed result
        for item in model_output:
            new_text = item['choices'][0]['text']
            message["answer"] += new_text
            print(new_text, end='')

        if memorize_message:
            self.messages_history.append(message)

        print()

