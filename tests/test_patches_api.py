"""
Unit tests for NinjaOne live patch reporting API integration.
"""

from unittest.mock import MagicMock
import pytest

from src.api.patches import (
    get_all_os_patches,
    get_all_software_patches,
    get_fleet_patch_counts,
)


class TestPatchesAPI:
    def test_get_fleet_patch_counts_approved_priority(self):
        client = MagicMock()
        client.get_paginated.side_effect = [
            # OS patches
            [
                {"deviceId": 101, "status": "APPROVED", "name": "KB5001234"},
                {"deviceId": 101, "status": "APPROVED", "name": "KB5001235"},
                {"deviceId": 102, "status": "PENDING", "name": "KB5001236"},
                {"deviceId": 103, "status": "REJECTED", "name": "KB5001237"},
            ],
            # Software patches
            [
                {"deviceId": 101, "status": "APPROVED", "name": "Chrome Update"},
                {"deviceId": 102, "status": "REJECTED", "name": "Blocked App"},
            ],
        ]

        os_counts, sw_counts = get_fleet_patch_counts(client)
        # Device 101 has 2 APPROVED patches
        assert os_counts.get(101) == 2
        # Device 102 has 0 APPROVED patches (only pending, but approved exist in fleet)
        assert os_counts.get(102) is None
        # Device 103 rejected patch is excluded
        assert os_counts.get(103) is None

        # Software patch count for device 101
        assert sw_counts.get(101) == 1
        assert sw_counts.get(102) is None

    def test_get_fleet_patch_counts_pending_fallback(self):
        client = MagicMock()
        client.get_paginated.side_effect = [
            # OS patches with only PENDING statuses (no explicit APPROVED in environment)
            [
                {"deviceId": 201, "status": "PENDING", "name": "KB5001"},
                {"deviceId": 201, "status": "PENDING", "name": "KB5002"},
                {"deviceId": 202, "status": "PENDING", "name": "KB5003"},
            ],
            # Software patches empty
            [],
        ]

        os_counts, sw_counts = get_fleet_patch_counts(client)
        assert os_counts.get(201) == 2
        assert os_counts.get(202) == 1
        assert sw_counts == {}

    def test_get_all_os_patches_fallback(self):
        client = MagicMock()
        # Primary endpoint raises error, fallback returns data
        client.get_paginated.side_effect = [
            Exception("404 endpoint not found"),
            [{"deviceId": 301, "status": "APPROVED", "name": "KB9999"}],
        ]

        res = get_all_os_patches(client)
        assert len(res) == 1
        assert res[0]["deviceId"] == 301
