import sys
import getopt
import signal
import shutil
import arrow
from subprocess import Popen, PIPE, SubprocessError
from pathlib import Path
from colorama import Fore
from os import environ as env


current_subprocs = set()
shutdown = False

def handle_signal(signum, frame):
    # send signal recieved to subprocesses
    global shutdown
    shutdown = True
    for proc in current_subprocs:
        if proc.poll() is None:
            proc.send_signal(signum)


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

DATA_PATH = env.get('DATA_PATH', './stream_chunks')
STREAM_URL = env.get('STREAM_URL', None)

if Path(Path(DATA_PATH) / Path('streaming')).exists():
    shutil.rmtree(Path(Path(DATA_PATH) / Path('streaming')).absolute())
Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
Path(Path(DATA_PATH) / Path('queue')).mkdir(parents=True, exist_ok=True)
Path(Path(DATA_PATH) / Path('streaming')).mkdir(parents=True, exist_ok=True)


def stream_audio(url):
    global shutdown
    command = ["ffmpeg", "-i", url, "-f",  "wav", "-ac", "1", "-ar", "16000", "-vn", "-c:a", "pcm_s16le", "-f", "segment", "-segment_time", "5", '%s/audio%%011d.wav' % Path(Path(DATA_PATH) / Path('streaming')).absolute()]
    proc = Popen(command, stderr=PIPE)
    current_subprocs.add(proc)

    errin = proc.stderr
    queue = []
    while True:
        if shutdown:
            break
        try:
            errline = errin.readline().decode().strip().replace("\r", "\n")
            errline_arr = errline.split("\n")
            for line in errline_arr:
                if line and "Opening \'" in line:
                    substr = line.strip().split("Opening \'")[1].split("\'")[0]
                    if substr not in [q[1] for q in queue]:
                        queue.append((str(arrow.utcnow().to('US/Pacific').format("MM-DD-YY-HH-mm-ss")), substr))

        except SubprocessError as _:
            errin.close()
            proc.kill()
            break

        if len(queue) > 1:
            timestamp, file_to_read = queue.pop(0)
            print('moved file %s to queue' % file_to_read)
            Path(file_to_read).rename(Path(DATA_PATH) / Path('queue') / Path("jeffco-ems-%s.wav" % timestamp))
    errin.close()
    current_subprocs.remove(proc)

def main(argv):

    url = ''
    try:
        opts, args = getopt.getopt(argv, "hi")
    except getopt.GetoptError:
        print(Fore.RED + 'stream.py -i <url> \n')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(Fore.RED + 'stream.py -i <url> \n')
        elif opt == '-i':
            url = arg
    if url == '':
        url = STREAM_URL
    print('starting')
    _ = stream_audio(url)


if __name__ == "__main__":
    main(sys.argv[1:])