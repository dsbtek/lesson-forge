# Model Integration Guide

Use this guide to connect any backend, frontend, CLI, or mobile application to the local `llama.cpp` multi-model & agent API.

## Connection Details

| Setting | Value |
| --- | --- |
| **Base URL (same machine)** | `http://localhost:8080/v1` |
| **Base URL (LAN / other device)** | `http://<HOST_IP>:8080/v1` |
| **Base URL (another Docker container)** | `http://host.docker.internal:8080/v1` (or `http://llama-api-router:8080/v1` on the `ai-models_default` network) |
| **API Key** | Not required (pass any non-empty placeholder like `"not-needed"` if an SDK requires one) |
| **CORS** | Enabled (`*`) for browser/frontend apps |

---

## Available Models & Virtual Agents

Pass any ID below in the `"model"` field of your request.

### Base Models
| ID | Type | Best For |
| --- | --- | --- |
| `llama-3.2-1b` *(default)* | Chat / Completion | Fast general text, lightweight tasks |
| `qwen2.5-1.5b` | Chat / Completion | Coding, reasoning, structured output |
| `all-minilm-l6-v2` | Embeddings | Semantic search, RAG, similarity |

### Virtual Agents (Zero Extra RAM)
Virtual agents route to `llama-3.2-1b` or `qwen2.5-1.5b` with a preconfigured `system_prompt` and default `temperature`. You can still override `temperature`, `max_tokens`, etc. per request.

| Agent ID | Backend | Purpose |
| --- | --- | --- |
| `coder` | `qwen2.5-1.5b` | Clean, working code with brief explanations |
| `code-reviewer` | `qwen2.5-1.5b` | Bugs, security issues, edge cases, improvements |
| `sql-assistant` | `qwen2.5-1.5b` | SQL queries and brief assumptions |
| `json-extractor` | `qwen2.5-1.5b` | Valid JSON extraction without markdown fences |
| `summarizer` | `llama-3.2-1b` | Concise bullet-point summaries |
| `translator` | `llama-3.2-1b` | Language translation |
| `classifier` | `llama-3.2-1b` | Categorization / sentiment with one-line reason |
| `general-assistant` | `llama-3.2-1b` | General Q&A |

---

## Endpoints

- `GET /health` — Router and backend container health + list of registered agents
- `GET /v1/models` — OpenAI-compatible list of all base models and virtual agents
- `POST /v1/chat/completions` — Chat completions (supports `"stream": true` SSE)
- `POST /v1/completions` — Raw text completions
- `POST /v1/embeddings` — Vector embeddings (use `"model": "all-minilm-l6-v2"`)

---

## Integration Examples

### 1. Recommended App Environment Variables
```env
AI_BASE_URL=http://localhost:8080/v1
AI_API_KEY=not-needed
AI_MODEL=coder
AI_EMBED_MODEL=all-minilm-l6-v2
```

### 2. Python (`openai` SDK)
```bash
pip install openai
```

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("AI_BASE_URL", "http://localhost:8080/v1"),
    api_key=os.getenv("AI_API_KEY", "not-needed"),
)

# Chat with a virtual agent
chat = client.chat.completions.create(
    model="coder",
    messages=[{"role": "user", "content": "Write a Python function to validate an email."}],
    max_tokens=200,
)
print(chat.choices[0].message.content)

# Streaming chat
stream = client.chat.completions.create(
    model="summarizer",
    messages=[{"role": "user", "content": "Summarize why Docker helps deployments."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print()

# Embeddings
emb = client.embeddings.create(
    model="all-minilm-l6-v2",
    input="Searchable document text",
)
vector = emb.data[0].embedding
print("Embedding dimensions:", len(vector))
```

### 3. JavaScript / TypeScript (`fetch`)
Works in Node.js 18+, browser apps, Next.js, Vite, etc.

```typescript
const BASE_URL = "http://localhost:8080/v1";

// Non-streaming chat
async function askAgent(model: string, prompt: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      messages: [{ role: "user", content: prompt }],
      max_tokens: 256,
    }),
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }

  const data = await res.json();
  return data.choices[0].message.content;
}

// Embeddings
async function getEmbedding(text: string): Promise<number[]> {
  const res = await fetch(`${BASE_URL}/embeddings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "all-minilm-l6-v2",
      input: text,
    }),
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }

  const data = await res.json();
  return data.data[0].embedding;
}
```

### 4. JavaScript / TypeScript (`openai` npm SDK)
```bash
npm install openai
```

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:8080/v1",
  apiKey: "not-needed",
});

const response = await client.chat.completions.create({
  model: "json-extractor",
  messages: [
    { role: "user", content: "Extract name and role: Alice is a Backend Engineer." },
  ],
});

console.log(response.choices[0].message.content);
```

### 5. `curl` Quick Tests
```bash
# Health check
curl -s http://localhost:8080/health

# Chat with an agent
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "classifier",
    "messages": [{"role": "user", "content": "I love how fast this API is!"}],
    "max_tokens": 32
  }'

# Embeddings
curl -s http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "all-minilm-l6-v2",
    "input": "Hello world"
  }'
```

---

## Connecting From Another Docker Compose Project

If your application runs in its own `docker-compose.yml`, attach it to the `ai-models_default` network and call `http://llama-api-router:8080/v1`:

```yaml
services:
  my-app:
    image: my-app:latest
    environment:
      - AI_BASE_URL=http://llama-api-router:8080/v1
    networks:
      - ai-models_default

networks:
  ai-models_default:
    external: true
```

---

## Error Codes & Tips

- **`404 Not Found`**: Unknown `"model"` ID. Check `GET /v1/models` for valid model and agent names.
- **`502 Bad Gateway`**: A backend `llama-server` container is starting up or stopped. Check `GET /health` or `docker compose ps`.
- **CPU Inference Latency**: On CPU-only hardware, keep `max_tokens` bounded (e.g., `128`–`512`) and use `"stream": true` for interactive UIs so tokens appear immediately.

