"""Browser checks for the static dashboard shell; uses no external data."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import unittest

from playwright.sync_api import expect, sync_playwright


APP_DIR = Path(__file__).with_name("app")


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


class DashboardShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        handler = partial(QuietStaticHandler, directory=str(APP_DIR))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/"
        cls.server_thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2)

    def setUp(self) -> None:
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        self.external_requests: list[str] = []
        self.page.on(
            "request",
            lambda request: self.external_requests.append(request.url)
            if not request.url.startswith(self.base_url)
            else None,
        )

    def tearDown(self) -> None:
        self.page.close()

    def test_home_is_sector_first_and_has_no_market_data(self) -> None:
        self.page.goto(self.base_url)
        self.assertEqual(self.page.title(), "Prediction Markets, Explained")
        self.assertTrue(self.page.get_by_role("heading", name="Understand what prediction markets are pricing").is_visible())
        self.assertTrue(self.page.get_by_text("Prototype · no market data loaded.").is_visible())
        self.assertTrue(self.page.get_by_role("link", name="Open Weather sector").is_visible())
        self.assertTrue(self.page.get_by_role("link", name="Browse cross-cutting studies").is_visible())
        self.assertFalse(self.page.get_by_role("link", name="Open study").count())
        self.assertEqual(self.external_requests, [])

    def test_weather_catalog_path_and_contextual_return_links(self) -> None:
        self.page.goto(self.base_url)
        self.page.get_by_role("link", name="Sectors", exact=True).click()
        self.page.wait_for_url("**#/sectors")
        expect(self.page.get_by_role("heading", name="Explore sectors")).to_be_visible()
        self.page.get_by_role("link", name="Open Weather sector").click()
        self.page.wait_for_url("**#/sectors/weather")
        expect(self.page.get_by_role("heading", name="Weather markets")).to_be_visible()
        self.assertEqual(self.page.url.split("#")[-1], "/sectors/weather")
        self.assertTrue(self.page.get_by_role("heading", name="What weather contracts resolve on").is_visible())
        self.page.get_by_role("link", name="Open the study").click()
        self.page.wait_for_url("**#/studies/weather")
        expect(self.page.get_by_role("heading", name="Daily temperature pilot")).to_be_visible()
        self.page.get_by_role("link", name="Weather markets").click()
        self.page.wait_for_url("**#/sectors/weather")
        expect(self.page.get_by_role("heading", name="Weather markets")).to_be_visible()
        self.page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Home", exact=True).click()
        self.page.wait_for_url("**#/")
        expect(self.page.get_by_role("heading", name="Understand what prediction markets are pricing")).to_be_visible()
        self.assertEqual(self.external_requests, [])

    def test_cross_cutting_study_paths_and_contextual_return_links(self) -> None:
        self.page.goto(self.base_url)
        self.page.get_by_role("link", name="Browse cross-cutting studies").click()
        self.page.wait_for_url("**#/collections/research")
        expect(self.page.get_by_role("heading", name="Studies across sectors")).to_be_visible()
        self.assertTrue(self.page.get_by_text("This collection is not a market sector.").is_visible())
        expected = {
            "cross-venue": "Polymarket–Kalshi comparison",
            "options": "Prediction-market options feasibility",
        }
        for route, heading in expected.items():
            with self.subTest(route=route):
                self.page.goto(self.base_url + f"#/collections/research")
                self.page.locator(f'a[href="#/studies/{route}"]').click()
                self.page.wait_for_url(f"**#/studies/{route}")
                expect(self.page.get_by_role("heading", name=heading)).to_be_visible()
                self.page.locator("#main").get_by_role("link", name="Cross-cutting studies").click()
                self.page.wait_for_url("**#/collections/research")
                expect(self.page.get_by_role("heading", name="Studies across sectors")).to_be_visible()
        self.assertEqual(self.external_requests, [])

    def test_study_pages_render_reader_context(self) -> None:
        self.page.goto(self.base_url + "#/sectors/weather")
        self.assertTrue(self.page.get_by_role("heading", name="Weather markets").is_visible())
        self.page.get_by_role("link", name="Open the study").click()
        self.page.wait_for_url("**#/studies/weather")
        expect(self.page.get_by_role("heading", name="Daily temperature pilot")).to_be_visible()
        expect(self.page.get_by_role("heading", name="Contract scope and settlement")).to_be_visible()
        expect(self.page.get_by_role("heading", name="Limitations")).to_be_visible()
        expect(self.page.get_by_role("heading", name="Sources and reproducibility")).to_be_visible()
        self.assertEqual(self.external_requests, [])

    def test_shared_study_sections_have_same_order_and_safe_empty_states(self) -> None:
        expected_sections = [
            "summary",
            "contract-scope",
            "market-pricing",
            "data-coverage",
            "method",
            "domain",
            "findings",
            "uncertainty",
            "limitations",
            "freshness",
            "provenance",
        ]
        for route in ("weather", "cross-venue", "options"):
            with self.subTest(route=route):
                self.page.goto(self.base_url + f"#/studies/{route}")
                sections = self.page.locator("[data-study-section]").evaluate_all(
                    "nodes => nodes.map(node => node.dataset.studySection)"
                )
                self.assertEqual(sections, expected_sections)
                self.assertIn("Evidence: not evaluated", self.page.locator("main").inner_text())
                self.assertIn("No quote is available", self.page.locator('[data-study-section="market-pricing"]').inner_text())
                coverage = self.page.locator('[data-study-section="data-coverage"]').inner_text()
                self.assertIn("Sample count\nNot reported", coverage)
                self.assertNotRegex(coverage, r"Sample count\s+0(?:\D|$)")
                self.assertIn("No metrics are supplied", self.page.locator('[data-study-section="findings"]').inner_text())
                self.assertIn("Source use remains unavailable", self.page.locator('[data-study-section="provenance"]').inner_text())
        self.assertEqual(self.external_requests, [])

    def test_visualization_component_shows_missing_quality_without_zero(self) -> None:
        self.page.goto(self.base_url + "#/studies/cross-venue")
        component = self.page.locator(".visualization-component").first
        self.assertTrue(component.get_by_role("heading", name="Matched quote chart unavailable").is_visible())
        self.assertIn("Chart unavailable until approved study data is supplied.", component.inner_text())
        self.assertIn("No datapoints supplied", component.inner_text())
        self.assertIn("not zero", component.inner_text())
        self.assertIn("Quote freshness\nNot assessed; no quote is loaded", component.inner_text())
        self.assertIn("Data-quality flags\nNot assessed", component.inner_text())
        self.assertIn("Source attribution\nNot supplied", component.inner_text())
        self.assertNotRegex(component.inner_text(), r"(?:Sample count|Datapoints)\s+0(?:\D|$)")
        self.assertEqual(self.external_requests, [])

    def test_visualization_component_supports_synthetic_chart_and_accessible_table(self) -> None:
        self.page.goto(self.base_url + "#/studies/weather")
        result = self.page.evaluate("""() => {
          const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
          svg.setAttribute("role", "img");
          svg.setAttribute("aria-label", "Synthetic fixture chart for component test only");
          const mark = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          mark.setAttribute("cx", "20"); mark.setAttribute("cy", "20"); mark.setAttribute("r", "4");
          svg.append(mark);
          const panel = window.DashboardComponents.renderVisualization({
            title: "Synthetic fixture chart — test only",
            description: "Synthetic fixture, not market data.",
            chartNode: svg,
            chartDescription: "Synthetic fixture chart for component test only",
            caption: "Synthetic fixture only; no real market values.",
            tableCaption: "Synthetic fixture data table — test only",
            columns: [{key: "period", label: "Period"}, {key: "value", label: "Value"}],
            rows: [
              {period: "Synthetic point", value: "0.5 (synthetic)"},
              {period: "Synthetic partial point", value: null},
            ],
            attribution: "Synthetic test source",
            updatedAt: "Synthetic test timestamp",
            quoteFreshness: "Synthetic test state",
            coverageGaps: ["Synthetic test gap"],
            uncertainty: "Synthetic test interval",
            flags: [
              {code: "wide_spread", label: "Wide quote", detail: "synthetic test flag"},
              {code: "stale_quote", label: "Stale quote", detail: "synthetic test flag"},
            ],
          });
          document.querySelector("main").append(panel);
          return {
            imageLabel: panel.querySelector("svg").getAttribute("aria-label"),
            caption: panel.querySelector("figcaption").textContent,
            tableCaption: panel.querySelector("table caption").textContent,
            headers: [...panel.querySelectorAll("thead th")].map(cell => [cell.textContent, cell.scope]),
            rowHeaders: [...panel.querySelectorAll("tbody th")].map(cell => [cell.textContent, cell.scope]),
            cells: [...panel.querySelectorAll("tbody td")].map(cell => cell.textContent),
            flag: panel.querySelector("[data-flag-code='wide_spread']").textContent,
            staleFlag: panel.querySelector("[data-flag-code='stale_quote']").textContent,
            quality: panel.querySelector(".quality-grid").innerText,
          };
        }""")
        self.assertEqual(result["imageLabel"], "Synthetic fixture chart for component test only")
        self.assertIn("Synthetic fixture only", result["caption"])
        self.assertIn("Synthetic fixture data table", result["tableCaption"])
        self.assertEqual(result["headers"], [["Period", "col"], ["Value", "col"]])
        self.assertEqual(result["rowHeaders"], [["Synthetic point", "row"], ["Synthetic partial point", "row"]])
        self.assertEqual(result["cells"], ["0.5 (synthetic)", "Not reported"])
        self.assertIn("Wide quote: synthetic test flag", result["flag"])
        self.assertIn("Stale quote: synthetic test flag", result["staleFlag"])
        self.assertIn("Synthetic test source", result["quality"])
        self.assertEqual(self.external_requests, [])

    def test_unknown_sectors_studies_and_routes_have_catalog_path(self) -> None:
        for route, heading in (
            ("#/sectors/politics", "Sector not available"),
            ("#/studies/not-yet-supported", "Study not found"),
            ("#/not-a-route", "Page not found"),
        ):
            with self.subTest(route=route):
                self.page.goto(self.base_url + route)
                self.assertTrue(self.page.get_by_role("heading", name=heading).is_visible())
                self.page.get_by_role("link", name="Return to the catalog").click()
                self.page.wait_for_url("**#/")
                expect(self.page.get_by_role("heading", name="Understand what prediction markets are pricing")).to_be_visible()

    def test_all_three_study_routes_are_explicitly_unavailable(self) -> None:
        expected = {
            "weather": "Daily temperature pilot",
            "cross-venue": "Polymarket–Kalshi comparison",
            "options": "Prediction-market options feasibility",
        }
        for route, heading in expected.items():
            with self.subTest(route=route):
                self.page.goto(self.base_url + f"#/studies/{route}")
                self.assertTrue(self.page.get_by_role("heading", name=heading).is_visible())
                self.assertTrue(self.page.get_by_role("heading", name="Study data unavailable").is_visible())
                self.assertIn("Evidence: not evaluated", self.page.locator("main").inner_text())
        self.assertEqual(self.external_requests, [])

    def test_mobile_and_desktop_have_no_horizontal_overflow(self) -> None:
        for width in (1280, 390, 320):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 844})
                self.page.goto(self.base_url + "#/studies/cross-venue")
                dimensions = self.page.evaluate(
                    "({body: document.body.scrollWidth, root: document.documentElement.clientWidth})"
                )
                self.assertLessEqual(dimensions["body"], dimensions["root"])
                self.assertTrue(self.page.get_by_role("navigation", name="Main navigation").is_visible())


if __name__ == "__main__":
    unittest.main()
