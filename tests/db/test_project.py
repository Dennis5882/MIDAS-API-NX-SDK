import json

import pytest
import responses

from midas_nx.client import UnsupportedMethodError
from midas_nx.db.project import StructureType, Unit


@responses.activate
def test_unit_update_sends_documented_assign_shape(gen_client):
    responses.add(responses.PUT, "https://x.test:443/gen/db/UNIT", json={}, status=200)
    Unit.update({1: {"FORCE": "KN", "DIST": "M", "HEAT": "KJ", "TEMPER": "C"}}, client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"1": {"FORCE": "KN", "DIST": "M", "HEAT": "KJ", "TEMPER": "C"}}}


@responses.activate
def test_unit_create_raises_before_any_http_call(gen_client):
    with pytest.raises(UnsupportedMethodError):
        Unit.create({1: {"FORCE": "KN"}}, client=gen_client)
    assert len(responses.calls) == 0


@responses.activate
def test_structure_type_delete_raises_before_any_http_call(gen_client):
    with pytest.raises(UnsupportedMethodError):
        StructureType.delete([1], client=gen_client)
    assert len(responses.calls) == 0
