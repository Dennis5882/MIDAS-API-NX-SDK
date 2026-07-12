import json

import pytest
import responses

from midas_nx.client import UnsupportedMethodError
from midas_nx.db.properties.material import Material, MaterialModifyConcrete
from midas_nx.db.properties.section import Section
from midas_nx.db.properties.thickness import Thickness


@responses.activate
def test_material_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/MATL", json={}, status=200)

    Material.create(
        {
            1: {
                "TYPE": "CONC",
                "NAME": "C32",
                "PARAM": [{"P_TYPE": 1, "STANDARD": "AS17(RC)", "DB": "C32"}],
            }
        },
        client=gen_client,
    )

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {
            "1": {
                "TYPE": "CONC",
                "NAME": "C32",
                "PARAM": [{"P_TYPE": 1, "STANDARD": "AS17(RC)", "DB": "C32"}],
            }
        }
    }


@responses.activate
def test_matd_create_raises_before_any_http_call(gen_client):
    with pytest.raises(UnsupportedMethodError):
        MaterialModifyConcrete.create({1: {"TYPE": "CONC"}}, client=gen_client)
    assert len(responses.calls) == 0


@responses.activate
def test_matd_get_and_put_are_allowed(gen_client):
    responses.add(responses.GET, "https://x.test:443/gen/db/MATD", json={"MATD": {}}, status=200)
    responses.add(responses.PUT, "https://x.test:443/gen/db/MATD", json={}, status=200)

    MaterialModifyConcrete.get(client=gen_client)
    MaterialModifyConcrete.update(
        {1: {"TYPE": "CONC", "NAME": "C16/20", "REBAR_CODENAME": "EN04(RC)"}},
        client=gen_client,
    )

    assert len(responses.calls) == 2


@responses.activate
def test_matd_delete_raises_before_any_http_call(gen_client):
    with pytest.raises(UnsupportedMethodError):
        MaterialModifyConcrete.delete([1], client=gen_client)
    assert len(responses.calls) == 0


@responses.activate
def test_section_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/SECT", json={}, status=200)

    Section.create(
        {
            1: {
                "SECTTYPE": "DBUSER",
                "SECT_NAME": "H300x150",
                "SECT_BEFORE": {
                    "SHAPE": "H",
                    "OFFSET_PT": "CC",
                    "DATATYPE": 1,
                    "SECT_I": {"DB_NAME": "KS21", "SECT_NAME": "H300x150x6.5/9"},
                },
            }
        },
        client=gen_client,
    )

    sent = responses.calls[0].request
    body = json.loads(sent.body)["Assign"]["1"]
    assert body["SECTTYPE"] == "DBUSER"
    # DATATYPE is a sibling of SECT_I inside SECT_BEFORE, not nested inside it
    # (docs/manual/04_DB_Properties.md #12-A) — regression check for that mix-up.
    assert body["SECT_BEFORE"]["DATATYPE"] == 1
    assert "DATATYPE" not in body["SECT_BEFORE"]["SECT_I"]


@responses.activate
def test_thickness_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/THIK", json={}, status=200)

    Thickness.create(
        {1: {"NAME": "T200", "TYPE": "VALUE", "bINOUT": False, "T_IN": 0.20, "T_OUT": 0, "O_VALUE": 0}},
        client=gen_client,
    )

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {"1": {"NAME": "T200", "TYPE": "VALUE", "bINOUT": False, "T_IN": 0.20, "T_OUT": 0, "O_VALUE": 0}}
    }
