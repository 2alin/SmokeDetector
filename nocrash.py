#!/usr/bin/python

from sh import git
import os
import subprocess as sp
from time import sleep
import sys

# Get environment variables
ChatExchangeU = os.environ.get('ChatExchangeU')
ChatExchangeP = os.environ.get('ChatExchangeP')

if ChatExchangeU is None:
    ChatExchangeU = str(input("Username: ")).strip('\r\n')

os.environ['CEU'] = "h"

if ChatExchangeP is None:
    ChatExchangeP = str(input("Password: ")).strip('\r\n')

count = 0
crashcount = 0
stoprunning = False
switch_to_standby = False
ecode = None  # Define this to prevent errors

while stoprunning is False:
    # print "[NoCrash] Switch to Standby? %s" % switch_to_standby
    if count == 0:
        if switch_to_standby or ((len(sys.argv) > 1) and ("standby" in sys.argv)):
            switch_to_standby = False
            command = 'python ws.py standby'.split()
        else:
            command = 'python ws.py first_start'.split()
    else:
        if not switch_to_standby:
            command = 'python ws.py'.split()
        else:
            switch_to_standby = False
            command = 'python ws.py standby'.split()

    try:
        ecode = sp.call(command)
    except KeyboardInterrupt:
        # print "[NoCrash] KeyBoard Interrupt received.."
        ecode = 6
    except Exception as e:
        raise e

    if ecode == 3:
        # print "[NoCrash] Pull in new updates."
        git.checkout('deploy')
        git.pull()
        git.submodule('update')
        count = 0
        crashcount = 0

    elif ecode == 4:
        # print "[NoCrash] Crashed."
        count += 1
        sleep(5)

        if crashcount == 2:
            # print "[NoCrash] Going to reverted state."
            git.checkout('HEAD~1')
            count = 0
            crashcount = 0

        else:
            crashcount += 1

    elif ecode == 5:
        count = 0

    elif ecode == 6:
        # print "[NoCrash] Stopping"
        stoprunning = True

    elif ecode == 7:
        # print "[NoCrash] Go to Standby Restart Called"
        switch_to_standby = True

    elif ecode == 8:
        # print "[NoCrash] Checkout Deploy"
        git.checkout('deploy')
        count = 0
        crashcount = 0

    elif ecode == 10:
        # print "[NoCrash] Socket failure, let network settle before restart."
        sleep(5)
        count = 0

    else:
        # print "[NoCrash] Death by Evil, restart in 5 seconds."
        sleep(5)
        count += 1
