import json

import pytest
import responses

from midas_nx.client import UnsupportedMethodError
from midas_nx.db.properties.damping import GroupDamping
from midas_nx.db.properties.hinge import InelasticHingeControl, InelasticHingeProperty
from midas_nx.db.properties.material import (
    ChangeProperty,
    InelasticFiberMaterialLink,
    InelasticMaterialProperty,
    Material,
    MaterialModifyConcrete,
    PlasticMaterial,
    TimeDependentMaterialCreepShrinkage,
    TimeDependentMaterialFunction,
    TimeDependentMaterialLink,
    TimeDependentMaterialStrength,
)
from midas_nx.db.properties.section import (
    EffectiveWidthScaleFactor,
    ElementStiffnessScaleFactor,
    FiberDivision,
    PlateStiffnessScaleFactor,
    Section,
    SectionReinforcement,
    SectionStiffness,
    SectionStressPoints,
    TaperedGroup,
    VirtualBeam,
    VirtualSection,
)
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


@responses.activate
def test_inelastic_fiber_material_link_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/IMFM", json={}, status=200)
    InelasticFiberMaterialLink.create(
        {1: {"CONC_NAME": "Concrete_KP", "CONFINED_CONC_NAME": "Confined_KP", "REBAR_NAME": "Rebar_Menegotto"}},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["CONC_NAME"] == "Concrete_KP"


@responses.activate
def test_time_dependent_material_function_create_creep_variant(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/TDMF", json={}, status=200)
    TimeDependentMaterialFunction.create(
        {
            1: {
                "NAME": "CreepFunc_1",
                "FTYPE": "CREEP",
                "CTYPE": "CC",
                "SCALE": 1.0,
                "vDAY": [{"DAY": 28, "VALUE": 0.5}, {"DAY": 90, "VALUE": 1.0}],
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["FTYPE"] == "CREEP"


@responses.activate
def test_time_dependent_material_creep_shrinkage_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/TDMT", json={}, status=200)
    TimeDependentMaterialCreepShrinkage.create(
        {1: {"NAME": "KDS2016", "CODE": "KDS2016", "STR": 24000, "HU": 70, "MSIZE": 0.2, "AGE": 28}},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["CODE"] == "KDS2016"


@responses.activate
def test_time_dependent_material_strength_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/TDME", json={}, status=200)
    TimeDependentMaterialStrength.create(
        {1: {"NAME": "TDME_KDS2016", "TYPE": "CODE", "CODENAME": "KDS2016", "STRENGTH": 24000}},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["TYPE"] == "CODE"


@responses.activate
def test_change_property_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/EDMP", json={}, status=200)
    ChangeProperty.create({10: {"TYPE": "NSM", "H_VS": 0.10}}, client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"10": {"TYPE": "NSM", "H_VS": 0.10}}}


@responses.activate
def test_time_dependent_material_link_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/TMAT", json={}, status=200)
    TimeDependentMaterialLink.create({2: {"TDMT_NAME": "KDS2016", "TDME_NAME": "KDS2016"}}, client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"2": {"TDMT_NAME": "KDS2016", "TDME_NAME": "KDS2016"}}}


@responses.activate
def test_plastic_material_create_von_mises_variant(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/EPMT", json={}, status=200)
    PlasticMaterial.create(
        {1: {"NAME": "Steel_VonMises", "MODEL_TYPE": "VM", "VMISES": {"INIT_YIELD_STRESS": 235000}}},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["MODEL_TYPE"] == "VM"


@responses.activate
def test_inelastic_material_property_create_kent_park_variant(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/FIMP", json={}, status=200)
    InelasticMaterialProperty.create(
        {
            3: {
                "NAME": "Conc_Kent&Park",
                "MATL_TYPE": "CONC",
                "HYS_MODEL": "KPM",
                "CONC": {"KENPAR": {"FC": 30000, "EC0": 0.002, "K": 1.0, "ECU": 0.003, "PARTIAL_FACT": 1.0}},
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["3"]["HYS_MODEL"] == "KPM"


@responses.activate
def test_tapered_group_create_poly_variant(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/TSGR", json={}, status=200)
    TaperedGroup.create(
        {2: {"NAME": "PolyGroup", "ELEMLIST": [4, 5, 6], "ZVAR": "POLY", "YVAR": "LINEAR", "ZEXP": 2.0}},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["2"]["ZVAR"] == "POLY"


@responses.activate
def test_section_stiffness_create_keyed_by_element_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/SECF", json={}, status=200)
    SectionStiffness.create(
        {9001: {"ITEMS": [{"ID": 1, "GROUP_NAME": "Creep716", "AREA_SF": 2.61}]}}, client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["9001"]["ITEMS"][0]["AREA_SF"] == 2.61


@responses.activate
def test_section_reinforcement_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/RPSC", json={}, status=200)
    SectionReinforcement.create(
        {
            401: {
                "OPT_MBAR_J": False,
                "OPT_SBAR_J": False,
                "OPT_CRACKED": False,
                "SBAR_ITEMS": [{"OPT_DR": False}, {"OPT_DR": False}],
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["401"]["OPT_CRACKED"] is False


@responses.activate
def test_section_stress_points_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/STRPSSM", json={}, status=200)
    SectionStressPoints.create(
        {
            9003: {
                "OPT_SAME_J": True,
                "POINT_SIZE_1": 2,
                "POINT_SIZE_2": 2,
                "POINT1": [{"PY": 0.00583, "PZ": 0.00476}],
                "POINT2": [{"PY": 0.00583, "PZ": 0.00476}],
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["9003"]["POINT_SIZE_1"] == 2


@responses.activate
def test_plate_stiffness_scale_factor_create_keyed_by_element_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/PSSF", json={}, status=200)
    PlateStiffnessScaleFactor.create(
        {12: {"ITEMS": [{"ID": 1, "GROUP_NAME": "Service", "AXIAL_X": 0.6}]}}, client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["12"]["ITEMS"][0]["AXIAL_X"] == 0.6


@responses.activate
def test_virtual_beam_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/VBEM", json={}, status=200)
    VirtualBeam.create({1: {"VSEC1": 1, "VSEC2": 2}}, client=gen_client)
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"1": {"VSEC1": 1, "VSEC2": 2}}}


@responses.activate
def test_virtual_section_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/VSEC", json={}, status=200)
    VirtualSection.create(
        {
            1: {
                "NAME": "Girder_I_Section",
                "CENT_CALC_TYPE": 0,
                "CEN_PT_X": 0,
                "CEN_PT_Y": 18.0,
                "CEN_PT_Z": 0.934,
                "NORMAL_X": 1,
                "NORMAL_Y": 0,
                "NORMAL_Z": 0,
                "NODE_LIST": [20, 29, 26, 23],
                "ELEM_LIST": [10, 11, 12],
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["NAME"] == "Girder_I_Section"


@responses.activate
def test_effective_width_scale_factor_create_keyed_by_element_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/EWSF", json={}, status=200)
    EffectiveWidthScaleFactor.create(
        {10: {"ITEMS": [{"ID": 1, "LYSCALE": 0.5, "ZTSCALE": 0.6, "ZBSCALE": 0.7, "bJ": False}]}},
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["10"]["ITEMS"][0]["LYSCALE"] == 0.5


@responses.activate
def test_element_stiffness_scale_factor_create_keyed_by_element_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/ESSF", json={}, status=200)
    ElementStiffnessScaleFactor.create(
        {1: {"ITEMS": [{"ID": 1, "AREA_SF": 0.5, "ASY_SF": 0.6}]}}, client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["ITEMS"][0]["AREA_SF"] == 0.5


@responses.activate
def test_fiber_division_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/FIBR", json={}, status=200)
    FiberDivision.create(
        {
            1: {
                "NAME": "Column_Fiber",
                "SECT_KEY": 11001,
                "ASSIGN_TYPE": 0,
                "FIMP_NAME": ["Steel", "Cover Concrete", "Core", "Core", "Core", "Core"],
                "FIBR_BASE": [{"FIBR_BASE_KEY": True}],
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["SECT_KEY"] == 11001


@responses.activate
def test_inelastic_hinge_control_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/IEHC", json={}, status=200)
    InelasticHingeControl.create(
        {
            1: {
                "BEAM_LOC": 1,
                "OPT_ConsiderRebarArea1D": False,
                "FAreaSizeCore": 1,
                "BeamDivNumNy": 15,
                "BeamDivNumNz": 20,
                "FAreaSizeCover": 1,
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["BeamDivNumNy"] == 15


@responses.activate
def test_inelastic_hinge_property_create_keyed_by_element_id(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/IEHG", json={}, status=200)
    InelasticHingeProperty.create(
        {2101: {"PROP_NAME": "Fiber_Auto", "FIBER_NAME": "B2102_Column12"}}, client=gen_client
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body) == {"Assign": {"2101": {"PROP_NAME": "Fiber_Auto", "FIBER_NAME": "B2102_Column12"}}}


@responses.activate
def test_group_damping_create_sends_documented_assign_shape(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/GRDP", json={}, status=200)
    GroupDamping.create(
        {
            1: {
                "bExistStrain": True,
                "OPT_CALC_WHEN_USED": True,
                "STRAIN_GROUP_ITEMS": [{"GROUP_TYPE": "MATERIAL", "GROUP_NAME": "1", "DAMPING_RATIO": 0.05}],
            }
        },
        client=gen_client,
    )
    sent = responses.calls[0].request
    assert json.loads(sent.body)["Assign"]["1"]["STRAIN_GROUP_ITEMS"][0]["DAMPING_RATIO"] == 0.05
