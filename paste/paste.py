import json
import time
import http.client

from paste import config


def get(alias):
    # connect to API
    if config.store_https:
        conn = http.client.HTTPSConnection(config.store)
    else:
        conn = http.client.HTTPConnection(config.store)

    # request given alias
    conn.request('GET', config.store_endpoint + 'store/paste/' + alias)

    # get response
    response = conn.getresponse()

    # check for 404
    if response.status == 404:
        raise KeyError()

    # get metadata
    name = response.getheader('Content-Filename')
    date = response.getheader('Last-Modified')
    expire = response.getheader('Expires')
    language = response.getheader('Content-Type')

    # store the code
    code = response.read().decode('utf-8')

    return name, date, expire, language, code


def put(alias, name, language, code):
    if isinstance(code, str):
        code = code.encode('utf-8')

    # connect to API
    if config.store_https:
        conn = http.client.HTTPSConnection(config.store)
    else:
        conn = http.client.HTTPConnection(config.store)

    # request given alias
    conn.request('HEAD', config.store_endpoint + 'store/paste/' + alias)

    # get response
    response = conn.getresponse()
    response.read()

    # check for existing alias
    if response.status == 200:
        raise KeyError()
    elif response.status == 400:
        raise NameError()
    elif response.status != 404:
        raise ValueError()

    # determine if this is a put or a post
    if alias:
        method = 'PUT'
    else:
        method = 'POST'

    # make a metadata request
    conn.request(method, config.store_endpoint + 'api/paste/' + alias, headers={'Content-Type': 'application/json'}, body=json.dumps({'filename': name, 'size': len(code), 'type': language, 'expire': time.time() + config.interval, 'locked': True}).encode('utf-8'))

    # get response
    response = conn.getresponse()

    # load data response
    data = json.loads(response.read().decode('utf-8'))

    # note bad requests
    if response.status != 201:
        raise ValueError()

    # make a data request
    conn.request('PUT', config.store_endpoint + 'store/paste/' + data['alias'], body=code)

    # get response
    response = conn.getresponse()
    response.read()

    # note bad requests
    if response.status != 204:
        raise KeyError()

    return data['alias']
