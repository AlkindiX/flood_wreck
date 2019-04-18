import requests
import random
import json
import io
import time
import string
import threading 
import os
from os import urandom 
from os import path
from fake_useragent import UserAgent
import eventlet
import datetime
import argparse

pxlist = []
# To make the output pretty for more than one thread
px_number = 1
px_is_printing = False
def px_flush():
    global px_number
    global px_is_printing
    px_is_printing = True
    for p in pxlist:
        print(p)
        pxlist.clear()
        px_is_printing = False

def px(s: str, count = True):
    global px_number
    global px_is_printing
    if count:
        pxlist.append(str(px_number) + '\t' + s)
        px_number+=1
    else:
        pxlist.append(s)

    rx = random.randrange(0,100)
    if rx > 60:
        if px_is_printing is True:
            return
        px_flush()

class Damingo(object):
    def __init__(self, *arg, **karg):
        self.r = random.Random()
        self.target = karg['target']
        self.tld = karg['tlds']
        self.thds_number = karg['thdnumber']
        self.payload = karg['payload']
        self.method = karg['method']
        self.return_codes = karg['return_codes']
        self.create_output_dir()

        print('[.] Load Data...')
        self.load_data()
        print('[+] Load Data Completed')
        self.kill_switch = False
        self.thds = []
    def load_data(self):
        self.namelist = json.loads(str(io.FileIO(path.join('random-name', 'names.json'), 'r').readall(), encoding='utf8'))
        # TODO: The proxy list need to be changed everytime like proxy updater
        # TODO: Some website require https (most of the time) proxies
        # I tried some of them, but faild :-(
        self.proxies_http = io.FileIO(path.join(os.getcwd(),'proxylist_http.txt')).readlines()
        
        print('-- > [.] Init fake_useragent (may take a while)...')
        self.ua = UserAgent(path=path.join(self.output_location, 'fake_useragent.json'))
        print('-- > [+] fake_useragent completed (cached)')
    def random_tld(self):
        return self.r.choice(self.tld)

    def random_names(self):
        return self.r.choice(self.namelist)
    
    # TODO: Make a behavioral password and email addresses to 
    # fool the scammer that they are real
    def random_password(self):
        return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits * 15) for i in range(self.r.randrange(8,12)))
    
    def random_email_sep(self):
        return self.r.choice(['-', '_'])

    def random_email(self):
        iterations = self.r.randrange(1,5)
        email = ''
        while iterations > 0:
            iterations -= 1
            rx = self.r.randrange(0,100)
            if 0 <= rx <= 90:
                n = self.r.choice(self.namelist).lower()
            elif 90 < rx <= 100:
                n=''
                if email == '':
                    n += self.r.choice(string.ascii_lowercase)
                n += str(self.r.randrange(1980, 2020, 2))
            email += n
            if iterations > 0:
                email += self.random_email_sep()
            
        email += '@'
        email += self.r.choice(tld)
        return email
    
    def create_output_dir(self):
        self.output_location = os.path.join(os.getcwd(), 'output')
        if path.exists(self.output_location) is False:
            os.mkdir(self.output_location)
        self.output_verbose = path.join(self.output_location, datetime.datetime.now().strftime('%m-%d-%Y'))
        if path.exists(self.output_verbose) is False:
            os.mkdir(self.output_verbose)
    
    def process_stream(self, tID):
        work_proxy = ''
        work_proxy_enabled = False
        try:
            while True:
                if self.kill_switch:
                    px('[-] Job %d Finished' % tID, False)
                    return
                website = self.r.choice(self.target)
                if work_proxy_enabled:
                    proxies = {
                        'http': work_proxy
                    }
                else:
                    proxies = {
                        'http': str(self.r.choice(self.proxies_http), encoding='utf8').strip()
                    }
                payload = self.generate_payload()
                # Random User Agent with most
                # used one statistically
                headers = {
                    'User-Agent': self.ua.random,
                }
                # Timeout the post command 
                # if reached n seconds
                # Userful to eliminate thread blocking
                with eventlet.Timeout(10):
                    if self.method == 'post':
                        rp = requests.post(
                            website,
                            data=payload,
                            headers=headers,
                            allow_redirects=False,
                            proxies=proxies
                        )
                    else:
                        rp = requests.get(
                            website,
                            data=payload,
                            headers=headers,
                            allow_redirects=False,
                            proxies=proxies
                        )
                if rp.status_code not in self.return_codes:
                    f = open(path.join(self.output_verbose, 'error_%i_Job%i.html' % (rp.status_code, tID)), 'wb+')
                    f.write(bytes(rp.text, encoding='utf8'))
                    f.close()
                    work_proxy = proxies['http']
                    work_proxy_enabled = True
                    
                px('[' + 'Job ' + str(tID) + '] ' + '[' + website + ']' + '[' + str(rp.status_code) + ']  ' + '[' + str(payload) + ']')   
        except eventlet.timeout.Timeout:
            px('[' + 'Job ' + str(tID) + '] ' + '[' + website + '] Request timeout', False)
            self.process_stream(tID)
            work_proxy_enabled = False
        except Exception as ex:
            px('[' + 'Job ' + str(tID) + '] ' + '[' + website + '] Problem: ' + str(ex)[:20])
            self.process_stream(tID)
            work_proxy_enabled = False
            pass
    def generate_payload(self):
        py = {}
        for p in self.payload:
            if p.find('@email@') > 0:
                pa = p.split('=')
                py[pa[0]] = self.random_email()
            elif p.find('@password@') > 0:
                pa = p.split('=')
                py[pa[0]] = self.random_password()
            elif p.find('@bool_int@') > 0:
                pa = p.split('=')
                py[pa[0]] = self.r.randrange(0,1)
            elif p.find('@bool@') > 0:
                pa = p.split('=')
                py[pa[0]] = self.r.choice([True, False])
            else:
                pa = p.split('=')
                py[pa[0]] = pa[1]
        return py
    def start_thread(self): 
        for c in range(self.thds_number):
            self.thds.append(threading.Thread(target=self.process_stream, args=[c+1]))
        x = 0
        for th in self.thds:
            x += 1
            print('[+] Starting Thread',x)
            th.start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.kill_switch = True

        for x in self.thds:
            if x != None and x.is_alive():
                x.join()

        px_flush()

target = [ 
    'http://sjfj4.me/office.php',
    'http://h84hg.me/office.php'

]

if __name__ == "__main__":
    ag = argparse.ArgumentParser(description='Flood and Wreck python script to bait email demanding scammers')
    ag.add_argument('-t',required=True , metavar='target', help='http target list', nargs='+', type=str)
    ag.add_argument('-p',required=True , metavar='payload', help='Supported paylods are: @password@ and @email@, @bool@ @bool_int@. Example: -p username=@email@ passwd=@password@', nargs='+')
    ag.add_argument('-l', required=False, metavar='tld', help='List some tld, example: google.com', nargs='+')
    ag.add_argument('-j', required=True, metavar='jobs', help='Number of threads to be launched', type=int)
    ag.add_argument('-c', required=True, metavar='method', help='supported methods: get, post')
    ag.add_argument('-r', required=True, metavar='response_code', help='Mark these respnonse as valid and continue so', nargs='+', type=int)
    args = ag.parse_args()
    target = args.t
    payload = args.p
    thds = args.j
    method = args.c
    return_codes = args.r
    if args.l == None:
        tld = ['outlook.com', 'hotmail.com', 'live.com']
    else:
        tld = args.l
    d = Damingo(target=target, payload=payload, tlds=tld, thdnumber=thds, method=method, return_codes=return_codes)
    d.start_thread()