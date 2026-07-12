import json

import responses

from midas_nx.db.node_element import Element, Node


@responses.activate
def test_node_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/NODE", json={}, status=200)

    Node.create({1: {"X": 0, "Y": 0, "Z": 3.2}}, client=gen_client)

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"1": {"X": 0, "Y": 0, "Z": 3.2}}}


@responses.activate
def test_node_get_returns_full_response(gen_client):
    responses.add(
        responses.GET, "https://x.test:443/gen/db/NODE",
        json={"NODE": {"1": {"X": 0, "Y": 0, "Z": 0}}}, status=200,
    )
    result = Node.get(client=gen_client)
    assert result == {"NODE": {"1": {"X": 0, "Y": 0, "Z": 0}}}


@responses.activate
def test_node_delete_sends_null_per_id(gen_client):
    responses.add(responses.DELETE, "https://x.test:443/gen/db/NODE", json={}, status=200)
    Node.delete([4], client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"4": None}}


@responses.activate
def test_element_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/ELEM", json={}, status=200)

    Element.create(
        {1: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2], "ANGLE": 0}},
        client=gen_client,
    )

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {"1": {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2], "ANGLE": 0}}
    }
