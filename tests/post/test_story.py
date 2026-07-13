import json

import responses

from midas_nx.post import story


@responses.activate
def test_get_story_drift_table_defaults_to_comb_and_forwards_all_kwargs(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_drift_table(
        table_name="Story Drift(Comb)",
        unit={"FORCE": "kN", "DIST": "mm"},
        styles={"FORMAT": "Fixed", "PLACE": 4},
        components=["Story", "Story Drift"],
        node_elems={"TO": "1 to 5"},
        load_case_names=["gLCB1(CB)"],
        opt_cs=True,
        stage_step=["CS1:001(first)"],
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Argument": {
            "TABLE_NAME": "Story Drift(Comb)",
            "TABLE_TYPE": "STORY_DRIFT_COMB",
            "UNIT": {"FORCE": "kN", "DIST": "mm"},
            "STYLES": {"FORMAT": "Fixed", "PLACE": 4},
            "COMPONENTS": ["Story", "Story Drift"],
            "NODE_ELEMS": {"TO": "1 to 5"},
            "LOAD_CASE_NAMES": ["gLCB1(CB)"],
            "OPT_CS": True,
            "STAGE_STEP": ["CS1:001(first)"],
        }
    }


@responses.activate
def test_get_story_drift_table_accepts_specific_variant(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_drift_table(story.TABLE_TYPE_STORY_DRIFT_X, "Story Drift(X)", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STORY_DRIFT_X"


@responses.activate
def test_get_story_displacement_table_defaults_to_comb(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_displacement_table(table_name="STORY_DISPLACEMENT_COMB", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STORY_DISPLACEMENT_COMB"


@responses.activate
def test_get_story_displacement_table_accepts_specific_variant(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_displacement_table(
        story.TABLE_TYPE_STORY_DISPLACEMENT_Y, "STORY_DISPLACEMENT_Y", client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STORY_DISPLACEMENT_Y"


@responses.activate
def test_get_story_shear_force_rs_table_sends_rs_load_case(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_shear_force_rs_table(
        table_name="STORY_SHEAR_FOR_RS", load_case_names=["Rx(RS)"], client=gen_client
    )
    sent = responses.calls[0].request
    body = json.loads(sent.body)["Argument"]
    assert body["TABLE_TYPE"] == "STORY_SHEAR_FOR_RS"
    assert body["LOAD_CASE_NAMES"] == ["Rx(RS)"]


@responses.activate
def test_get_story_shear_force_coefficient_table_sends_rs_load_case(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_shear_force_coefficient_table(
        table_name="STORY_SHEAR_FORCE_COEFFICIENT", load_case_names=["Rx(RS)"], client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STORY_SHEAR_FORCE_COEFFICIENT"


@responses.activate
def test_get_story_mode_shape_table_sends_minimal_argument(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_mode_shape_table(
        table_name="STORY_MODE_SHAPE",
        unit={"FORCE": "kN", "DIST": "m"},
        styles={"FORMAT": "Fixed", "PLACE": 6},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Argument": {
            "TABLE_NAME": "STORY_MODE_SHAPE",
            "TABLE_TYPE": "STORY_MODE_SHAPE",
            "UNIT": {"FORCE": "kN", "DIST": "m"},
            "STYLES": {"FORMAT": "Fixed", "PLACE": 6},
        }
    }


@responses.activate
def test_get_story_shear_force_ratio_table_sends_load_case(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_shear_force_ratio_table(
        table_name="STORY_SHEAR_FORCE_RATIO", load_case_names=["EX(ST)"], client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STORY_SHEAR_FORCE_RATIO"


@responses.activate
def test_get_story_eccentricity_table_uses_documented_misspelled_type(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_eccentricity_table(table_name="STORY_ECNTRICITY", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Argument": {"TABLE_NAME": "STORY_ECNTRICITY", "TABLE_TYPE": "STORY_ECNTRICITY"}
    }


@responses.activate
def test_get_overturning_moment_table_sends_load_case(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_overturning_moment_table(
        table_name="OVERTURNING_MOMENT", load_case_names=["Rx(RS)"], client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "OVERTURNING_MOMENT"


@responses.activate
def test_get_story_axial_force_sum_table_sends_minimal_argument(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_axial_force_sum_table(table_name="STORY_AXIAL_FORCE_SUM", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Argument": {"TABLE_NAME": "STORY_AXIAL_FORCE_SUM", "TABLE_TYPE": "STORY_AXIAL_FORCE_SUM"}
    }


@responses.activate
def test_get_story_stability_coefficient_table_defaults_to_x(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_stability_coefficient_table(table_name="STORY_STABILITY_COEFFICIENT_X", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STORY_STABILITY_COEFFICIENT_X"


@responses.activate
def test_get_story_stability_coefficient_table_accepts_y(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_story_stability_coefficient_table(
        story.TABLE_TYPE_STORY_STABILITY_COEFFICIENT_Y, "STORY_STABILITY_COEFFICIENT_Y", client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STORY_STABILITY_COEFFICIENT_Y"


@responses.activate
def test_get_torsional_irregularity_table_defaults_to_x(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_torsional_irregularity_table(table_name="TorIrr(X)", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "TORSIONAL_IRREGULARITY_X"


@responses.activate
def test_get_torsional_amplification_factor_table_accepts_y(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_torsional_amplification_factor_table(
        story.TABLE_TYPE_TORSIONAL_AMPLIFICATION_FACTOR_Y, "TorAmp(Y)", client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "TORSIONAL_AMPLIFICATION_FACTOR_Y"


@responses.activate
def test_get_stiffness_irregularity_table_defaults_to_x(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_stiffness_irregularity_table(table_name="STIFFNESS_IRREGULARITY_X", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "STIFFNESS_IRREGULARITY_X"


@responses.activate
def test_get_capacity_irregularity_table_sends_minimal_argument(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_capacity_irregularity_table(table_name="CAPACITY_IRREGULARITY", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Argument": {"TABLE_NAME": "CAPACITY_IRREGULARITY", "TABLE_TYPE": "CAPACITY_IRREGULARITY"}
    }


@responses.activate
def test_get_criteria_for_regularity_in_plan_table_sends_minimal_argument(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_criteria_for_regularity_in_plan_table(
        table_name="CRITERIA_FOR_REGULARITY_IN_PLAN", client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {
        "Argument": {
            "TABLE_NAME": "CRITERIA_FOR_REGULARITY_IN_PLAN",
            "TABLE_TYPE": "CRITERIA_FOR_REGULARITY_IN_PLAN",
        }
    }


@responses.activate
def test_get_ultimate_story_shear_force_check_table_sends_load_case(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_ultimate_story_shear_force_check_table(
        table_name="ULTIMATE_STORY_SHEAR_FORCE_CHECK", load_case_names=["Rx(RS)"], client=gen_client
    )
    sent = responses.calls[0].request
    body = json.loads(sent.body)["Argument"]
    assert body["TABLE_TYPE"] == "ULTIMATE_STORY_SHEAR_FORCE_CHECK"
    assert body["LOAD_CASE_NAMES"] == ["Rx(RS)"]


@responses.activate
def test_get_weight_irregularity_table_defaults_to_x(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_weight_irregularity_table(
        table_name="WtIrr(X)",
        unit={"FORCE": "kgf", "DIST": "mm"},
        load_case_names=["DL(ST)"],
        client=gen_client,
    )
    sent = responses.calls[0].request
    body = json.loads(sent.body)["Argument"]
    assert body["TABLE_TYPE"] == "WEIGHT_IRREGULARITY_X"
    assert body["UNIT"] == {"FORCE": "kgf", "DIST": "mm"}


@responses.activate
def test_get_weight_irregularity_table_accepts_y(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/post/TABLE", json={}, status=200)
    story.get_weight_irregularity_table(story.TABLE_TYPE_WEIGHT_IRREGULARITY_Y, "WtIrr(Y)", client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Argument"]["TABLE_TYPE"] == "WEIGHT_IRREGULARITY_Y"
