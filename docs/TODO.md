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

## Optional follow-ups

- [ ] Add `variants[]` content to high-value bullets in `base.yaml`
- [ ] Interview prep command (from ats-resume-tailor pattern)
- [ ] Browser extension to send JD from job sites to WebUI
- [ ] `base_zh.yaml` Chinese variant content

## Notes

- RxResume credentials: store in `.env` as `RXRESU_API_KEY` — never commit
- Agent instructions: [`../AGENTS.md`](../AGENTS.md)
