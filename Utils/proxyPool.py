import random, requests, queue, signal
from threading import Thread

proxy_list = []
requests.adapters.DEFAULT_RETRIES = 5
q = queue.Queue()
is_exit = False

def get_list():
    with open('proxyList.txt', 'r') as f:
        text = f.read()
        for proxy in text.split('\n'):
            proxy = proxy.split('@')[0].strip()
            if proxy != '':
                q.put(proxy)

def add_proxy():
    while not q.empty() and not is_exit:
        proxy = q.get()
        valid = validate(proxy)
        print('{0} validation {1}'.format(proxy, valid))
        if valid:
            proxy_list.append(proxy)

def validate(proxy):
    proxies = {"http": "http://{}".format(proxy), "https": "https://{}".format(proxy)}
    try:
        r = requests.get('https://maoyan.com/', proxies=proxies, timeout=10)
        if r.status_code == 200:
            return True
    except Exception as e:
        pass
    return False

def get_proxy():
    index = random.randint(0, len(proxy_list) - 1)
    return proxy_list[index]

def handler(signum, frame):
    global is_exit
    is_exit = True
    print("receive a signal %d, is_exit = %d".format(signum, is_exit))

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)
get_list()
thread_list = []
for i in range(0, 20):
    t = Thread(target=add_proxy)
    thread_list.append(t)
    t.setDaemon(True)
    t.start()

while True:
    alive = False
    for thread in thread_list:
        alive = alive or thread.isAlive()
    if not alive:
        break

print(len(proxy_list))
if len(proxy_list) == 0:
    raise Exception

