# LLM Provider Configuration

Switch LLM providers via `.env` without code changes. All providers use the OpenAI-compatible API format.

## Quick switch

```env
# Set the active provider
LLM_PROVIDER=kimi    # or: deepseek | minimax
```

Then run as usual:

```bash
python resume.py build --company Acme --jd jds/target.txt --llm
python resume.py llm-providers   # show all providers + which keys are set
```

Override per command:

```bash
python resume.py build --company Acme --jd jds/target.txt --llm --llm-provider minimax
```

---

## Providers

### DeepSeek (default)

| Variable | Default |
|---|---|
| `DEEPSEEK_API_KEY` | — |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` |

Recommended for resume/JD work: `deepseek-v4-flash`. Alternatives: `deepseek-v4-pro` (heavier reasoning), `deepseek-reasoner` (deep thinking), `deepseek-chat` (general).

Platform: https://platform.deepseek.com

---

### Kimi (Moonshot AI) — China inland

| Variable | Default |
|---|---|
| `KIMI_API_KEY` | — |
| `KIMI_BASE_URL` | `https://api.moonshot.cn/v1` |
| `KIMI_MODEL` | `kimi-k2.5` |

Popular models:

| Model | Notes |
|---|---|
| `kimi-k2.5` | Latest K2.5 (recommended) |
| `kimi-k2-0905-preview` | K2 preview |
| `moonshot-v1-32k` | 32K context |
| `moonshot-v1-128k` | 128K context |
| `moonshot-v1-8k` | Short tasks, lowest cost |

Platform: https://platform.moonshot.cn (China)  
International base URL: `https://api.moonshot.ai/v1` — keys are **not** interchangeable between regions.

---

### MiniMax — China inland

| Variable | Default |
|---|---|
| `MINIMAX_API_KEY` | — |
| `MINIMAX_BASE_URL` | `https://api.minimaxi.com/v1` |
| `MINIMAX_MODEL` | `MiniMax-M2.5` |

Popular models:

| Model | Notes |
|---|---|
| `MiniMax-M2.5` | Best balance of quality + cost |
| `MiniMax-M2.5-highspeed` | Same quality, faster |
| `MiniMax-M2.7` | Newer M series |
| `MiniMax-M2.7-highspeed` | M2.7 fast variant |
| `MiniMax-M3` | Latest flagship, 1M context |

Platform: https://platform.minimaxi.com (China)  
International base URL: `https://api.minimax.io/v1`

---

## Example `.env`

Copy from [`.env.example`](../.env.example):

```env
LLM_PROVIDER=deepseek

DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

KIMI_API_KEY=sk-...
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5

MINIMAX_API_KEY=sk-api-...
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL=MiniMax-M2.5
```

---

## Implementation

Provider resolution lives in [`src/llm_config.py`](../src/llm_config.py):

- `resolve_llm_config(provider)` — returns API key, base URL, model
- `get_llm_client(provider)` — returns `(OpenAI client, model, config)`
- `list_providers()` — metadata for CLI / docs

Used by `resume.py` (`--llm`, `--tailor`, `--boost`, `cover-letter`).

---

## Related

- Quality pipeline: [`resume-quality-pipeline.md`](resume-quality-pipeline.md)
