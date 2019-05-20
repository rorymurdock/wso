import json
import random
import string
from REST import REST

# Thanks to https://github.com/typicode/jsonplaceholder
# For the demo REST API

rest = REST(url='jsonplaceholder.typicode.com')

print(rest.response_headers('/posts/1'))

# Generate random data for testing
def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def test_rest_get():
    response = rest.get("/posts/1")
    response = json.loads(response.text)
    assert response['userId'] == 1
    assert response['id'] == 1
    assert response['title'] == 'sunt aut facere repellat provident occaecati excepturi optio reprehenderit'
    assert response['body'] == 'quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto'

def test_rest_post():
    test_title = randomString(10)
    test_body = randomString(10)
    test_UserId = 23423

    payload = {}
    payload['title'] = test_title
    payload['body'] = test_body
    payload['userId'] = test_UserId

    response = rest.post("/posts", payload)

    assert response.status_code == 201

    response = json.loads(response.text)
    
    assert response['userId'] == test_UserId
    assert response['id'] == 101
    assert response['title'] == test_title
    assert response['body'] == test_body

def test_rest_put():
    test_title = randomString(10)
    test_body = randomString(10)
    test_UserId = '23423'

    payload = {}
    payload['title'] = test_title
    payload['body'] = test_body
    payload['userId'] = test_UserId

    response = rest.put("/posts/1", payload)
    
    assert response.status_code == 200

    response = json.loads(response.text)
    
    assert response['userId'] == test_UserId
    assert response['id'] == 1
    assert response['title'] == test_title
    assert response['body'] == test_body

def test_rest_delete():
    response = rest.delete('/posts/1')
    assert response.status_code == 200

def test_response_headers():
    response = rest.response_headers('/posts/1')

    assert response['Content-Type'] == 'application/json; charset=utf-8'
    assert response['Connection'] == 'keep-alive'
    assert response['Server'] == 'cloudflare'