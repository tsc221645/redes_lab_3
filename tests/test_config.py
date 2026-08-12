import os
import tempfile
import unittest
from pathlib import Path
from src.common.config import load_config

class ConfigEnvironmentTests(unittest.TestCase):
    def test_env_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "router.json"
            path.write_text('{"node_id":"A","role":"router","listen_ip":"${TEST_ROUTER_IP}","listen_port":5000}', encoding="utf-8")
            previous = os.environ.get("TEST_ROUTER_IP")
            os.environ["TEST_ROUTER_IP"] = "100.64.0.1"
            try:
                self.assertEqual(load_config(path).listen_ip, "100.64.0.1")
            finally:
                if previous is None:
                    os.environ.pop("TEST_ROUTER_IP", None)
                else:
                    os.environ["TEST_ROUTER_IP"] = previous
