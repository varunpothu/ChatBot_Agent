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
    from storage.conversation_memory import PostgresConversationMemory

    store = PostgresConversationMemory(Engine("What is the course fee?"))
    assert store.resolve("conversation-1", "And when is it due?") == "What is the course fee? And when is it due?"


def test_normal_question_is_not_prefixed():
    from storage.conversation_memory import PostgresConversationMemory

    store = PostgresConversationMemory(Engine("What is the course fee?"))
    assert store.resolve("conversation-1", "What documents do I need?") == "What documents do I need?"


def test_local_conversation_can_be_deleted():
    from agents.conversation import ConversationMemory

    store = ConversationMemory()
    store.remember("conversation-1", "What is the fee?", "fees")
    assert store.delete("conversation-1") is True
    assert store.resolve("conversation-1", "And when is it due?") == "And when is it due?"
