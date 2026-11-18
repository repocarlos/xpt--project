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
        expect(self.page.get_by_role("heading", name="What does the contract resolve on?")).to_be_visible()
        expect(self.page.get_by_role("heading", name="Limitations and uncertainty")).to_be_visible()
        expect(self.page.get_by_role("heading", name="Sources and reproducibility")).to_be_visible()
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
