import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# We need to import main from sharpei, but it doesn't exist yet.
# This test will fail on import or when calling main.

class TestCLI(unittest.TestCase):
    def setUp(self):
        # Save original env
        self.original_api_key = os.environ.get("SHARPEI_API_KEY")
        if "SHARPEI_API_KEY" in os.environ:
            del os.environ["SHARPEI_API_KEY"]

    def tearDown(self):
        # Restore original env
        if self.original_api_key:
            os.environ["SHARPEI_API_KEY"] = self.original_api_key
        elif "SHARPEI_API_KEY" in os.environ:
            del os.environ["SHARPEI_API_KEY"]

    @patch("uvicorn.run")
    @patch("threading.Thread")
    @patch("sharpei.open_browser")
    def test_main_default_args(self, mock_open_browser, mock_thread, mock_uvicorn_run):
        import sharpei
        # We expect a main function to exist
        with patch.object(sys, 'argv', ['sharpei.py']):
            sharpei.main()
        
        mock_uvicorn_run.assert_called_once_with(
            app="app.main:app", 
            host="127.0.0.1", 
            port=8000, 
            reload=True,
            ssl_certfile=None,
            ssl_keyfile=None
        )

    @patch("uvicorn.run")
    @patch("threading.Thread")
    def test_main_custom_args(self, mock_thread, mock_uvicorn_run):
        import sharpei
        with patch.object(sys, 'argv', [
            'sharpei.py', 
            '--host', '0.0.0.0', 
            '--port', '9000', 
            '--no-browser',
            '--api-key', 'secret-key'
        ]):
            sharpei.main()
        
        mock_uvicorn_run.assert_called_once_with(
            app="app.main:app", 
            host="0.0.0.0", 
            port=9000, 
            reload=False,
            ssl_certfile=None,
            ssl_keyfile=None
        )
        self.assertEqual(os.environ.get("SHARPEI_API_KEY"), "secret-key")
        mock_thread.assert_not_called()

    @patch("uvicorn.run")
    @patch("threading.Thread")
    def test_main_ssl_args(self, mock_thread, mock_uvicorn_run):
        import sharpei
        with patch.object(sys, 'argv', [
            'sharpei.py', 
            '--ssl-cert', 'cert.pem', 
            '--ssl-key', 'key.pem'
        ]):
            sharpei.main()
        
        mock_uvicorn_run.assert_called_once_with(
            app="app.main:app", 
            host="127.0.0.1", 
            port=8000, 
            reload=True,
            ssl_certfile='cert.pem',
            ssl_keyfile='key.pem'
        )
        # Check if open_browser was called with is_https=True
        # We need to check the thread call since open_browser runs in a thread
        mock_thread.assert_called_once()
        args, kwargs = mock_thread.call_args
        self.assertEqual(kwargs['target'], sharpei.open_browser)
        self.assertEqual(kwargs['args'], ("127.0.0.1", 8000, True))

if __name__ == "__main__":
    unittest.main()
