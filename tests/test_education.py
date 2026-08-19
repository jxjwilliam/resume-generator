import unittest

from src.compose import format_education_institution
from src.cli import build_variant


class FormatEducationInstitutionTests(unittest.TestCase):
    def test_appends_country(self):
        self.assertEqual(
            format_education_institution({
                "institution": "Xi'an Jiaotong University",
                "location": "China",
            }),
            "Xi'an Jiaotong University, China",
        )
        self.assertEqual(
            format_education_institution({
                "institution": "Universal Learning Institute",
                "location": "Vancouver, Canada",
            }),
            "Universal Learning Institute, Vancouver, Canada",
        )

    def test_does_not_duplicate_location_already_in_name(self):
        self.assertEqual(
            format_education_institution({
                "institution": "Xi'an Jiaotong University, China",
                "location": "China",
            }),
            "Xi'an Jiaotong University, China",
        )


class BuildVariantEducationTests(unittest.TestCase):
    def test_education_institution_includes_location(self):
        base = {
            "identity": {
                "name": "William Jiang",
                "email": "a@b.c",
                "phone": "(236) 992-3846",
                "location": "Vancouver",
                "headline": "Engineer",
                "urls": [],
            },
            "summary": "Summary.",
            "experience": [],
            "skills": {},
            "projects": [],
            "education": [
                {
                    "institution": "Xi'an Jiaotong University",
                    "degree": "Bachelor of Engineering",
                    "graduation": "1995-07",
                    "location": "China",
                    "status": "active",
                },
                {
                    "institution": "Universal Learning Institute",
                    "degree": "Diploma of Business Management",
                    "graduation": "2006-03",
                    "location": "Vancouver, Canada",
                    "status": "active",
                },
            ],
        }
        variant, _, _ = build_variant(
            base, tags=None, template="sb2nov",
            company="TestCo", role="Engineer", pages=0,
        )
        inst = [e["institution"] for e in variant["cv"]["sections"]["EDUCATION"]]
        self.assertEqual(inst, [
            "Xi'an Jiaotong University, China",
            "Universal Learning Institute, Vancouver, Canada",
        ])


if __name__ == "__main__":
    unittest.main()
