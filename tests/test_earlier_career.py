import unittest

from src.compose import format_earlier_career_line, select_earlier_career_jobs
from src.cli import build_variant


def _job(*, company, title, location, start, end, status, bullets=None, period=None,
         earlier_company=None, earlier_title=None):
    job = {
        "company": company,
        "title": title,
        "location": location,
        "start": start,
        "end": end,
        "status": status,
        "tags": ["software-engineering"],
        "bullets": bullets or [
            {
                "text": f"Did work at {company}.",
                "tags": ["software-engineering"],
                "relevance": "high",
                "status": "active",
            }
        ],
    }
    if period:
        job["period"] = period
    if earlier_company:
        job["earlier_company"] = earlier_company
    if earlier_title:
        job["earlier_title"] = earlier_title
    return job


WEBMD = _job(
    company="WebMD",
    title="Senior Frontend Engineer",
    location="New York City, USA",
    start="2014-11",
    end="2017-08",
    status="active",
)
BEST_BUY = _job(
    company="Best Buy Canada",
    title="Senior JavaScript Engineer",
    location="Canada",
    start="2007-03",
    end="2014-07",
    status="earlier",
    period="Mar 2007 – Jul 2014",
    earlier_company="Best Buy Canada (Vancouver)",
)
FEDEX = _job(
    company="FedEx",
    title="Computer Programmer Analyst",
    location="Singapore",
    start="2000-10",
    end="2004-12",
    status="earlier",
    period="Oct 2000 – Dec 2004",
    earlier_company="FedEx Singapore",
)
ZTE = _job(
    company="ZTE (Zhongxing Telecom)",
    title="Software Engineer",
    location="China",
    start="1995-09",
    end="2000-09",
    status="earlier",
    period="Sep 1995 – Sep 2000",
    earlier_company="ZTE China",
    earlier_title="Software Engineer, CDMA Systems",
)


class SelectEarlierCareerTests(unittest.TestCase):
    def test_returns_earlier_jobs_newest_first(self):
        jobs = select_earlier_career_jobs([ZTE, WEBMD, FEDEX, BEST_BUY])
        self.assertEqual(
            [j["company"] for j in jobs],
            ["Best Buy Canada", "FedEx", "ZTE (Zhongxing Telecom)"],
        )

    def test_skips_active_and_deprecated_jobs(self):
        dropped = _job(
            company="Old Co", title="Dev", location="X",
            start="1990-01", end="1991-01", status="deprecated",
        )
        jobs = select_earlier_career_jobs([WEBMD, dropped])
        self.assertEqual(jobs, [])


class FormatEarlierCareerTests(unittest.TestCase):
    def test_screenshot_lines_bold_company_no_extra_location(self):
        self.assertEqual(
            format_earlier_career_line(BEST_BUY),
            "**Best Buy Canada (Vancouver)** — Senior JavaScript Engineer | Mar 2007 – Jul 2014",
        )
        self.assertEqual(
            format_earlier_career_line(FEDEX),
            "**FedEx Singapore** — Computer Programmer Analyst | Oct 2000 – Dec 2004",
        )
        self.assertEqual(
            format_earlier_career_line(ZTE),
            "**ZTE China** — Software Engineer, CDMA Systems | Sep 1995 – Sep 2000",
        )


class BuildVariantEarlierCareerTests(unittest.TestCase):
    def test_section_order_skills_before_experience(self):
        base = {
            "identity": {
                "name": "William Jiang",
                "email": "a@b.c",
                "phone": "(236) 992-3846",
                "location": "Vancouver",
                "headline": "Engineer",
                "urls": [],
            },
            "summary": "Summary text.",
            "experience": [ZTE, FEDEX, BEST_BUY, WEBMD],
            "skills": {
                "languages": [
                    {"name": "Python", "status": "active", "tags": ["python"]},
                ],
            },
            "projects": [],
            "education": [],
        }
        variant, _, _ = build_variant(
            base,
            tags=None,
            template="sb2nov",
            company="TestCo",
            role="Engineer",
            pages=0,
        )
        keys = list(variant["cv"]["sections"].keys())
        self.assertEqual(keys[:4], [
            "SUMMARY", "CORE SKILLS", "EXPERIENCE", "EARLIER CAREER",
        ])
        self.assertEqual(
            [j["company"] for j in variant["cv"]["sections"]["EXPERIENCE"]],
            ["WebMD"],
        )
        self.assertEqual(
            variant["cv"]["sections"]["EARLIER CAREER"],
            [
                "**Best Buy Canada (Vancouver)** — Senior JavaScript Engineer | Mar 2007 – Jul 2014",
                "**FedEx Singapore** — Computer Programmer Analyst | Oct 2000 – Dec 2004",
                "**ZTE China** — Software Engineer, CDMA Systems | Sep 1995 – Sep 2000",
            ],
        )
        self.assertFalse(variant["design"]["page"]["show_top_note"])
        self.assertEqual(
            variant["design"]["colors"]["section_titles"],
            "rgb(31,56,100)",
        )


if __name__ == "__main__":
    unittest.main()
