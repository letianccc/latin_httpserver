import subprocess
import os

def log(*vargs, **kargs):
    print(*vargs, **kargs)




def kill_pid():
    port = '21'
    command = ["netstat -tlnp |grep :%s" % port]
    a = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    # print(a.stdout.decode())

    result = a.stdout.decode()
    rows = result.split('\n')
    # print(result)
    target = []
    rows = rows[:-1]
    for r in rows:
        cols = r.split()
        pid_col = cols[-1]
        trailing = '/python3'
        if pid_col.endswith(trailing):
            pid = pid_col[:-len(trailing)]
            target.append(pid)
        else:
            raise Exception

    for pid in target:
        command = ['kill', '-9', pid]
        subprocess.run(command, stdout=subprocess.PIPE)

def kill_python_process():
    command = ["ps -C python3"]
    a = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    result = a.stdout.decode()
    rows = result.split('\n')
    target = []
    rows = rows[1:-1]
    cur_pid = str(os.getpid())
    for r in rows:
        cols = r.split()
        pid = cols[0]
        if pid != cur_pid:
            target.append(pid)

    for pid in target:
        command = ['kill', '-9', pid]
        subprocess.run(command, stdout=subprocess.PIPE)

if __name__ == '__main__':
    kill_python_process()
