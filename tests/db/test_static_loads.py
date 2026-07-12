import json

import responses

from midas_nx.db.static_loads import BeamLoad, NodalLoad, PressureLoad, SelfWeight, StaticLoadCase


@responses.activate
def test_static_load_case_create(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/STLD", json={}, status=200)
    StaticLoadCase.create({1: {"NAME": "DL", "TYPE": "D", "DESC": "Dead Load"}}, client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"1": {"NAME": "DL", "TYPE": "D", "DESC": "Dead Load"}}}


@responses.activate
def test_self_weight_create(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/BODF", json={}, status=200)
    SelfWeight.create({1: {"LCNAME": "DL", "GROUP_NAME": "", "FV": [0, 0, -1]}}, client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"1": {"LCNAME": "DL", "GROUP_NAME": "", "FV": [0, 0, -1]}}}


@responses.activate
def test_nodal_load_create_keyed_by_node_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/CNLD", json={}, status=200)
    NodalLoad.create(
        {8: {"ITEMS": [{"ID": 1, "LCNAME": "LL", "FZ": -50.0}]}},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"8": {"ITEMS": [{"ID": 1, "LCNAME": "LL", "FZ": -50.0}]}}}


@responses.activate
def test_beam_load_create_keyed_by_element_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/BMLD", json={}, status=200)
    BeamLoad.create(
        {
            115: {
                "ITEMS": [
                    {
                        "ID": 1,
                        "LCNAME": "L",
                        "CMD": "BEAM",
                        "TYPE": "UNILOAD",
                        "DIRECTION": "GZ",
                        "D": [0, 1, 0, 0],
                        "P": [-50, -50, 0, 0],
                    }
                ]
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["115"]["ITEMS"][0]["TYPE"] == "UNILOAD"


@responses.activate
def test_pressure_load_create_keyed_by_element_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/PRES", json={}, status=200)
    PressureLoad.create(
        {
            116: {
                "ITEMS": [
                    {
                        "ID": 1,
                        "LCNAME": "Element_Type1",
                        "CMD": "PRES",
                        "ELEM_TYPE": "PLATE",
                        "FACE_EDGE_TYPE": "FACE",
                        "DIRECTION": "LZ",
                        "FORCES": [-10, 0, 0, 0, 0],
                    }
                ]
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["116"]["ITEMS"][0]["FORCES"] == [-10, 0, 0, 0, 0]
