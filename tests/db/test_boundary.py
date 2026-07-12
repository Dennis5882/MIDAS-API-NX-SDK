import json

import responses

from midas_nx.db.boundary import Constraint


@responses.activate
def test_constraint_create_sends_items_array_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/CONS", json={}, status=200)

    Constraint.create(
        {1: {"ITEMS": [{"ID": 1, "GROUP_NAME": "Support", "CONSTRAINT": "1111111"}]}},
        client=gen_client,
    )

    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Assign": {"1": {"ITEMS": [{"ID": 1, "GROUP_NAME": "Support", "CONSTRAINT": "1111111"}]}}
    }
