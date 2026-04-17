from know_ops_mcp.knowledge import serializer


def test_round_trip_preserves_metadata_and_content():
    metadata = {
        "unique_name": "round-trip",
        "type": "general",
        "title": "Round trip",
        "description": "Verify serialize/deserialize symmetry.",
        "tags": ["test", "round-trip"],
    }
    content = "# Body\n\nMultiple paragraphs.\n\nWith blank lines."

    text = serializer.serialize(metadata, content)
    meta_out, content_out = serializer.deserialize(text)

    assert meta_out == metadata
    assert content_out == content


def test_empty_content_round_trips():
    metadata = {"unique_name": "empty", "type": "general"}
    text = serializer.serialize(metadata, "")
    meta_out, content_out = serializer.deserialize(text)
    assert meta_out == metadata
    assert content_out == ""


def test_unicode_round_trips():
    metadata = {"unique_name": "unicode", "type": "general", "title": "한글 제목"}
    content = "본문에 한글, emoji 🚀, и кириллица."
    text = serializer.serialize(metadata, content)
    meta_out, content_out = serializer.deserialize(text)
    assert meta_out == metadata
    assert content_out == content
