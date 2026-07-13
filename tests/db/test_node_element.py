import json

import responses

from midas_nx.db.node_element import DomainElement, Element, MainDomain, Node, Skew, SubDomain


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


@responses.activate
def test_skew_create_sends_angle_method_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/SKEW", json={}, status=200)

    Skew.create({1: {"iMETHOD": 1, "ANGLE_X": 45, "ANGLE_Y": 0, "ANGLE_Z": 90}}, client=gen_client)

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {"1": {"iMETHOD": 1, "ANGLE_X": 45, "ANGLE_Y": 0, "ANGLE_Z": 90}}
    }


@responses.activate
def test_main_domain_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/MADO", json={}, status=200)

    MainDomain.create(
        {1: {"NAME": "DM1", "TYPE": 4, "MATL": 0, "PROP": 0, "SUB_TYPE": 2}}, client=gen_client
    )

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {"1": {"NAME": "DM1", "TYPE": 4, "MATL": 0, "PROP": 0, "SUB_TYPE": 2}}
    }


@responses.activate
def test_sub_domain_create_sends_gen_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/SBDO", json={}, status=200)

    SubDomain.create(
        {
            1: {
                "SUB_DOMAIN_NAME": "SDM1",
                "MEMBER_TYPE": 1,
                "V1": 0,
                "V2": 90,
                "DOMAIN_NAME": "DM1",
                "bUseMt": True,
                "THICKNESS": 0.2,
            }
        },
        client=gen_client,
    )

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {
            "1": {
                "SUB_DOMAIN_NAME": "SDM1",
                "MEMBER_TYPE": 1,
                "V1": 0,
                "V2": 90,
                "DOMAIN_NAME": "DM1",
                "bUseMt": True,
                "THICKNESS": 0.2,
            }
        }
    }


@responses.activate
def test_domain_element_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/DOEL", json={}, status=200)

    DomainElement.create(
        {163: {"TYPE": 1, "KEY_DOMAIN": 1, "MAIN_DOMAIN_NAME": "DM1"}}, client=gen_client
    )

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {"163": {"TYPE": 1, "KEY_DOMAIN": 1, "MAIN_DOMAIN_NAME": "DM1"}}
    }
