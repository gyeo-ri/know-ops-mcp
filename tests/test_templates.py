from know_ops_mcp import templates


def test_style_guide_loads_non_empty():
    guide = templates.load_style_guide()
    assert "Key namespace" in guide
    assert "projects/<project>" in guide


def test_every_declared_doc_type_has_a_template():
    for doc_type in templates.DOC_TYPES:
        template = templates.load_template(doc_type)
        assert template is not None, doc_type
        assert f"Template: {doc_type}" in template


def test_unknown_doc_type_returns_none():
    assert templates.load_template("does-not-exist") is None
