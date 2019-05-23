import json
import random
import string
from REST import REST

# Thanks to https://postman-echo.com
# For the demo REST API

rest = REST(url='postman-echo.com')

# Generate random data for testing
def randomString(stringLength=15):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def test_rest_get():
    test_param1 = randomString()
    test_param1_value = randomString()
    test_param2 = randomString()
    test_param2_value = randomString()

    response = rest.get("/get?%s=%s&%s=%s" % (
        test_param1, 
        test_param1_value, 
        test_param2, 
        test_param2_value))
    
    assert response.status_code == 200

    response = json.loads(response.text)['args']
    
    assert response[test_param1] == test_param1_value
    assert response[test_param2] == test_param2_value

def test_rest_post():
    test_title = randomString()
    test_body = randomString()
    test_UserId = randomString()

    payload = {}
    payload['title'] = test_title
    payload['body'] = test_body
    payload['userId'] = test_UserId

    response = rest.post("/post", payload)

    assert response.status_code == 200

    response = json.loads(response.text)['data']
    
    assert response['userId'] == test_UserId
    assert response['title'] == test_title
    assert response['body'] == test_body

def test_rest_put():
    test_title = randomString()
    test_body = randomString()
    test_UserId = randomString()

    payload = {}
    payload['title'] = test_title
    payload['body'] = test_body
    payload['userId'] = test_UserId

    response = rest.put("/put", payload)

    assert response.status_code == 200

    response = json.loads(response.text)['form']

    print(response)
    
    assert response['userId'] == test_UserId
    assert response['title'] == test_title
    assert response['body'] == test_body

def test_rest_delete():
    response = rest.delete('/delete')
    assert response.status_code == 200

def test_response_headers():
    response = rest.response_headers('/get')

    assert response['Content-Type'] == 'application/json; charset=utf-8'
    assert response['Connection'] == 'keep-alive'
    assert response['Server'] == 'nginx'

def test_custom_header():
    header_content = randomString()
    header_key = randomString()

    headers = {header_key: header_content}

    rest = REST(url='postman-echo.com', headers=headers, debug=True)

    response = json.loads(rest.get('/headers').text)

    assert response['headers'][header_key] == header_content
