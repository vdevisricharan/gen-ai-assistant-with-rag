from backend.storage import Database


def test_storage_persists_chunks_and_messages(tmp_path):
    database = Database(tmp_path / "rag.sqlite3")

    document_id = database.insert_document("Reset Password", "Reset content")
    database.insert_chunk(document_id, "Reset Password", 0, "Reset content", [1.0, 0.0])
    database.append_message("s1", "user", "hello")
    database.append_message("s1", "assistant", "hi")

    chunks = database.fetch_chunks()
    messages = database.fetch_recent_messages("s1", pair_limit=1)

    assert database.count_chunks() == 1
    assert chunks[0].embedding == [1.0, 0.0]
    assert [message.role for message in messages] == ["user", "assistant"]


def test_recent_messages_are_trimmed_to_pair_limit(tmp_path):
    database = Database(tmp_path / "rag.sqlite3")
    for index in range(6):
        database.append_message("s1", "user", f"q{index}")
        database.append_message("s1", "assistant", f"a{index}")

    messages = database.fetch_recent_messages("s1", pair_limit=5)

    assert len(messages) == 10
    assert messages[0].content == "q1"
    assert messages[-1].content == "a5"
