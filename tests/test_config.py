import os
import unittest
from unittest.mock import patch

from prediction_market_lab import LabConfig


class LabConfigTests(unittest.TestCase):
    def test_defaults_are_analysis_only(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = LabConfig.from_env()

        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(str(config.data_dir), "data")
        self.assertFalse(config.enable_trading)

    def test_env_overrides_are_loaded(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PML_LOG_LEVEL": "debug",
                "PML_DATA_DIR": "./scratch",
                "PML_ENABLE_TRADING": "true",
            },
            clear=True,
        ):
            config = LabConfig.from_env()

        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(str(config.data_dir), "scratch")
        self.assertTrue(config.enable_trading)


if __name__ == "__main__":
    unittest.main()
