# TODO — Status

## Completed

- [x] LLM JD composition (`--llm`, `--tailor`, `--boost`)
- [x] WebUI (Resume, Transform, Compare, History tabs)
- [x] JD copy & paste + PDF upload
- [x] Template picker with visual previews
- [x] Tag system + `python resume.py tags`
- [x] `requirements.txt`
- [x] Structured JD analysis (`analyze`, `score`, `compare`)
- [x] Bullet ranking + caps (`compose.py`, `--max-bullets`, `--max-jobs`)
- [x] ATS scoring + `ats-report.json` on every build with `--jd`
- [x] Multi-JD compare (CLI + WebUI Compare tab)
- [x] Documentation: [`resume-quality-pipeline.md`](resume-quality-pipeline.md)
- [x] Tailor validation + rich `bullet-diff.json`
- [x] Page budget (`--pages`) + history ATS audit trail
- [x] LLM hybrid bullet scoring + structured JD parse (`llm_pipeline.py`)
- [x] Senior job filter + `--target-score` rebuild helper
- [x] `score --variant`, `interview` CLI, `provenance.json` per build
- [x] RxResume `--template auto` (kakuna/bronzor/chikorita)
- [x] `base.yaml` variants, metrics, keywords + content refactor

## Optional follow-ups

- [ ] Browser extension to send JD from job sites to WebUI
- [ ] `base_zh.yaml` Chinese variant content

## Notes

- RxResume credentials: store in `.env` as `RXRESU_API_KEY` — never commit
- Agent instructions: [`../AGENTS.md`](../AGENTS.md)
