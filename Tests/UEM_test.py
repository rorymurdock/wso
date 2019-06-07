"""Performs built tests for the UEM Module"""
from REST import REST
from UEM import UEM

AW = UEM(debug=True)
DEMO_API = REST(url='postman-echo.com')

# HTTP Code tests
def test_expected():
    assert AW.check_http_response(200, 200) is True

def test_unexpected():
    assert AW.check_http_response('unexpected') is False

def test_true_http():
    for code in (200, 201, 204):
        assert AW.check_http_response(DEMO_API.get("/status/%i" % code).status_code) is True

def test_false_http():
    for code in (401, 403, 404, 422):
        assert AW.check_http_response(DEMO_API.get("/status/%i" % code).status_code) is False

# Test sub-functions
def test_json():
    assert isinstance(AW.str_to_json('{"test":"ing"}'), dict) is True
    assert AW.str_to_json('{"test":"ing"}')['test'] == "ing"
    assert AW.str_to_json("string") is None

def test_append_url():
    assert AW.append_url('a', {'b': 'c'}) == 'a?b=c'
    assert AW.append_url('a?b=c', {'d': 'e'}) == 'a?b=c&d=e'

def test_basic_url():
    response = AW.basic_url('/api/system/info')
    assert response[0]['ProductName'] == 'AirWatch Platform Service'
    assert isinstance(response[0], dict) is True
    assert response[1] == 200

    response = AW.basic_url('/api/404')
    assert response[0] is False
    assert response[1] == 404

# UEM API Tests
def test_version():
    """Checks AW Version"""
    assert AW.system_info()['ProductVersion'] == '19.7.0.0'
    print(AW.system_info()['ProductVersion'])

def test_remaining_api_calls():
    """Checks remaining API calls"""
    assert isinstance(AW.remaining_api_calls(), int) is True

def test_get_og():
    """Get AW OG"""
    assert AW.get_og()["LocationGroups"][0]["Name"] == "pytest"
    assert AW.get_og(name="pytest")["LocationGroups"][0]["Name"] == "pytest"
    assert len(AW.get_og(name="notexistantog")['LocationGroups']) == 0