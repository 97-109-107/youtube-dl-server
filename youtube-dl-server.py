import json
import os
import subprocess
from queue import Queue
from bottle import route, run, Bottle, request, static_file, auth_basic
from threading import Thread

app = Bottle()
user = os.environ['YTDL_USER']
password = os.environ['YTDL_PASS']
path = os.environ['YTDL_PATH'].rstrip('//')
port = os.getenv('YTDL_PORT', 8080)

def check(u, p):
    if (u == user) and (p == password):
        return True
    else:
        return False


@app.route('/ytdl')
@auth_basic(check)
def dl_queue_list():
    return static_file('index.html', root='./')


@app.route('/ytdl/static/:filename#.*#')
@auth_basic(check)
def server_static(filename):
    return static_file(filename, root='static/')

@app.route('/ytdl/q', method='GET')
@auth_basic(check)
def q_size():
    return { "success" : True, "size" : json.dumps(list(dl_q.queue)) }

@app.route('/ytdl/q', method='POST')
@auth_basic(check)
def q_put():
    url = request.forms.get( "url" )
    if "" != url:
        dl_q.put( url )
        print("Added url " + url + " to the download queue")
        return { "success" : True, "url" : url }
    else:
        return { "success" : False, "error" : "dl called without a url" }

def dl_worker():
    while not done:
        item = dl_q.get()
        download(item)
        dl_q.task_done()

def download(url):
    print("Starting download of " + url)
    command = 'youtube-dl -o "' + path + '/.incomplete/%(title)s.%(ext)s" -f best[acodec=none][ext=mp4]+best[vcodec=none][ext=m4a] --exec \'touch {} && mv {} ' + path + '\' --merge-output-format mp4 ' + url
    subprocess.call(command, shell=True)
    print("Finished downloading " + url)

dl_q = Queue();
done = False;
dl_thread = Thread(target=dl_worker)
dl_thread.start()

print("Started download thread")

app.run(host='0.0.0.0', port=port, debug=True)
done = True
dl_thread.join()
