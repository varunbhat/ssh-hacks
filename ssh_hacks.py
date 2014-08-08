#!/usr/bin/env python
import os
import socket
import select
import sys
import threading

import paramiko
import time
import random

SSH_PORT = 22
DEFAULT_PORT = 4000

g_verbose = True

def handler(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        verbose('Forwarding request to %s:%d failed: %r' % (host, port, e))
        return

    verbose('Connected!  Tunnel open %r -> %r -> %r' % (chan.origin_addr,
                                                        chan.getpeername(), (host, port)))
    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()
    verbose('Tunnel closed from %r' % (chan.origin_addr,))


def reverse_forward_tunnel(server_port, remote_host, remote_port, transport):
    transport.request_port_forward('', server_port)
    while True:
        chan = transport.accept(10)
        if chan is None:
            try:
                transport.getpeername()
            except socket.error, v:
                print v
                return
            continue
        thr = threading.Thread(target=handler, args=(chan, remote_host, remote_port))
        thr.setDaemon(True)
        thr.start()

def verbose(s):
    if g_verbose:
        print(s)

def get_host_port(spec, default_port):
    "parse 'hostname:22' into a host and port, with the port optional"
    args = (spec.split(':', 1) + [default_port])[:2]
    args[1] = int(args[1])
    return args[0], args[1]


def main():
    while 1:
        client = paramiko.SSHClient()
        config = paramiko.SSHConfig()
#         config.parse(open(os.getenv('HOME') + '/.ssh/config'))
#         o = config.lookup('vmrf')
#         o['port'] = get_host_port(o['remoteforward'].split(' ')[0], SSH_PORT)
#         remote = get_host_port(o['remoteforward'].split(' ')[1], DEFAULT_PORT)
#         server = get_host_port(o['hostname'], SSH_PORT)
        server = ['1ivr.tk', 22]
        remote1 = ['localhost', int(random.random() * 1000 + 8000)]
        remote = ['localhost', 22]
    
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
    
        verbose('Connecting to ssh host %s:%d ...' % (server[0], server[1]))
        try:
            client.connect(server[0], server[1], username='ivr', key_filename="/home/varunbhat/.ssh/ivr.pem", password=None)
        except Exception as e:
            print('*** Failed to connect to %s:%d: %r' % (server[0], server[1], e))
            time.sleep(1)
            continue
    
        verbose('Now forwarding remote port %d to %s:%d ...' % (remote1[1] , remote[0], remote[1]))
    
        try:
            reverse_forward_tunnel(remote1[1] , remote[0], remote[1], client.get_transport())
        except KeyboardInterrupt:
            print('C-c: Port forwarding stopped.')
            sys.exit(0)
            
    

if __name__ == '__main__':
	main()
