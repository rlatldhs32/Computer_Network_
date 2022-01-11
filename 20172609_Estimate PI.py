#!/usr/bin/env python3
# Foundations of Python Network Programming, Third Edition
# https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter08/queuepi.py
# Small application that uses several different message queues

import matplotlib.pyplot as plt
import argparse
import random
import threading
import time
import zmq
import sys
B = 32  # number of bits of precision in each random integer


def ones_and_zeros(digits):
    """Express `n` in at least `d` binary digits, with no special prefix."""
    return bin(random.getrandbits(digits)).lstrip('0b').zfill(digits)


def client(zcontext, starturl, returnurl):
   # sys.stdout.flush()
    try:
        N = input('What is N ? : ')
        Num = int(N)
        if(Num < 0):
            print("Put Positive Integer.")
            return
    except ValueError as e:
        print(e)
        return

    zsock = zcontext.socket(zmq.PUSH)  # link between bitsource by PUSH-PULL
    zsock.connect(starturl)
    zsock.send_string(N)  # send N to bitsource
    isock = zcontext.socket(zmq.PULL)  # link between tally by PUSH-PULL
    isock.bind(returnurl)
    p = q = cnt = 0
    X = []
    Y = []
    plt.xlabel("Iteration Number")
    plt.ylabel("PI")
    plt.title("Getting Approximation of PI")
    time.sleep(1)  # to not lost data during socket moving
    while True:
        cnt += 1
        decision = isock.recv_string()
        q += 1
        if decision == 'Y':
            p += 4
        X.append(cnt)
        Y.append(p/q)
        plt.plot(X, Y, 'go')
        plt.pause(0.0001)  # to show  the changes in pi value in real-time.
        print(p/q)  # to know what is actually the estimated PI-value is .
        # because PLT's spot is somehow too big to know actual value.
        if(cnt == Num):
            plt.show()  # show Final plt


def bitsource(zcontext, incomingurl, outurl):

    isock = zcontext.socket(zmq.PULL)  # link between Client
    isock.bind(incomingurl)
    N = isock.recv_string()  # recv N from client
    Num = int(N)  # type change occur
    zsock = zcontext.socket(zmq.PUB)
    zsock.bind(outurl)
    time.sleep(1)  # to not lost data during socket moving
    for i in range(0, Num):  # Make Iteration which size is N
        zsock.send_string(ones_and_zeros(B * 2))
        time.sleep(0.01)


def always_yes(zcontext, in_url, out_url):
    isock = zcontext.socket(zmq.SUB)
    isock.connect(in_url)
    isock.setsockopt(zmq.SUBSCRIBE, b'00')
    osock = zcontext.socket(zmq.PUSH)
    osock.connect(out_url)
    time.sleep(1)  # to not lost data during socket moving
    while True:
        isock.recv_string()
        osock.send_string('Y')


def judge(zcontext, in_url, pythagoras_url, out_url):
    """Determine whether each input coordinate is inside the unit circle."""
    isock = zcontext.socket(zmq.SUB)
    isock.connect(in_url)
    for prefix in b'01', b'10', b'11':
        isock.setsockopt(zmq.SUBSCRIBE, prefix)
    psock = zcontext.socket(zmq.REQ)
    psock.connect(pythagoras_url)
    osock = zcontext.socket(zmq.PUSH)
    osock.connect(out_url)
    unit = 2 ** (B * 2)
    time.sleep(1)  # to not lost data during socket moving
    while True:
        bits = isock.recv_string()
        n, m = int(bits[::2], 2), int(bits[1::2], 2)
        psock.send_json((n, m))
        sumsquares = psock.recv_json()
        osock.send_string('Y' if sumsquares < unit else 'N')


def pythagoras(zcontext, url):
    """Return the sum-of-squares of number sequences."""
    zsock = zcontext.socket(zmq.REP)
    zsock.bind(url)
    time.sleep(1)  # to not lost data during socket moving
    while True:
        numbers = zsock.recv_json()
        zsock.send_json(sum(n * n for n in numbers))


def tally(zcontext, incomingurl, outurl):
    """Tally how many points fall within the unit circle, and print pi."""
    zsock = zcontext.socket(zmq.PULL)
    zsock.bind(incomingurl)
    osock = zcontext.socket(zmq.PUSH)  # link between client by PUSH-PULL
    osock.connect(outurl)
    time.sleep(1)  # to not lost data during socket moving

    while True:
        decision = zsock.recv_string()
        osock.send_string(decision)


if __name__ == '__main__':

    zcontext = zmq.Context()

    # make url which is for between client - bitsource
    Firstpushpull = 'tcp://127.0.0.1:6703'
    pubsub = 'tcp://127.0.0.1:6700'
    reqrep = 'tcp://127.0.0.1:6701'
    pushpull = 'tcp://127.0.0.1:6702'
    # make url which is for between tally - client
    lastpushpull = 'tcp://127.0.0.1:6704'

    choices = {'judge': judge, 'pythagoras': pythagoras, 'client': client,  # choose argument role
               'always_yes': always_yes, 'bitsource': bitsource, 'tally': tally}
    parser = argparse.ArgumentParser(description='Select function')
    parser.add_argument('role', choices=choices)
    parser.add_argument('-p', metavar='port', type=int, default=1060)
    args = parser.parse_args()
    function = choices[args.role]

    if function == judge:
        judge(zcontext, pubsub, reqrep, pushpull)
    elif id(function) == id(pythagoras):
        pythagoras(zcontext, reqrep)
    elif id(function) == id(client):
        client(zcontext, Firstpushpull, lastpushpull)
    elif id(function) == id(always_yes):
        always_yes(zcontext, pubsub, pushpull)
    elif id(function) == id(bitsource):
        bitsource(zcontext, Firstpushpull, pubsub)
    elif id(function) == id(tally):
        tally(zcontext, pushpull, lastpushpull)
    else:
        print("Put right value")
