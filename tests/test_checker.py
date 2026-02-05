from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vlc_updater.checker import _extract_version, compare_versions, run_check
from vlc_updater.db import connect, fetch_history, init_db, insert_check


class CheckerTests(unittest.TestCase):
    def test_extract_version_prefers_vlc_context(self) -> None:
        html = """
        <html>
          <body>
            <h1>VLC media player 3.0.21</h1>
            <p>Other number 2026.01</p>
          </body>
        </html>
        """
        self.assertEqual(_extract_version(html), "3.0.21")

    def test_compare_versions(self) -> None:
        self.assertEqual(compare_versions("3.0.20", "3.0.21"), 1)
        self.assertEqual(compare_versions("3.0.21", "3.0.21"), 0)
        self.assertIsNone(compare_versions(None, "3.0.21"))

    def test_run_check_with_unreachable_url_returns_error(self) -> None:
        result = run_check("3.0.20", source_url="http://127.0.0.1:9")
        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error_message)


class DatabaseTests(unittest.TestCase):
    def test_insert_and_fetch_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.sqlite3"
            conn = connect(db_path)
            try:
                init_db(conn)
                row_id = insert_check(
                    conn,
                    {
                        "created_at": "2026-01-01T00:00:00+00:00",
                        "product": "vlc",
                        "installed_version": "3.0.20",
                        "latest_version": "3.0.21",
                        "update_available": 1,
                        "source_url": "https://example.com/vlc",
                        "status": "ok",
                        "error_message": None,
                    },
                )
                rows = fetch_history(conn)
            finally:
                conn.close()

            self.assertEqual(row_id, 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["latest_version"], "3.0.21")


if __name__ == "__main__":
    unittest.main()
