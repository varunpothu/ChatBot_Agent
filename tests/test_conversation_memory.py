from storage.conversation_memory import PostgresConversationMemory


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class Connection:
    def __init__(self, previous):
        self.previous = previous

    def execute(self, *_args, **_kwargs):
        return Result(self.previous)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class Engine:
    def __init__(self, previous):
        self.previous = previous

    def connect(self):
        return Connection(self.previous)


def test_follow_up_resolution_uses_previous_query_only():
    store = PostgresConversationMemory(Engine("What is the course fee?"))
    assert store.resolve("conversation-1", "And when is it due?") == "What is the course fee? And when is it due?"


def test_normal_question_is_not_prefixed():
    store = PostgresConversationMemory(Engine("What is the course fee?"))
    assert store.resolve("conversation-1", "What documents do I need?") == "What documents do I need?"
