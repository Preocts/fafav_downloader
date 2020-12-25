""" Simple tests

Author: Preocts <preocts@preocts.com>
"""
import os
import unittest

from shutil import copy
from unittest.mock import patch

from fafavs import main


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        with open("./tests/fixtures/page_out", "r") as f:
            self.page = f.read()
        with open("./tests/fixtures/download_out", "r") as f:
            self.download_page = f.read()
        copy("./tests/fixtures/list_test", "./fakeuser_test")
        return super().setUp()

    def tearDown(self) -> None:
        if os.path.isfile("./fakeuser_test"):
            os.remove("./fakeuser_test")
        return super().tearDown()

    def test_spoof_header(self) -> None:
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = FileNotFoundError()
            with self.assertRaises(Exception):
                main.spoof_header()
        self.assertIsInstance(main.spoof_header(), dict)
        return None

    def test_read_page(self) -> None:
        good_url = "https://www.furaffinity.net/msg/submissions/"
        bad_url = "https://www.furaffinity.net/msg"
        self.assertTrue(main.read_page(good_url))
        self.assertFalse(main.read_page(bad_url))
        page = main.read_page(good_url)
        self.assertNotIn(page, "Please log in!")
        return None

    def test_parse_favorite_links(self) -> None:
        results = main.parse_favorite_links(self.page)
        self.assertIsInstance(results, set)
        self.assertEqual(len(results), 72)
        self.assertEqual(len(main.parse_favorite_links("")), 0)
        return None

    def test_find_next_page(self) -> None:
        results = main.find_next_page(self.page, "fakeuser")
        self.assertIsInstance(results, str)
        self.assertTrue(results)
        self.assertFalse(main.find_next_page("", "fakeuser"))
        return None

    def test_get_download_div(self) -> None:
        expected = (
            '<div class="download"><a href="//d.facdn.net/art/son-of'
            "-liberty/1608334656/1608334656.son-of-liberty_ladybonda"
            'gesmol.jpg">Download</a></div>'
        )
        results = main.get_download_div(self.download_page)
        self.assertEqual(results, expected)
        self.assertEqual(main.get_download_div(""), "")
        return None

    def test_parse_div_url(self) -> None:
        provided = (
            '<div class="download"><a href="//d.facdn.net/art/son-of'
            "-liberty/1608334656/1608334656.son-of-liberty_ladybonda"
            'gesmol.jpg">Download</a></div>'
        )
        expected = (
            "https://d.facdn.net/art/son-of-liberty/1608334656/"
            "1608334656.son-of-liberty_ladybondagesmol.jpg"
        )
        self.assertEqual(main.parse_div_url(provided), expected)

    def test_get_list_from_file(self) -> None:
        results = main.get_list_from_file("fakeuser", "test")
        self.assertEqual(len(results), 3)
