"""Tests for DbResource's cross-cutting .info() classmethod (base.py) —
uses Node as a representative concrete resource, mirroring test_client.py's
pattern of testing shared client behavior via a stand-in.
"""
import pytest
import responses

from midas_nx.client import ProductMismatchError
from midas_nx.db.node_element import Node


@responses.activate
def test_info_hits_info_db_prefixed_endpoint(gen_client):
    responses.add(
        responses.GET,
        "https://x.test:443/gen/info/db/NODE",
        json={"NODE": {"X": "double", "Y": "double", "Z": "double"}},
        status=200,
    )

    result = Node.info(client=gen_client)

    assert result == {"NODE": {"X": "double", "Y": "double", "Z": "double"}}
    sent = responses.calls[0].request
    assert sent.url == "https://x.test:443/gen/info/db/NODE"


def test_info_still_enforces_product_check(gen_client):
    from midas_nx.db.bridge import BridgeGirderDiagram

    with pytest.raises(ProductMismatchError):
        BridgeGirderDiagram.info(client=gen_client)
