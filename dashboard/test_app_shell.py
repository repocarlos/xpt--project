"""Browser checks for the static dashboard shell; uses no external data."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import unittest

from playwright.sync_api import sync_playwright


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

    def test_home_has_prototype_notice_and_no_market_data(self) -> None:
        self.page.goto(self.base_url)
        self.assertEqual(self.page.title(), "Prediction Markets, Explained")
        self.assertTrue(self.page.get_by_role("heading", name="Understand what prediction markets are pricing").is_visible())
        self.assertTrue(self.page.get_by_text("Prototype · no market data loaded.").is_visible())
        self.assertTrue(self.page.get_by_role("link", name="Open study").first.is_visible())
        self.assertEqual(self.external_requests, [])

    def test_sector_and_study_routes_render_reader_context(self) -> None:
        self.page.goto(self.base_url + "#/sectors/weather")
        self.assertTrue(self.page.get_by_role("heading", name="Weather markets").is_visible())
        self.assertTrue(self.page.get_by_role("heading", name="What weather contracts resolve on").is_visible())
        self.page.get_by_role("link", name="Open the study").click()
        self.assertTrue(self.page.get_by_role("heading", name="Daily temperature pilot").is_visible())
        self.assertTrue(self.page.get_by_role("heading", name="What does the contract resolve on?").is_visible())
        self.assertTrue(self.page.get_by_role("heading", name="Limitations and uncertainty").is_visible())
        self.assertTrue(self.page.get_by_role("heading", name="Sources and reproducibility").is_visible())
        self.assertEqual(self.external_requests, [])

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
