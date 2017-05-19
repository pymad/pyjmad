#!/usr/bin/env python
# -*- coding: utf-8 -*-
from subprocess import Popen
import os, pipes, signal, socket, time, site

print('Hack to fetch required JARs from CERN')
pid = Popen('sshpass -e ssh -oStrictHostKeyChecking=no -N -D 51080 '+pipes.quote(os.environ['SSHUSER']), shell=True).pid

for i in range(0,30):
    time.sleep(1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('127.0.0.1',51080))
    if result == 0:
        sock.close()
        break
    else:
        print('Still waiting for proxy, turn %d' % i)

os.environ['HTTP_PROXY'] = 'socks5h://localhost:51080/'
os.environ['HTTPS_PROXY'] = 'socks5h://localhost:51080/'

if not hasattr(site, 'getusersitepackages'):
    print('running in VirtualEnv, monkey-patching site module')
    site.getusersitepackages = lambda: ''

print('Stage set, triggering JAR fetching ...')
import cmmnbuild_dep_manager
mgr = cmmnbuild_dep_manager.Manager()
mgr.resolve()

os.kill(pid, signal.SIGTERM)