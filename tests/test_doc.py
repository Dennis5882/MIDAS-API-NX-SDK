import json

import responses

from midas_nx import doc


@responses.activate
def test_new_project_sends_empty_argument(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/doc/NEW", json={}, status=200)
    doc.new_project(client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Argument": {}}


@responses.activate
def test_open_project_sends_path_as_argument(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/doc/OPEN", json={}, status=200)
    doc.open_project("C:\\models\\a.mgb", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Argument": "C:\\models\\a.mgb"}


@responses.activate
def test_stage_as_sends_stage_step_and_export_path(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/doc/STAGAS", json={}, status=200)
    doc.stage_as("Fase1", export_path="C:\\MIDAS\\FASE1.mcb", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Argument": {"STAGE_STEP": "Fase1", "EXPORT_PATH": "C:\\MIDAS\\FASE1.mcb"}
    }


@responses.activate
def test_analyze_without_type_sends_empty_argument(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/doc/ANAL", json={}, status=200)
    doc.analyze(client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Argument": {}}


@responses.activate
def test_analyze_with_type_sends_type(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/doc/ANAL", json={}, status=200)
    doc.analyze("PUSHOVER", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Argument": {"TYPE": "PUSHOVER"}}
