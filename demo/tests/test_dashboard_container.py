"""Phase 10 container entrypoint tests; Docker daemon not needed."""
import contextlib
import io
import os
import unittest
from unittest.mock import MagicMock, patch

from nawa_demo import dashboard_container


class DockerEntrypointTests(unittest.TestCase):
    def test_intake_cannot_be_enabled_in_demo_mode(self):
        with patch.dict(os.environ, {'NAWA_INTAKE': 'synthetic', 'NAWA_AUTH': 'demo', 'NAWA_STORAGE': 'memory'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'requires OIDC and PostgreSQL'):
                dashboard_container.serve()

    @patch('nawa_demo.dashboard_container.HTTPServer')
    @patch('nawa_demo.dashboard_container.make_handler')
    @patch('nawa_demo.dashboard_container.DashboardState')
    def test_container_binds_inside_container(self, state_cls, handler, http_cls):
        http_cls.return_value.__enter__.return_value.serve_forever.return_value = None
        with contextlib.redirect_stdout(io.StringIO()):
            dashboard_container.serve()
        state_cls.assert_called_once_with()
        handler.assert_called_once_with(state_cls.return_value)
        http_cls.assert_called_once_with(('0.0.0.0', 8765), handler.return_value)
        http_cls.return_value.__enter__.return_value.serve_forever.assert_called_once_with()

    @patch('nawa_demo.dashboard_container.HTTPServer')
    def test_keyboard_interrupt_stops_cleanly(self, http_cls):
        http_cls.return_value.__enter__.return_value.serve_forever.side_effect = KeyboardInterrupt
        with contextlib.redirect_stdout(io.StringIO()):
            dashboard_container.serve()
        http_cls.return_value.__exit__.assert_called_once()

    def test_local_dashboard_binding_unmodified(self):
        # Prevent a mistaken replacement of the existing local-only launcher.
        import inspect
        from nawa_demo.dashboard import main
        self.assertIn("'127.0.0.1'", inspect.getsource(main))


if __name__ == '__main__':
    unittest.main()
