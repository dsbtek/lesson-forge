"""The bundled seed corpus parses and carries the metadata retrieval relies on
(app/rag/seed/standards.jsonl).

The seed is ingested by default (`make ingest`), so it must always be well-formed:
non-empty content plus the `meta` keys used for citations, filtering, and authority
ranking (README §10).
"""

from __future__ import annotations

from app.rag import loaders
from app.rag.ingest import SEED_DIR

REQUIRED_META_KEYS = {
    "code",
    "framework",
    "grade",
    "subject",
    "jurisdiction",
    "authority_level",
    "document_version",
    "section",
}


def _seed_docs():
    seed_files = sorted(SEED_DIR.glob("*.jsonl"))
    assert seed_files, f"no seed corpus found under {SEED_DIR}"
    return list(loaders.load_documents(seed_files))


def test_seed_corpus_loads():
    docs = _seed_docs()
    assert len(docs) >= 12  # NGSS + CCSS starter set


def test_every_record_has_content_and_required_meta():
    for doc in _seed_docs():
        assert doc.text.strip(), "seed record has empty content"
        missing = REQUIRED_META_KEYS - doc.meta.keys()
        assert not missing, f"{doc.meta.get('code')} missing meta keys: {missing}"


def test_seed_is_marked_official():
    # Authority filtering boosts official sources; the seed must qualify.
    assert all(d.meta["authority_level"] == "official" for d in _seed_docs())


def test_standard_codes_are_unique():
    codes = [d.meta["code"] for d in _seed_docs()]
    assert len(codes) == len(set(codes))
