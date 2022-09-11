import requests, time, random, itertools, threading, json

with open('proxies.txt', 'r', encoding='utf-8') as proxyfile:
    proxies = itertools.cycle(proxyfile.readlines())

with open('config.json', 'r+', encoding='utf-8') as configfile:
    config = json.load(configfile)

pkeys = requests.get('https://apis.roblox.com/captcha/v1/metadata').json()['funCaptchaPublicKeys']

def grandom(rtype):
    return f'{config["prefix"]}{random.randint(100000,999999)}' if rtype == 'password' else f"{config['prefix']}{''.join((random.choice('abcdxyzpqrABCDXYZPQR') for i in range(8)))}"

def csrf(proxy, cookie=None):
    proxysplit = proxy.split(':')
    proxies = {
        'https': f'http://{proxysplit[2]}:{proxysplit[3]}@{proxysplit[0]}:{proxysplit[1]}'
    }
    return requests.post("https://auth.roblox.com/v2/logout", proxies=proxies, cookies={".ROBLOSECURITY": cookie}).headers["x-csrf-token"] if cookie else requests.post('https://catalog.roblox.com/v1/catalog/items/details', proxies=proxies).headers['x-csrf-token']

def registerinfo(proxy):
    proxysplit = proxy.split(':')
    proxies = {
        'https': f'http://{proxysplit[2]}:{proxysplit[3]}@{proxysplit[0]}:{proxysplit[1]}'
    }
    cdetails = requests.post("https://auth.roblox.com/v2/signup", proxies=proxies, headers={"x-csrf-token":csrf(proxy), "User-Agent":"Mozilla/5.0 (Windows; U; Windows CE) AppleWebKit/534.47.7 (KHTML, like Gecko) Version/4.1 Safari/534.47.7"}, json={"username":"fsdhfkshdfk123","password":"WE*@*!&EUAHUISFHS","birthday":"1962-04-08T23:00:00.000Z","gender":2,"isTosAgreementBoxChecked":True,"agreementIds":["848d8d8f-0e33-4176-bcd9-aa4e22ae7905","54d8a8f0-d9c8-4cf3-bd26-0cbf8af0bba3"]})
    if cdetails.status_code != 429:
        return cdetails.json()["errors"][0]["fieldData"].split(",")[0], cdetails.json()["errors"][0]["fieldData"].split(",")[1]
    else:
        print('too many requested on registerinfo, retrying.')
        time.sleep(1); return registerinfo(proxy)

def solve(blob, pkey):
    solvej = {
      "key": config['key'],
      "task": {
          "type": "FunCaptchaTaskProxyless",
          "site_url": "https://www.roblox.com/",
          "public_key": pkey,
          "service_url": "https://roblox-api.arkoselabs.com/",
          "blob": blob
      }
    }
    create = requests.post('https://captcha.rip/api/create', json=solvej)
    if not "id" in create.text:
        print("error", create.text)
        return False
    checkj = {
        'key': config['key'],
        'id': create.json()['id']
    }
    fetch = requests.post('https://captcha.rip/api/fetch', json=checkj)
    while fetch.json()['message'] == 'Processing':
        time.sleep(1)
        fetch = requests.post('https://captcha.rip/api/fetch', json=checkj)
    if fetch.json()['message'] == 'Solved':
        print(f'solved! {fetch.text}')
        return fetch.json()['token']
    else:
        print(f'failed {fetch.text}')
        return False

def register(cid, token, proxy):
    username = grandom('username')
    password = grandom('password')
    proxysplit = proxy.split(':')
    registerj = {
        'agreementIds': ["848d8d8f-0e33-4176-bcd9-aa4e22ae7905", "54d8a8f0-d9c8-4cf3-bd26-0cbf8af0bba3"],
        'birthday': "1996-04-05T08:00:00.000Z",
        'captchaId': cid,
        'captchaToken': token, 
        'gender': 1,
        'isTosAgreementBoxChecked': True,
        'username': username,
        'password': password
    }
    proxies = {
        'https': f'http://{proxysplit[2]}:{proxysplit[3]}@{proxysplit[0]}:{proxysplit[1]}'
    }
    attemptregister = requests.post('https://auth.roblox.com/v2/signup', headers={'x-csrf-token': csrf(proxy)}, json=registerj, proxies=proxies)
    if attemptregister.status_code == 200:
        print(f'successfully registered {username}:{password} on {proxy}')
        with open('cookies.txt', 'a+') as cookiesfile:
            cookiesfile.write(f'{username}:{password}:{attemptregister.cookies[".ROBLOSECURITY"]}\n')
        with open('formatted.txt', 'a+') as formattedfile:
            formattedfile.write(f'{username}:{password}:{proxy}:{attemptregister.cookies[".ROBLOSECURITY"]}\n')
    elif attemptregister.status_code == 429:
        print('too many requests when registering, retrying.')
        time.sleep(3)
        cid, blob = registerinfo(proxy)
        return register(cid, solve(blob), proxy)
    else:
        print(attemptregister.text, attemptregister.status_code)

def main():
    while True:
        proxy = next(proxies).strip()
        cid, blob = registerinfo(proxy)
        solved = solve(blob, pkeys['ACTION_TYPE_WEB_SIGNUP'])
        if solved:
            register(cid, solved, proxy)

for _ in range(config['threads']):
    threading.Thread(target=main).start()
