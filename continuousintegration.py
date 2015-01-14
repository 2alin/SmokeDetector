import socket
import requests
import sys
from globalvars import GlobalVars

def watchCi():
    HOST = ''
    PORT = 49494

    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "CI Socket Created"

    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
        print 'Bind Failed. Error code: ' + str(msg[0])
        return

    s.listen(10)
    print 'listening for ci changes'

    while 1:
        conn, addr = s.accept()
        circleci_addr = socket.getaddrinfo("circleci.com", 80, 0, 0, socket.IPPROTO_TCP)[0][4][0]
        is_circleci = addr == circleci_addr
        print 'Received request from ' + addr[0] + " ; " + "verified as CircleCI" if is_circleci else "NOT verified as CircleCI!"
        if not is_circleci:
            GlobalVars.charcoal_hq.send_message("WARNING: got socket that doesn't come from CircleCI")
            s.close()
            continue
        r=requests.get('https://api.github.com/repos/Charcoal-SE/SmokeDetector/git/refs/heads/master')
        latest_sha = r.json()["object"]["sha"]
        r = requests.get('https://api.github.com/repos/Charcoal-SE/SmokeDetector/commits/' + latest_sha + '/statuses')
        states = []
        for status in r.json():
            state = status["state"]
            states.append(state)
        if "success" in states:
            GlobalVars.charcoal_hq.send_message("CI build passed. Ready to pull!")
        elif "error" in states or "failure" in states:
            GlobalVars.charcoal_hq.send_message("CI build failed, *someone* (prolly Undo) borked something!")
    s.close()
