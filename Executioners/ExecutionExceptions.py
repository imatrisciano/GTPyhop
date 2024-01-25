class PreconditionsNotMetException(Exception):
    @staticmethod
    def check_predicate(predicate: bool, fail_message: str = None):
        if not predicate:
            raise PreconditionsNotMetException(fail_message)


class ExecutionFailedException(Exception):
    pass
