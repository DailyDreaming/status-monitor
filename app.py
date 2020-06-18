import requests
import json
import time
import threading

from flask import Flask, render_template
from time import gmtime, strftime


refresh_interval = 1.0
filename = 'endpoints.json'

app = Flask(__name__)
with open(filename, 'r') as f:
    endpoints = json.load(f)

flat_list_of_urls = []
for group, urls in endpoints.items():
    flat_list_of_urls += urls

statuses = {}


class LoopStatus:
    def __init__(self, time_to_sleep):
        self.lock = threading.Lock()
        self.tts = time_to_sleep
        self.go_on = True

    def check_url(self, url):
        try:
            return str(requests.get(url, timeout=2).status_code)
        except:
            return '500'

    def update_status(self, urls):
        global statuses
        for url in urls:
            statuses[url] = self.check_url(url)
        print(statuses)

    def loop(self):
        while self.go_on:
            time.sleep(self.tts)
            with self.lock:
                self.update_status(flat_list_of_urls)

    def exit(self):
        self.go_on = False


looper = LoopStatus(refresh_interval)


def lock_acquire(func):
    def __inner__(*args):
        with looper.lock:
            res = func(*args)
        return res
    return __inner__


@app.route('/')
@lock_acquire
def main_page():
    return render_template(
        'index.html',
        returned_statuses=statuses,
        checkurls=endpoints,
        last_update_time=strftime("%Y-%m-%d %H:%M:%S", gmtime())
    )


if __name__ == "__main__":
    t = threading.Thread(target=looper.loop, name="looper")
    t.start()
    app.run(host="localhost", debug=1, use_reloader=False)
    looper.exit()
