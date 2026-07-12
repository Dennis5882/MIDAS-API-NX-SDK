import json

import pytest
import requests
import responses

from midas_nx.client import (
    MidasAPI,
    MidasAuthError,
    MidasClient,
    MidasConnectionError,
    MidasNotFoundError,
    MidasRequestError,
    MidasServerError,
    Product,
    build_base_url,
    configure,
)


def test_build_base_url():
    assert build_base_url(Product.GEN) == "https://moa-engineers.midasit.com:443/gen"
    assert build_base_url("civil") == "https://moa-engineers.midasit.com:443/civil"


def test_client_defaults_base_url_from_product():
    client = MidasClient(mapi_key="k", product=Product.CIVIL)
    assert client.base_url == "https://moa-engineers.midasit.com:443/civil"


def test_client_reads_env_vars(monkeypatch):
    monkeypatch.setenv("MIDAS_MAPI_KEY", "env-key")
    monkeypatch.setenv("MIDAS_BASE_URL", "https://envhost:443/gen")
    client = MidasClient()
    assert client.mapi_key == "env-key"
    assert client.base_url == "https://envhost:443/gen"


@responses.activate
def test_request_sends_correct_url_headers_and_body(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/NODE", json={"NODE": {}}, status=200)

    result = gen_client.request("POST", "/db/NODE", {"Assign": {"1": {"X": 0, "Y": 0, "Z": 0}}})

    assert result == {"NODE": {}}
    sent = responses.calls[0].request
    assert sent.url == "https://x.test:443/gen/db/NODE"
    assert sent.headers["MAPI-Key"] == "test-key"
    assert sent.headers["Content-Type"] == "application/json"
    assert json.loads(sent.body) == {"Assign": {"1": {"X": 0, "Y": 0, "Z": 0}}}


@responses.activate
def test_request_empty_response_body_returns_empty_dict(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/doc/SAVE", body="", status=200)
    assert gen_client.request("POST", "/doc/SAVE", {"Argument": {}}) == {}


@responses.activate
def test_401_raises_auth_error_not_process_exit(gen_client):
    responses.add(
        responses.GET, "https://x.test:443/gen/db/NODE",
        json={"message": "Invalid MAPI-Key"}, status=401,
    )
    with pytest.raises(MidasAuthError) as exc_info:
        gen_client.request("GET", "/db/NODE")
    assert exc_info.value.status_code == 401


@responses.activate
def test_404_raises_not_found_error(gen_client):
    responses.add(responses.GET, "https://x.test:443/gen/db/NODE", json={}, status=404)
    with pytest.raises(MidasNotFoundError):
        gen_client.request("GET", "/db/NODE")


@responses.activate
def test_other_4xx_raises_request_error(gen_client):
    responses.add(responses.POST, "https://x.test:443/gen/db/NODE", json={"message": "bad"}, status=400)
    with pytest.raises(MidasRequestError):
        gen_client.request("POST", "/db/NODE", {})


@responses.activate
def test_5xx_raises_server_error(gen_client):
    responses.add(responses.GET, "https://x.test:443/gen/db/NODE", json={}, status=500)
    with pytest.raises(MidasServerError):
        gen_client.request("GET", "/db/NODE")


@responses.activate
def test_network_failure_raises_connection_error(gen_client):
    responses.add(
        responses.GET, "https://x.test:443/gen/db/NODE",
        body=requests.exceptions.ConnectionError("boom"),
    )
    with pytest.raises(MidasConnectionError):
        gen_client.request("GET", "/db/NODE")


@responses.activate
def test_free_function_delegates_to_configured_default_client():
    configure(mapi_key="configured-key", base_url="https://x.test:443/gen", product=Product.GEN)
    responses.add(responses.POST, "https://x.test:443/gen/doc/NEW", json={}, status=200)

    MidasAPI("POST", "/doc/NEW", {"Argument": {}})

    assert responses.calls[0].request.headers["MAPI-Key"] == "configured-key"


def test_check_product_raises_by_default_when_mismatched(civil_client):
    from midas_nx.client import ProductMismatchError

    with pytest.raises(ProductMismatchError):
        civil_client.check_product(frozenset({"gen"}), "Some Civil-only Resource")


def test_check_product_warns_instead_of_raising_when_not_strict():
    client = MidasClient(mapi_key="k", base_url="https://x.test:443/gen", product=Product.GEN, strict_product=False)
    # Should not raise.
    client.check_product(frozenset({"civil"}), "Some Civil-only Resource")
