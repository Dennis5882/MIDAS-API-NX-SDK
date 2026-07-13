"""Source: docs/manual/09_DB_Dynamic_Loads.md, items 1-12.

Unlike most Hyper-S "-M1" variants elsewhere in the manual (documented as
thin stubs), THGC-M1/THOO-M1/THIS-M1 here have full Specifications tables —
implemented, with deeply-nested control sub-objects left as Any (matching
the SECT_I precedent) given their size.
"""
from __future__ import annotations

from typing import Any, List, TypedDict

from .base import DbResource, GET_PUT_DELETE_METHODS


class ResponseSpectrumFunctionValue(TypedDict, total=False):
    PERIOD: float  # Period (sec), required
    VALUE: float  # required


class ResponseSpectrumFunctionPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #1 — /db/SPFC Specifications table.

    Deeply conditional on the design-code discriminator (User-defined vs.
    Korea/US/Eurocode/China/... code variants, each with its own extra
    keys) — only the common envelope + the User-defined "aFUNC" shape are
    typed for v1; code-specific extra keys go as extra dict keys.
    """

    NAME: str  # Response Spectrum Function Name, required
    iTYPE: int  # 1=Normalized Accel, 2=Accel, 3=Velocity, 4=Displacement; required
    iMETHOD: int  # 0=Scale Factor, 1=Max Value; default 0, optional
    SCALE: float  # Scale Value, required
    GRAV: float  # Gravitational Acceleration (iTYPE=1 only), required
    DRATIO: float  # Damping Ratio, default 0.05, optional
    DESC: str  # default "", optional
    aFUNC: List[ResponseSpectrumFunctionValue]  # User-defined function data, required for user-defined


class ResponseSpectrumFunction(DbResource):
    ENDPOINT = "/db/SPFC"
    NAME = "Response Spectrum Functions"
    PRODUCTS = frozenset({"gen", "civil"})


class ResponseSpectrumUseMode(TypedDict, total=False):
    bUSE: bool  # Mode use flag, optional
    MSFACTOR: float  # Mode shape factor, optional


class ResponseSpectrumLoadCasePayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #2 — /db/SPLC Specifications table."""

    NAME: str  # Load Case Name, required
    DESC: str  # default "", optional
    DIR: str  # "XY" / "Z", default "XY", optional
    ANGLE: float  # Excitation Angle, default 0, optional
    SCALE: float  # Scale Coefficient, required
    PMFT: float  # Period Modification Factor, required
    aFUNCNAME: List[str]  # Spectrum Function Name list (/db/SPFC names), required
    INTERP: str  # "LINEAR" / "LOG", default "LINEAR", optional
    COMTYPE: str  # "SRSS"/"CQC"/"ABS"/"Linear", default "CQC", optional
    bADDSIGN: bool  # Add Sign to Results, default false, optional
    iSIGNTYPE: int  # 0=Principal Mode, 1=Absolute Max; default 1, optional
    bMODE: bool  # Mode Shape Selection, optional
    aUSEMODE: List[ResponseSpectrumUseMode]  # optional
    bDAMP: bool  # Apply Damping Method, default false, optional
    bCDAMP: bool  # Damping Ratio Correction, default false, optional
    iMDTYPE: int  # 1=Modal, 2=M&S, 3=StrainEnergy; required if bDAMP=true


class ResponseSpectrumLoadCase(DbResource):
    ENDPOINT = "/db/SPLC"
    NAME = "Response Spectrum Load Cases"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeHistoryInitialLoadItem(TypedDict, total=False):
    SLC: str  # Static Load Case Name, required
    SF: float  # Scale Factor, required
    LCT: int  # Load Case Type: Static=1, Construction=18; required


class TimeHistoryGlobalControlPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #3 — /db/THGC Specifications table. CIVIL NX only."""

    GNT: int  # Geometric Nonlinearity Type: None=0, Large Displacement=1, P-Delta=2; required
    ILT: int  # Initial Load Type: Nonlinear static=0, Static/construction stage import=1; default 0, required
    aILL: List[TimeHistoryInitialLoadItem]  # Initial Load List, default [], optional
    IEPI: bool  # Ignore NL Initial Load Element Option, default true, optional
    NSTEP: int  # Number of Increment Steps, default 1, optional
    bROT: bool  # Output Method: false=final step only, true=step increment; default false, optional
    SNIO: int  # Output Step Increment Count, default 1, optional
    bPCF: bool  # Allow Convergence Failure, default true, required
    MAXNS: int  # Maximum Number of Substeps, default 10, required
    MAXIT: int  # Maximum Iteration Count, default 10, required
    bDN: bool  # Use Displacement Norm, default true, optional
    bFN: bool  # Use Force Norm, default false, optional
    bEN: bool  # Use Energy Norm, default false, optional
    DN: float  # Displacement Norm Value, default 0.001, optional
    FN: float  # Force Norm Value, default 0, optional
    EN: float  # Energy Norm Value, default 0, optional
    bULSM: bool  # Apply Line Search Method, default false, optional
    ULSM: int  # Line Search Starting Iteration Count, default 5, optional
    ENERGYRESULT: bool  # Output Time-History Energy Results, default true, optional
    SDVI: bool  # Viscous/Oil Damper Results, default true, optional
    SDVE: bool  # Viscoelastic Damper Results, default true, optional
    SDST: bool  # Steel Damper Results, default true, optional
    SDHY: bool  # Hysteretic Isolation Device Results, default true, optional
    SDIS: bool  # Isolation Device Results, default true, optional
    bMSSSTATUS: bool  # Model Yield Status, default true, optional


class TimeHistoryGlobalControl(DbResource):
    ENDPOINT = "/db/THGC"
    NAME = "Time History Global Control"
    PRODUCTS = frozenset({"civil"})


class TimeHistoryGlobalControlHyperSPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #4 — /db/THGC-M1 Specifications table
    (Hyper-S). Nested INCREMENT_STEP/ITER_PARAM/HINGE_OPT sub-objects are left
    as Any given their size — see the manual for their full shape.
    """

    GEO_NONL_TYPE: int  # None=0, Large Disp=1, P-Delta=2; required
    INIT_LOAD_TYPE: int  # Nonlinear static=0, Retrieve static/construction stage results=1; required
    INIT_LOAD_LIST: Any  # [{"LC_NAME","SF","LC_TYPE"}, ...], optional
    INCREMENT_STEP: Any  # {"NSTEP","OUT_TYPE","STEP_INC"}, optional
    ITER_PARAM: Any  # {"PERMIT_FAIL","MAX_ITER","NORM_CTRL",...}, required
    IGNORE_ELEM: bool  # Ignore NL Initial Load Elements, default false, optional
    SEQ_LOAD_TYPE: int  # Undeformed=0, Deformed=1; default 1, optional
    HINGE_OPT: Any  # {"PSPRING_SUP","EL"}, optional


class TimeHistoryGlobalControlHyperS(DbResource):
    ENDPOINT = "/db/THGC-M1"
    NAME = "Time History Global Control (Hyper-S)"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = GET_PUT_DELETE_METHODS


class TimeHistoryOutputOptionHyperSPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #5 — /db/THOO-M1 Specifications table (Hyper-S)."""

    OUT_OPT: Any  # {"HINGE_OUT","COMMON_OPT","FIBER_OUT"}, required
    RESULT_SELECTION: Any  # {"ENERGY_RESULT","SDVI","SDVE","SDST","SDHY","SDIS"}, required


class TimeHistoryOutputOptionHyperS(DbResource):
    ENDPOINT = "/db/THOO-M1"
    NAME = "Time History Output Option (Hyper-S)"
    PRODUCTS = frozenset({"gen", "civil"})
    METHODS = GET_PUT_DELETE_METHODS


class TimeHistoryLoadCaseCommon(TypedDict, total=False):
    """The /db/THIS "COMMON" sub-object."""

    NAME: str  # Load Case Name, required
    DESC: str  # default "", optional
    iATYPE: int  # Analysis Type: Linear=1, Nonlinear=2; required
    iAMETHOD: int  # Analysis Method: Modal=1, Direct=2, Static=3; required
    iTHTYPE: int  # Time History Type: Transient=1, Periodic=2; required
    ENDTIME: float  # End Time (sec), required
    INC: float  # Time Increment, required
    iOUT: int  # Output Step Increment, required
    INITMETHOD: str  # "INIT" / "ORDER", required
    iMDTYPE: int  # Damping Method: Modal=1, M&S=2, StrainEnergy=3; required


class TimeHistoryLoadCasePayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #6 — /db/THIS Specifications table.

    Deeply conditional on COMMON.iATYPE x COMMON.iAMETHOD (Linear/Nonlinear
    x Modal/Direct Integration/Static) — only the COMMON envelope is typed
    for v1; variant-specific keys (e.g. DALL for modal damping, iNMM for
    Newmark integration, bITER for nonlinear iteration) go as extra dict
    keys alongside COMMON.
    """

    COMMON: TimeHistoryLoadCaseCommon  # required


class TimeHistoryLoadCase(DbResource):
    ENDPOINT = "/db/THIS"
    NAME = "Time History Load Cases"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeHistoryLoadCaseHyperSPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #7 — /db/THIS-M1 Specifications table
    (Hyper-S). ANAL_CASE/DAMPING/NONL_CTRL_PARAM sub-objects are left as Any
    given their size — see the manual for their full shape.
    """

    NAME: str  # required
    DESC: str  # optional
    ANAL_CASE: Any  # {"ANAL_TYPE","ANAL_METHOD","TH_TYPE"}, required
    ENDTIME: float  # required
    TIME_INC: float  # required
    OUTPUT_STEP: int  # required
    INIT_METHOD: str  # "INIT" / "ORDER", required
    USE_INIT_LOAD: bool  # required
    CUM_DVA: bool  # Cumulative Displacement/Velocity/Acceleration, optional
    KEEP_LOAD: bool  # Maintain final-step load state, optional
    KEEP_ACC: bool  # Maintain final-step acceleration, optional
    DAMPING: Any  # {"DAMPING_METHOD","ALL_DAMPING_RATIO","MODAL_DAMPING_RATIO"}, required
    NONL_CTRL_PARAM: Any  # {"PERFORM_ITER","ITER_CTRL":{...}}, required for iATYPE=Nonlinear


class TimeHistoryLoadCaseHyperS(DbResource):
    ENDPOINT = "/db/THIS-M1"
    NAME = "Time History Load Cases (Hyper-S)"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeHistoryFunctionValue(TypedDict, total=False):
    TIME: float  # required
    VALUE: float  # required


class TimeHistoryFunctionPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #8 — /db/THFC Specifications table.

    FUNCTYPE=1 (Time Function) uses iMETHOD/SCALE/MAXVALUE/aFUNCDATA;
    FUNCTYPE=2 (Sinusoidal) uses CONS_A/CONS_C/FREQUENCY/DAMP_FACTOR/PHASE_ANGLE.
    """

    NAME: str  # required
    DESC: str  # default "", optional
    iTYPE: int  # 1=Normalized Accel, 2=Accel, 3=Force, 4=Moment, 5=Normal; required
    GRAV: float  # required
    FUNCTYPE: int  # 1=Time Function, 2=Sinusoidal; required
    # FUNCTYPE=1 only
    iMETHOD: int  # 0=Scale Factor, 1=Max Value; required
    SCALE: float  # required if iMETHOD=0
    MAXVALUE: float  # default 0, optional, used if iMETHOD=1
    aFUNCDATA: List[TimeHistoryFunctionValue]  # required
    # FUNCTYPE=2 only
    CONS_A: float  # Constant A, required
    CONS_C: float  # Constant C, required
    FREQUENCY: float  # required
    DAMP_FACTOR: float  # required
    PHASE_ANGLE: float  # required


class TimeHistoryFunction(DbResource):
    ENDPOINT = "/db/THFC"
    NAME = "Time History Functions"
    PRODUCTS = frozenset({"gen", "civil"})


class GroundAccelerationPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #9 — /db/THGA Specifications table."""

    NAME: str  # Time History Load Case Name, required
    ANGLE: float  # Horizontal Ground Acceleration Angle, default 0, optional
    FUNCX: str  # X-direction Function Name (/db/THFC name), required
    SCALEX: float  # required
    ATIMEX: float  # default 0, optional
    FUNCY: str  # required
    SCALEY: float  # required
    ATIMEY: float  # default 0, optional
    FUNCZ: str  # required
    SCALEZ: float  # required
    ATIMEZ: float  # default 0, optional


class GroundAcceleration(DbResource):
    ENDPOINT = "/db/THGA"
    NAME = "Ground Acceleration"
    PRODUCTS = frozenset({"gen", "civil"})


class DynamicNodalLoadItem(TypedDict, total=False):
    """One entry of the /db/THNL "ITEMS" array. No GROUP_NAME here (unlike
    most "ITEMS" entries) — the manual's fields are ID/THLCNAME/FUNC_NAME/
    DIR/ARRIVAL_TIME/SCALE_FACTOR only."""

    ID: int  # Serial Number, default 0, optional
    THLCNAME: str  # Time History Load Case Name, required
    FUNC_NAME: str  # Time History Function Name (Force/Moment types only), required
    DIR: str  # "X" / "Y" / "Z", required
    ARRIVAL_TIME: float  # required
    SCALE_FACTOR: float  # required


class DynamicNodalLoadPayload(TypedDict):
    """docs/manual/09_DB_Dynamic_Loads.md #10 — /db/THNL. Keyed by node id."""

    ITEMS: List[DynamicNodalLoadItem]


class DynamicNodalLoad(DbResource):
    ENDPOINT = "/db/THNL"
    NAME = "Dynamic Nodal Loads"
    PRODUCTS = frozenset({"gen", "civil"})


class TimeVaryingStaticLoadPayload(TypedDict, total=False):
    """docs/manual/09_DB_Dynamic_Loads.md #11 — /db/THSL Specifications table."""

    THIS_LCNAME: str  # Time History Load Case Name (/db/THIS name), required
    SLOAD: str  # Static Load Case Name (/db/STLD name), required
    THIS_FUNCNAME: str  # Time History Function Name (Normal type only), required
    ATIME: float  # Arrival Time, default 0, optional
    SCALE: float  # required


class TimeVaryingStaticLoad(DbResource):
    ENDPOINT = "/db/THSL"
    NAME = "Time Varying Static Loads"
    PRODUCTS = frozenset({"gen", "civil"})


class MultipleSupportExcitationItem(TypedDict, total=False):
    """One entry of the /db/THMS "ITEMS" array. No GROUP_NAME here (unlike
    most "ITEMS" entries) — the manual's fields are ID/LCNAME/ANGLE/FUNCX...
    /ATIMEZ only."""

    ID: int  # Serial Number, default 0, optional
    LCNAME: str  # Time History Load Case Name, required
    ANGLE: float  # Horizontal Ground Acceleration Angle, default 0, optional
    FUNCX: str  # X-direction Function Name (NormAccel/Acceleration types only), required
    SCALEX: float  # required
    ATIMEX: float  # default 0, optional
    FUNCY: str  # optional
    SCALEY: float  # optional
    ATIMEY: float  # default 0, optional
    FUNCZ: str  # optional
    SCALEZ: float  # optional
    ATIMEZ: float  # default 0, optional


class MultipleSupportExcitationPayload(TypedDict):
    """docs/manual/09_DB_Dynamic_Loads.md #12 — /db/THMS. Keyed by node/group id."""

    ITEMS: List[MultipleSupportExcitationItem]


class MultipleSupportExcitation(DbResource):
    ENDPOINT = "/db/THMS"
    NAME = "Multiple Support Excitation"
    PRODUCTS = frozenset({"gen", "civil"})
