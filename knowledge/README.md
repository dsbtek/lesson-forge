# knowledge/

Source curriculum documents and standards corpora (NGSS, Common Core, state
frameworks, etc.) that seed the hybrid-RAG `knowledge_chunks` table. At generation
time the Curriculum Researcher retrieves from this corpus so lessons cite real
standards instead of stubs (README §10).

Drop documents here, then run `make ingest`. The directory is mounted read-only
into the `api`/`worker` containers at `/knowledge`.

## Supported formats

Ingestion dispatches by file extension (see `app/rag/loaders.py`):

| Extension | Loader |
| --- | --- |
| `.txt`, `.md` | stdlib (plain text) |
| `.pdf` | `pypdf` (lazy import) |
| `.html`, `.htm` | `beautifulsoup4` (lazy import) |
| `.jsonl` | pre-structured records (see below) |

Directories are walked recursively; unsupported files are ignored.

### Pre-structured records (`.jsonl`)

One JSON object per line. `content` is required; `source` and `meta` are optional
but recommended — `meta` drives filtering, citations, and authority ranking:

```json
{"content": "Standard text…", "source": "NGSS", "meta": {"code": "5-ESS2-1", "framework": "NGSS", "grade": "5", "subject": "science", "jurisdiction": "US", "authority_level": "official", "document_version": "2013", "section": "Earth's Systems"}}
```

The bundled seed corpus (`app/rag/seed/standards.jsonl`, ~14 NGSS + CCSS records)
is ingested by default so retrieval works out of the box.

## Pipeline

`load → chunk → embed → upsert`, all offline-first and gated by `RAG_ENABLED`:

1. **Load** documents from the seed corpus and any `--paths` (this directory).
2. **Chunk** into overlapping, paragraph-aware windows (`app/rag/chunking.py`).
3. **Embed** each chunk with Ollama `nomic-embed-text` (768-dim) — skipped when
   embeddings are disabled, leaving chunks searchable via full-text (FTS) only.
4. **Upsert** into `knowledge_chunks`. Ingestion is **idempotent**: a sha256 of
   `source + content` is stored in `meta.hash`; re-ingesting skips unchanged chunks.

Retrieval fuses dense (pgvector cosine), sparse (Postgres FTS), and explicit
standard-code matches via Reciprocal Rank Fusion, boosts `authority_level:
official` sources, and filters by grade/subject/framework (`app/rag/retrieval.py`).

## Enabling RAG (live stack)

```bash
ollama pull nomic-embed-text          # host Ollama; provides embeddings
# .env: RAG_ENABLED=true, EMBEDDING_MODEL=nomic-embed-text, EMBEDDING_DIM=768
make migrate                          # applies 0002: sets vector dim + HNSW index
make ingest                           # seed corpus + ./knowledge → chunked, embedded, indexed
```

Verify: `make psql` then `SELECT count(*), count(embedding) FROM knowledge_chunks;`
(both should be > 0). Generate a lesson — the SSE stream shows `retrieval.started` /
`retrieval.completed`, and the persisted lesson's `research.citations` are populated.

With `RAG_ENABLED=false` (the default), none of the above is required: no DB or
embedding calls happen and the researcher falls back to deterministic output.
