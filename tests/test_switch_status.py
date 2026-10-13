"""Regression tests for Apex polling and output commands.

Run with python3 -m unittest discover -s tests -v. Lightweight HA module
stubs let these tests exercise the actual switch implementation without
installing Home Assistant or connecting to a controller.
"""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch


def load_switch():
    """Load the production module with only its HA base classes stubbed."""
    source_dir = Path(__file__).resolve().parents[1] / "custom_components" / "apex"
    package = ModuleType("_apex_switch_tests")
    package.__path__ = [str(source_dir)]
    package.ApexEntity = type("ApexEntity", (), {})
    ha = ModuleType("homeassistant")
    components = ModuleType("homeassistant.components")
    switch_platform = ModuleType("homeassistant.components.switch")
    switch_platform.SwitchEntity = type("SwitchEntity", (), {})
    modules = {
        "_apex_switch_tests": package,
        "homeassistant": ha,
        "homeassistant.components": components,
        "homeassistant.components.switch": switch_platform,
    }
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(
            "_apex_switch_tests.switch", source_dir / "switch.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.Switch


Switch = load_switch()


def output(status, did="6_8"):
    return {
        "did": did,
        "name": "ATO",
        "type": "24v",
        "status": [status, "", "OK", ""],
    }


class PollingStatusTests(unittest.TestCase):
    def setUp(self):
        self.initial = output("AOF")
        self.coordinator = SimpleNamespace(data={"outputs": [self.initial]})
        self.entity = Switch(self.coordinator, self.initial, {})

    def test_polling_replaces_attributes_for_every_mode(self):
        for status in ("OFF", "AON", "ON", "AOF"):
            with self.subTest(status=status):
                current = output(status)
                self.coordinator.data = {"outputs": [current]}
                self.assertEqual(self.entity.extra_state_attributes["status"][0], status)
                self.assertEqual(self.entity.is_on, status in ("ON", "AON"))
                self.assertIsNot(self.entity.extra_state_attributes, current)

    def test_mode_changes_refresh_when_output_stays_off(self):
        self.assertFalse(self.entity.is_on)
        self.coordinator.data = {"outputs": [output("OFF")]}
        self.assertFalse(self.entity.is_on)
        self.assertEqual(self.entity.extra_state_attributes["status"][0], "OFF")
        self.coordinator.data = {"outputs": [output("AOF")]}
        self.assertEqual(self.entity.extra_state_attributes["status"][0], "AOF")

    def test_matches_output_id_after_list_reordering(self):
        self.coordinator.data = {"outputs": [output("ON", "other"), output("OFF")]}
        self.assertEqual(self.entity.extra_state_attributes["status"][0], "OFF")

    def test_missing_output_does_not_publish_cached_mode(self):
        for data in (None, {}, {"outputs": []}, {"outputs": [output("ON", "other")]}):
            with self.subTest(data=data):
                self.coordinator.data = data
                self.assertEqual(self.entity.extra_state_attributes, {})

    def test_feed_cycle_metadata_is_preserved(self):
        feed = {"did": "1", "name": "Feed A", "type": "Feed"}
        entity = Switch(self.coordinator, feed, {})
        self.assertEqual(entity.extra_state_attributes, feed)
        self.assertIsNot(entity.extra_state_attributes, feed)


class OutputCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_output_commands_request_coordinator_refresh(self):
        for status, method in (("ON", "async_turn_on"), ("OFF", "async_turn_off")):
            with self.subTest(status=status):
                current = output("AOF")
                response = output(status)
                coordinator = SimpleNamespace(
                    data={"outputs": [current]},
                    hass=SimpleNamespace(async_add_executor_job=AsyncMock(return_value=response)),
                    apex=SimpleNamespace(toggle_output=Mock()),
                    async_request_refresh=AsyncMock(),
                )
                entity = Switch(coordinator, current, {})
                entity.async_write_ha_state = Mock()

                async def refresh():
                    coordinator.data = {"outputs": [output(status)]}

                coordinator.async_request_refresh.side_effect = refresh
                await getattr(entity, method)()
                coordinator.hass.async_add_executor_job.assert_awaited_once_with(
                    coordinator.apex.toggle_output, "6_8", status
                )
                coordinator.async_request_refresh.assert_awaited_once()
                self.assertEqual(entity.extra_state_attributes["status"][0], status)


if __name__ == "__main__":
    unittest.main()
