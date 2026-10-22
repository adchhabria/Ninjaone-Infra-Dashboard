"""
Unit tests for NinjaOne live patch reporting API integration.
"""

from unittest.mock import MagicMock
import pytest

from src.api.patches import (
    get_all_os_patches,
    get_all_software_patches,
    get_fleet_patch_counts,
    is_os_security_or_cumulative_patch,
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

    def test_is_os_security_or_cumulative_patch_heuristics(self):
        # 1. Valid OS Cumulative & Security Updates
        assert is_os_security_or_cumulative_patch("2024-10 Cumulative Update for Windows Server 2022 for x64-based Systems (KB5044281)") is True
        assert is_os_security_or_cumulative_patch("Security Update for Windows Server 2019 (KB5034441)") is True
        assert is_os_security_or_cumulative_patch("2024-08 Cumulative Update for Windows 11 Version 23H2 (KB5041585)") is True

        # 2. Excluded non-OS products
        assert is_os_security_or_cumulative_patch("2024-10 Cumulative Update for .NET Framework 3.5 and 4.8.1 (KB5044091)") is False
        assert is_os_security_or_cumulative_patch("Security Update for Microsoft Office 2016 (KB5002457)") is False
        assert is_os_security_or_cumulative_patch("Security Update for SQL Server 2019 RTM GDR (KB5014353)") is False
        assert is_os_security_or_cumulative_patch("Security Update for Microsoft Exchange Server 2019") is False

        # 3. Benign updates
        assert is_os_security_or_cumulative_patch("Intel Corporation - Extension - 1.0.0.1") is False
        assert is_os_security_or_cumulative_patch("Security Intelligence Update for Microsoft Defender Antivirus") is False

        # 4. Custom keyword addition
        assert is_os_security_or_cumulative_patch("Windows Server Hotfix KB9999", included_keywords=["Hotfix"]) is True

        # 5. Custom product exclusion
        assert is_os_security_or_cumulative_patch("Custom Driver Security Update", excluded_products=["Driver"]) is False

        # 6. Explicit title match override
        assert is_os_security_or_cumulative_patch("Custom Kernel Patch Alpha", selected_patch_titles=["Custom Kernel Patch Alpha"]) is True

    def test_get_fleet_patch_counts_sec_counts_and_discovered_titles(self):
        client = MagicMock()
        client.get_paginated.side_effect = [
            # OS patches
            [
                {"deviceId": 401, "status": "APPROVED", "name": "2024-10 Cumulative Update for Windows Server 2022"},
                {"deviceId": 401, "status": "APPROVED", "name": "Cumulative Update for .NET Framework 4.8.1"},
                {"deviceId": 402, "status": "APPROVED", "name": "Cumulative Update for .NET Framework 4.8.1"},
            ],
            # Software patches
            [
                {"deviceId": 401, "status": "APPROVED", "name": "Chrome Update"},
            ],
        ]

        res = get_fleet_patch_counts(client)
        # Device 401 has 2 approved OS patches, but ONLY 1 is an OS Cumulative Update
        assert res.os_counts[401] == 2
        assert res.os_sec_counts[401] == 1
        assert "2024-10 Cumulative Update for Windows Server 2022" in res.os_sec_names[401]

        # Device 402 has 1 approved OS patch (.NET), but 0 OS Cumulative/Security updates!
        assert res.os_counts[402] == 1
        assert res.os_sec_counts.get(402) is None

        # Discovered titles list contains all distinct titles
        assert "2024-10 Cumulative Update for Windows Server 2022" in res.discovered_titles
        assert "Cumulative Update for .NET Framework 4.8.1" in res.discovered_titles
        assert "Chrome Update" in res.discovered_titles
