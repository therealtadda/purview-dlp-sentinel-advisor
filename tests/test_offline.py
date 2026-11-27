"""Offline repository contracts; these checks do not parse or execute KQL."""

import csv
import io
import json
import re
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENTINEL = ROOT / "ops" / "sentinel"


def read(path):
    return path.read_text(encoding="utf-8")


def seed_rows(text):
    body = text.split("[", 1)[1].rsplit("]", 1)[0]
    matches = re.findall(
        r'datetime\((\d{4}-\d{2}-\d{2})\),\s*"([^"]+)",\s*"([^"]+)",'
        r'\s*"([^"]*)",\s*"([^"]*)"', body
    )
    return [tuple(row) for row in matches]


class EvidenceContractTests(unittest.TestCase):
    def test_seed_matches_disconnected_prompt(self):
        seed = seed_rows(read(SENTINEL / "lab-seed.kql"))
        prompt = read(ROOT / "docs" / "analysis-prompts.md")
        csv_lines = re.findall(r"^2026-01-\d\d,.*$", prompt, re.MULTILINE)
        self.assertEqual(seed, [tuple(row) for row in csv.reader(io.StringIO("\n".join(csv_lines)))])
        self.assertEqual(len(seed), 5)
        self.assertEqual(len({row[:2] for row in seed}), len(seed))

    def test_seed_contains_only_valid_contract_values(self):
        allowed_sources = {"CloudAppEvents", "MicrosoftPurviewInformationProtection", "SecurityAlert"}
        bands = {"zero", "suppressed", "10-19", "20-49", "50-99", "100+"}
        for week, source, coverage, volume, correlation in seed_rows(read(SENTINEL / "lab-seed.kql")):
            with self.subTest(week=week, source=source):
                self.assertIn(source, allowed_sources)
                self.assertIn(coverage, {"complete", "partial"})
                if coverage == "partial":
                    self.assertEqual((volume, correlation), ("", ""))
                else:
                    self.assertIn(volume, bands)
                    permitted = {"observed", "withheld", "unverified"} if source == "SecurityAlert" else {"not_applicable"}
                    self.assertIn(correlation, permitted)

    def test_jobs_default_to_no_publication(self):
        for path in sorted(SENTINEL.glob("job-*.kql")):
            with self.subTest(job=path.name):
                query = read(path)
                self.assertIn("let approved_for_release = false;", query)
                self.assertIn("let ready = false;", query)
                self.assertTrue(query.rstrip().endswith("| where can_publish_week(week, now(), approved_for_release)"))
                self.assertNotIn("DataSecurityEvents", query)
        self.assertIn("let link_ready = false;", read(SENTINEL / "job-alerts.kql"))
        self.assertIn('ProviderName:string)[];', read(SENTINEL / "job-alerts.kql"))

    def test_reader_projects_exact_contract(self):
        reader = read(SENTINEL / "read-weekly.kql")
        self.assertRegex(reader, r"(?m)^\| project WeekStart, Source, Coverage, Volume, Correlation$")
        self.assertIn("WeekStart >= first_week and WeekStart < end_week_exclusive", reader)
        for raw in ("CloudAppEvents", "SecurityAlert", "DataSecurityEvents", "RawEventData"):
            self.assertNotIn(raw, reader)

    def test_weekly_release_guards_and_disclosure_conditions(self):
        query = " ".join(read(SENTINEL / "weekly-functions.kql").split())
        for fragment in (
            "approved_for_release and dayofweek(week) == 1d and startofday(week) == week",
            "clock >= week + 9d",
            'ready and toscalar(rows | where isempty(EventId) | count) == 0',
            '| distinct EventId',
            'Coverage=iff(valid, "complete", "partial")',
            'Volume=iff(valid, volume_band(Records), "")',
            'Correlation=iff(valid, "not_applicable", "")',
            'on VendorName, ProductName, ProviderName',
            'EventTime > StartTime and EventTime < EndTime',
            'linked >= 10 and total - linked >= 10, "observed", "withheld"',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, query)

    def test_synthetic_assertions_are_named_and_documented(self):
        fixtures = read(SENTINEL / "weekly-fixtures.kql")
        tests = re.findall(r'Test="([^"]+)"', fixtures)
        self.assertEqual(len(tests), 16)
        self.assertEqual(len(set(tests)), 16)
        for name in (
            "missing event identifier fails closed",
            "missing alert identifier fails closed",
            "invalid alert window leaves linkage unverified",
            "empty allowlist fails closed",
            "conflicting latest duplicates invalidate linkage only",
        ):
            self.assertIn(name, tests)
        self.assertIn("16 result rows", read(ROOT / "docs" / "sentinel.md"))

    def test_investigation_defaults_and_scope_are_bounded(self):
        query = read(SENTINEL / "investigate-alert.kql")
        for name in ("alert_id", "approved_vendor", "approved_product", "approved_provider"):
            self.assertIn(f'let {name} = "";', query)
            self.assertIn(f"isnotempty({name})", query)
        for fragment in (
            "until_utc - from_utc <= 1d",
            "TimeGenerated >= from_utc and TimeGenerated < until_utc",
            "SystemAlertId == alert_id",
            "VendorName == approved_vendor",
            "ProductName == approved_product",
            "ProviderName == approved_provider",
            "| take 25",
        ):
            self.assertIn(fragment, query)
        self.assertNotIn("DataSecurityEvents", query)

    def test_synthetic_investigation_cases(self):
        fixture = read(SENTINEL / "investigate-alert-fixture.kql")
        rows = re.findall(
            r'datetime\(([^)]+)\), datetime\([^)]+\), datetime\([^)]+\), '
            r'"([^"]+)", "([^"]+)", "([^"]+)", "([^"]+)", "([^"]+)"',
            fixture,
        )
        self.assertEqual(len(rows), 4)
        start = datetime.fromisoformat("2026-01-05T00:00:00Z")
        end = datetime.fromisoformat("2026-01-06T00:00:00Z")
        expected = ("fixture-case-alert", "fixture-vendor", "fixture-product", "fixture-provider")
        matched = [
            alert_type
            for time, alert_type, alert_id, vendor, product, provider in rows
            if start <= datetime.fromisoformat(time) < end
            and (alert_id, vendor, product, provider) == expected
        ]
        self.assertEqual(matched, ["fixture-alert"])


class DocumentationTests(unittest.TestCase):
    def test_readme_examples_are_lab_only_and_parse(self):
        text = read(ROOT / "README.md")
        examples = re.findall(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        self.assertEqual(len(examples), 2)
        cli, vscode = [json.loads(example) for example in examples]
        server = cli["mcpServers"]["sentinel-lab"]
        self.assertEqual(set(server), {"type", "url", "tools"})
        self.assertEqual(server["type"], "http")
        self.assertEqual(server["tools"], ["query_lake"])
        self.assertEqual(server["url"], "https://sentinel.microsoft.com/mcp/data-exploration")
        self.assertEqual(vscode["servers"]["sentinel-lab"]["url"], server["url"])
        self.assertFalse((ROOT / ".mcp.json").exists())
        self.assertFalse((ROOT / ".github" / "mcp.json").exists())

    def test_all_queries_are_catalogued(self):
        readme = read(ROOT / "README.md")
        for path in SENTINEL.glob("*.kql"):
            with self.subTest(path=path.name):
                self.assertIn(f"(ops/sentinel/{path.name})", readme)

    def test_relative_markdown_links_exist(self):
        for path in [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]:
            text = read(path)
            for target in re.findall(r"\]\(([^ )]+)\)", text):
                location, _, anchor = target.partition("#")
                if "://" in location or location.startswith("mailto:"):
                    continue
                destination = path.parent / location if location else path
                with self.subTest(file=path.name, target=target):
                    self.assertTrue(destination.exists())
                    if anchor and destination.is_file() and destination.suffix == ".md":
                        headings = re.findall(r"^#+\s+(.+)$", read(destination), re.MULTILINE)
                        slugs = {
                            re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
                            for heading in headings
                        }
                        self.assertIn(anchor, slugs)


if __name__ == "__main__":
    unittest.main()
