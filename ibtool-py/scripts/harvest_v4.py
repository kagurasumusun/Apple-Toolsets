#!/usr/bin/env python3
"""
harvest_v4.py - Mac 上で ibtool を実行してフィクスチャを取得する (新セッション対応版)

新 upterm セッション (lYyOdmMKT7AYrCDUvuAd) で Mac に接続し、bash + ibtool を
実行して大量の本物の Apple 出力を sftp で取得する。
"""
import paramiko, time, os, sys, io, re

HOST = 'uptermd.upterm.dev'
PORT = 22
USER = sys.argv[1] if len(sys.argv) > 1 else 'lYyOdmMKT7AYrCDUvuAd'
KEY = '/home/user/.ssh/upterm_id_ed25519'

REMOTE_WORK = '/tmp/ibtool_probe'
LOCAL_BASE = '/home/user/ibtool-py/fixtures/probe'


def sftp_get_all(sftp, remote_dir, local_dir):
    """Recursively sftp get all files"""
    os.makedirs(local_dir, exist_ok=True)
    items = sftp.listdir_attr(remote_dir)
    for item in items:
        if item.filename.startswith('.'):
            continue
        rp = f'{remote_dir}/{item.filename}'
        lp = f'{local_dir}/{item.filename}'
        if item.st_mode & 0o170000 == 0o040000:  # dir
            sftp_get_all(sftp, rp, lp)
        else:
            try:
                sftp.get(rp, lp)
                print(f'  got: {rp} -> {lp}')
            except Exception as e:
                print(f'  ERR get {rp}: {e}')


def run(chan, cmd, t=3, long_t=None):
    """Run command in shell channel; returns output stripped of ANSI"""
    if long_t:
        t = long_t
    chan.send(cmd + '\n')
    time.sleep(t)
    data = b''
    chan.settimeout(t)
    try:
        while True:
            r = chan.recv(65536)
            if not r:
                break
            data += r
    except Exception:
        pass
    # Strip ANSI escapes
    text = data.decode('utf-8', errors='replace')
    text = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)
    text = re.sub(r'\x1b\([AB]', '', text)
    text = re.sub(r'\x1b[\(\)][0-9A-Za-z]', '', text)
    text = re.sub(r'\x1b[\[\]()][0-9;?]*[A-Za-z]?', '', text)
    text = re.sub(r'\r', '', text)
    # Last few lines that contain actual command output
    lines = [l for l in text.split('\n') if l.strip() and not l.startswith('[upterm]')]
    return '\n'.join(lines)


def main():
    os.makedirs(LOCAL_BASE, exist_ok=True)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY)
    client.connect(HOST, port=PORT, username=USER, pkey=pkey,
                   allow_agent=False, look_for_keys=False, timeout=15)
    print(f'connected to {USER}@{HOST}')

    sftp = client.open_sftp()
    print('sftp open')

    chan = client.get_transport().open_session(timeout=15)
    chan.get_pty(term='xterm', width=132, height=43)
    chan.invoke_shell()
    time.sleep(2)
    while chan.recv_ready():
        chan.recv(65536)
    print('shell opened')

    # 1. Verify ibtool
    print('--- ibtool info ---')
    print(run(chan, 'uname -a', 2))
    print(run(chan, 'xcode-select -p', 2))
    print(run(chan, 'xcrun --find ibtool', 2))
    print(run(chan, 'sw_vers', 2))

    # 2. Setup remote workdir
    print('--- setup remote workdir ---')
    run(chan, f'mkdir -p {REMOTE_WORK}', 2)
    run(chan, f'cd {REMOTE_WORK} && pwd', 2)

    sftp.close()
    chan.close()
    client.close()
    print('--- probe complete ---')


if __name__ == '__main__':
    main()
