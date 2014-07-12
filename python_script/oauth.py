from rauth import OAuth1Service
import urllib2, urllib, chardet, MySQLdb
from bs4 import BeautifulSoup

FIRST_ID = 0
last_id = None
ROUND = 0

def get_session():
    '''
      By calling self-defined functions: visit_url(url), get_auth_token(content) and get_pin(authorize_url, authenticity_token), to get the session instance, which can be used to call twitter API.  
    '''
    twitter = OAuth1Service(
        name = "twitter",
        consumer_key = 'EMuscv9fTwLZVdCdaZE2LUybi',
        consumer_secret = '4Vqwy2GzqDFT8wsu2MKkh3QUrbWxor0K4gT0ZqiEUV3BjuRb68',
        request_token_url = 'https://api.twitter.com/oauth/request_token',
        access_token_url = 'https://api.twitter.com/oauth/access_token',
        authorize_url = 'https://api.twitter.com/oauth/authorize',
        base_url = 'https://api.twitter.com/1.1/'
    )
    request_token, request_token_secret = twitter.get_request_token()
    authorize_url = twitter.get_authorize_url(request_token)
    #print 'The url is: ' + authorize_url
    content = visit_url(authorize_url)
    authenticity_token = get_auth_token(content)
    pin = get_pin(authorize_url, authenticity_token)
   # print 'got the pin code: ' + pin
    session = twitter.get_auth_session(request_token, request_token_secret, method = 'POST', data = {'oauth_verifier': pin})
    f = file('tokens.txt', 'w')
    f.write('request_token: ' + request_token)
    f.write('\nrequest_token_secret: ' + request_token_secret)
    f.write('\npincode: ' + pin)
    f.close()
    return session
def visit_url(url):
    '''
        Visit the authorize page, get the content and save it local
    '''
    proxy_handler = urllib2.ProxyHandler({'https': 'http://127.0.0.1:8087'})
    opener = urllib2.build_opener(proxy_handler, urllib2.HTTPSHandler)
    response = opener.open(url)
    content = response.read()
    f = file('authorize.html', 'w')
    f.write(content)
    f.close()
    return content

def get_auth_token(content):
    '''
        Parse the auth token page returned in function visit_url(url) to get the auth token
    '''
    soup = BeautifulSoup(content)
    find = soup.findAll('form', id = 'oauth_form')[0].contents[0].contents[0]
    authenticity_token = find['value']
    #print 'authenticity_token: ' + authenticity_token
    return authenticity_token

def get_pin(url, authenticity_token):
    '''
        Visit the url again, submit username and password, and parse the returned pin page to get the pin code
    '''
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
    return pin

def read(session, screen_name, last_id = None):
    '''
        Read one user's tweets by calling the API
    '''
    params = {
        'screen_name': screen_name,
        'count': 200
    }
    if last_id:
        params['max_id'] = last_id
    r = session.get('statuses/user_timeline.json', verify = False, params = params)
    resp_data = r.json()
    return resp_data

def write2DB(resp_data, i, write_first_tweet = False):
    length = len(resp_data)
    conn = MySQLdb.connect('172.16.20.204', 'root', 'iieneliot', 'weibo', charset='utf8')
    cur = conn.cursor() 
    if resp_data[0]['id_str']:
        #print "type(resp_data[0]): " + str(type(resp_data[0]))
        #print str(resp_data[0]).encode('UTF-8')
        for j, tweet in enumerate(resp_data, 1):
            if not write_first_tweet and j == 0:
                continue
            
            #print 'The ' + str(j + 200 * i) + 'th tweet...'
            id = tweet['id_str'].encode('UTF-8')
            text = tweet['text'].encode('UTF-8')
            created_at = tweet['created_at'].encode('UTF-8')
            user = tweet['user']
            username = user['screen_name'].encode('UTF-8')
            userid = user['id_str'].encode('UTF-8')
            if tweet['geo']:

                geo_coordinates_lon = tweet['geo']['coordinates'][0]
                geo_coordinates_lat = tweet['geo']['coordinates'][1]
            else:
                geo_coordinates_lon = 'null'
                geo_coordinates_lat = 'null'
            if tweet['place']:
                place_name = tweet['place']['full_name'].encode('UTF-8')
            else:
                place_name = 'null'
            if tweet['place']:
                place_country = tweet['place']['country'].encode('UTF-8')
            else:
                place_country = 'null'
            try:
                id = MySQLdb.escape_string(id)
                text = MySQLdb.escape_string(text)
                created_at = MySQLdb.escape_string(created_at)
                username = MySQLdb.escape_string(username)
                userid = MySQLdb.escape_string(userid)
                place_name = MySQLdb.escape_string(place_name)
                place_country = MySQLdb.escape_string(place_country)
                sql = "insert ignore into tweets values('%s', '%s', '%s', '%s', '%s', %s, %s, '%s', '%s')"%(id, text, created_at, username, userid, geo_coordinates_lon, geo_coordinates_lat, place_name, place_country)
                #print "sql: " + sql
                cur.execute(sql)
                #content = ('tweet ID: {0}, tweet text: {1}, created at: {2}, username: {3}, user ID: {4}\n'.format(id, text, created_at, username, userid))
                #f.write(content)
            except UnicodeEncodeError:
                print "Hmmm, we caught a strange code, we will jump the " + str(j + 200 * i) + "th tweet. It's tweet ID is: " + str(id) + ". And the content's charset is: "+ str(chardet.detect(text))
        
            if j == length -1:
                last_id = id
                conn.commit()
                cur.close()
                conn.close()
                return last_id
    else: 
        conn.commit()
        cur.close()
        conn.close()
        return -1

def find_screen_names():
    '''
        Search in MySQL for screen_names whose history data haven't downloaded
    '''
    try:
        conn = MySQLdb.connect('172.16.20.204', 'root', 'iieneliot', 'weibo', charset='utf8')
        cur = conn.cursor() 
        count = cur.execute('select screen_name from blacklist where history_data=0;')
        results = []
        for i in range(count):
            result = cur.fetchone()
            results.append(result[0].encode('UTF-8'))
        
        cur.close()
        conn.close()
        #print "We got " + str(count) + "screen names. They are: " + str(results)
        return results
    except MySQLdb.Error,e:
        print "MySQL Error %d: %s" % (e.args[0], e.args[1])

def set_history_data(screen_name):
    '''
        Called after downloading the history data. Set the flag to 1 so that the history data of the specified screen_names won't be downloaded again.
    '''
    try:
        conn = MySQLdb.connect('172.16.20.204', 'root', 'iieneliot', 'weibo', charset='utf8')
        cur = conn.cursor()
        screen_name = MySQLdb.escape_string(screen_name)
        cur.execute("update blacklist set history_data=1 where screen_name='%s';"%(screen_name))
        conn.commit()
        cur.close()
        conn.close()
        return 1
    except MySQLdb.Error,e:
        print "MySQL Error %d: %s" % (e.args[0], e.args[1])
        return -1

screen_names = find_screen_names()
session = get_session()
for screen_name in screen_names:
    print screen_name
    i = 0
    resp_data = read(session, screen_name)
    try:
        first_id = resp_data[0]['id_str']
        last_id = write2DB(resp_data, i, write_first_tweet = True)
    except IndexError:
        print "This user hasn't tweet! The resp_data is: " + str(resp_data)
        result = set_history_data(screen_name)
        if result == 1:
            print 'Success setting the history_data flag!'
        else:
            print 'Fail to set the history_data flag!'
        continue
    except KeyError:
        print 'KeyError!! The resp_data is: ' + str(resp_data)
    while not last_id == -1:
        i = i + 1
        try:
            resp_data = read(session, screen_name, last_id)
            if first_id == resp_data[0]['id_str']:
                break
            else:
                first_id = resp_data[0]['id_str']
            last_id = write2DB(resp_data, i)
        except KeyError:
            print 'KeyError!! The resp_data is: ' + str(resp_data[0])
        #print 'The last tweet id is: ' + str(last_id)
    result = set_history_data(screen_name)
    if result == 1:
        print 'Success setting the history_data flag!'
    else:
        print 'Fail to set the history_data flag!'
    print screen_name + ': Done'
