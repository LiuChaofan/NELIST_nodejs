import requests, urllib2, urllib, json, MySQLdb, sys
from requests_oauthlib import OAuth1
from urlparse import parse_qs
from bs4 import BeautifulSoup

consumer_key = 'EMuscv9fTwLZVdCdaZE2LUybi'
consumer_secret = '4Vqwy2GzqDFT8wsu2MKkh3QUrbWxor0K4gT0ZqiEUV3BjuRb68'

def visit_url(url):
    proxy_handler = urllib2.ProxyHandler({'https': 'http://127.0.0.1:8087'})
    opener = urllib2.build_opener(proxy_handler, urllib2.HTTPSHandler)
    response = opener.open(url)
    content = response.read()
    soup = BeautifulSoup(content)
    find = soup.findAll('form', id = 'oauth_form')[0].contents[0].contents[0]
    authenticity_token = find['value']
    print 'authenticity_token:' + authenticity_token
    return authenticity_token

def get_pin(url, authenticity_token):
    print 'The url is: ' + url
    para = {
        'authenticity_token': authenticity_token,
        'session[username_or_email]': 'liu_chaofan',
        'session[password]': 'jianqiang'
    }
    data = urllib.urlencode(para)
    proxy_handler = urllib2.ProxyHandler({'https': 'http://127.0.0.1:8087'})
    req = urllib2.Request(url, data)
    opener = urllib2.build_opener(proxy_handler, urllib2.HTTPSHandler)
    response = opener.open(req)
    content = response.read()
    soup = BeautifulSoup(content)
    pin = soup.findAll('div', id = 'oauth_pin')[0].p.kbd.code.contents[0]
    print 'got pin code: ' + str(pin)
    return pin

def REST_friends(oauth, screen_name, cursor = None):
    print 'Calling the REST friends API'
    params = {'count': 200, 'skip_status': 1}
    params['screen_name'] = screen_name
    if cursor:
        params['cursor'] = cursor
    proxies = {'https': 'http://127.0.0.1:8087'}
    r = requests.get('https://api.twitter.com/1.1/friends/list.json', params = params, auth = oauth, proxies = proxies, verify = False)
    print 'status code: ' + str(r.status_code)
    if not r.status_code == 200:
        print 'Got an error, test: ' + r.text
        return {'next_cursor': 0}
    else:
        print 'Success!'
        result = r.json()
        return result

def write2db(result):
    try:
        conn = MySQLdb.connect('172.16.20.204', 'root', 'iieneliot', 'weibo', charset = 'utf8')
        cur = conn.cursor()
        for user in result['users']:
            screen_name = user['screen_name'].encode('UTF-8')
            uid = user['id_str'].encode('UTF-8')
            sql = "insert ignore into blacklist values('%s', '%s', '%s', '%s')"%(screen_name, uid, '0', '0')
            cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "MySQL Error %d: %s" % (e.args[0], e.args[1])


oauth = OAuth1(consumer_key, consumer_secret)
proxies = {'https': 'http://127.0.0.1:8087'}
r = requests.post(
    url = 'https://api.twitter.com/oauth/request_token',
    proxies = proxies,
    auth = oauth, verify = False)
credentials = parse_qs(r.content)
request_key = credentials.get('oauth_token')[0]
request_secret = credentials.get('oauth_token_secret')[0]

authorize_url = 'https://api.twitter.com/oauth/authorize?oauth_token=%s'%request_key
authenticity_token = visit_url(authorize_url)
verifier = get_pin(authorize_url, authenticity_token)

oauth = OAuth1(
    consumer_key,
    consumer_secret,
    request_key,
    request_secret,
    verifier = verifier
)
r = requests.post(url = 'https://api.twitter.com/oauth/access_token', auth = oauth, proxies = proxies, verify = False)
credentials = parse_qs(r.content)
access_token_key = credentials.get('oauth_token')[0]
access_token_secret = credentials.get('oauth_token_secret')[0]
oauth = OAuth1(consumer_key, consumer_secret, access_token_key, access_token_secret)
#f = file('friends.txt', 'w') #used for debug
screen_name = sys.argv[1]
result = REST_friends(oauth, screen_name)
write2db(result)
#for user in result['users']:
    #f.write(user['screen_name'] + '\n')
cursor = result['next_cursor']
while not cursor == 0:
    result = REST_friends(oauth, screen_name, cursor = cursor)
    print result['next_cursor']
    cursor = result['next_cursor']
    if cursor == 0:
        break
    write2db(result)
    #for user in result['users']:
        #f.write(user['screen_name'] + '\n')

print 'Done.'
