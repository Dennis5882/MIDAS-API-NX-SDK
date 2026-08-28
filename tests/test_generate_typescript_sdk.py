"""Shadow-run guards for the contract-first npm resource generator."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_typescript_sdk as generator  # noqa: E402


def test_contracted_resource_surfaces_match_the_legacy_sdk_anchor():
    """A Stage 3 switch is allowed only when it preserves generated output."""
    resources = {resource["endpoint"]: resource for resource in generator._load_resources()}
    contracts = generator._contract_resource_surfaces()

    assert contracts
    for endpoint, surface in contracts.items():
        resource = resources[endpoint]
        assert resource["name"] == surface["name"]
        assert resource["products"] == surface["products"]
        assert resource["methods"] == surface["methods"]
        assert resource["contractManualChapter"] == surface["manualChapter"]
