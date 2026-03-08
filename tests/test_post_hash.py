from hptraffic.content_hash import build_content_hash


def test_same_content_has_same_hash_after_normalization() -> None:
    first_hash = build_content_hash(
        title="Hello   World", content="Visit https://example.com for DETAILS"
    )
    second_hash = build_content_hash(
        title="hello world", content="visit for details"
    )

    assert first_hash == second_hash


def test_different_content_has_different_hash() -> None:
    first_hash = build_content_hash(title="Hello", content="A")
    second_hash = build_content_hash(title="Hello", content="B")

    assert first_hash != second_hash
