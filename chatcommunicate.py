import random
import time
from parsing import *
from datahandling import *
from bayesianfuncs import bayesian_learn_title
from globalvars import GlobalVars
import os
import re
from datetime import datetime
from utcdate import UtcDate
from apigetpost import api_get_post
from spamhandling import handle_spam

# Please note: If new !!/ commands are added or existing ones are modified, don't forget to
# update the wiki at https://github.com/Charcoal-SE/SmokeDetector/wiki/Commands.


def post_message_in_room(room_id_str, msg, length_check=True):
    if room_id_str == GlobalVars.charcoal_room_id:
        GlobalVars.charcoal_hq.send_message(msg, length_check)
    elif room_id_str == GlobalVars.meta_tavern_room_id:
        GlobalVars.tavern_on_the_meta.send_message(msg, length_check)


def is_message_a_report(message_content, user_id, room_id):
    return user_id == GlobalVars.smokeDetector_user_id[room_id] and \
        message_content.startswith("[ [SmokeDetector](https://github.com/Charcoal-SE/SmokeDetector) ] ")


def watcher(ev, wrap2):
    if ev.type_id != 1:
        return
    print(ev)
    ev_room = str(ev.data["room_id"])
    ev_user_id = str(ev.data["user_id"])
    content_source = ev.message.content_source
    if is_message_a_report(content_source, ev_user_id, ev_room):
        GlobalVars.latest_smokedetector_report = content_source
    message_parts = content_source.split(" ")
    second_part_lower = "" if len(message_parts) < 2 else message_parts[1].lower()
    content_lower = ev.content.lower()

    ev_user_name = ev.data["user_name"].encode('utf-8')
    GlobalVars.tavern_users_chatting.append(ev_user_name)

    if re.compile(":[0-9]+").search(message_parts[0]) or message_parts[0].lower() == "sd":
        if (second_part_lower.startswith("false") or second_part_lower.startswith("fp")) \
                and is_privileged(ev_room, ev_user_id, wrap2):
            should_delete = True
            if not content_lower.startswith("sd f"):
                msg_id = int(message_parts[0][1:])
                msg_content = None
                msg_to_delete = wrap2.get_message(msg_id)
                if str(msg_to_delete.owner.id) == GlobalVars.smokeDetector_user_id[ev_room]:
                    msg_content = msg_to_delete.content_source
            else:
                msg_to_delete = None
                if len(GlobalVars.latest_smokedetector_report) < 1:
                    ev.message.reply("I don't have any reports posted after latest reboot.")
                    return
                msg_content = GlobalVars.latest_smokedetector_report
            quiet_action = ("-" in message_parts[1].lower())
            if msg_content is None:
                return
            site_post_id = fetch_post_id_and_site_from_msg_content(msg_content)
            if site_post_id is None:
                ev.message.reply("Could not register title as false positive.")
                return
            post_type = site_post_id[2]
            add_false_positive((site_post_id[0], site_post_id[1]))
            user_added = False
            if message_parts[1].lower().startswith("falseu") or message_parts[1].lower().startswith("fpu"):
                url_from_msg = fetch_owner_url_from_msg_content(msg_content)
                if url_from_msg is not None:
                    user = get_user_from_url(url_from_msg)
                    if user is not None:
                        add_whitelisted_user(user)
                        user_added = True
            learned = False
            if post_type == "question":
                learned = bayesian_learn_title(fetch_title_from_msg_content(msg_content), "good")
                if learned and user_added:
                    if not quiet_action:
                        ev.message.reply("Registered question as false positive, whitelisted user and added title to Bayesian doctype 'good'.")
                elif learned:
                    if not quiet_action:
                        ev.message.reply("Registered question as false positive and added title to Bayesian doctype 'good'.")
                else:
                    ev.message.reply("Registered question as false positive, but could not add title to Bayesian doctype 'good'.")
            elif post_type == "answer":
                if user_added:
                    if not quiet_action:
                        ev.message.reply("Registered answer as false positive and whitelisted user.")
                else:
                    if not quiet_action:
                        ev.message.reply("Registered answer as false positive.")
            if should_delete:
                try:
                    msg_to_delete.delete()
                except:
                    pass
        if (second_part_lower.startswith("true") or second_part_lower.startswith("tp")) \
                and is_privileged(ev_room, ev_user_id, wrap2):
            if not content_lower.startswith("sd t"):
                msg_id = int(message_parts[0][1:])
                msg_content = None
                msg_true_positive = wrap2.get_message(msg_id)
                if str(msg_true_positive.owner.id) == GlobalVars.smokeDetector_user_id[ev_room]:
                    msg_content = msg_true_positive.content_source
            else:
                if len(GlobalVars.latest_smokedetector_report) < 1:
                    ev.message.reply("I don't have any reports posted after latest reboot.")
                    return
                msg_content = GlobalVars.latest_smokedetector_report
            quiet_action = ("-" in message_parts[1].lower())
            if msg_content is None:
                return
            post_type = fetch_post_id_and_site_from_msg_content(msg_content)[2]
            learned = False
            user_added = False
            if message_parts[1].lower().startswith("trueu") or message_parts[1].lower().startswith("tpu"):
                url_from_msg = fetch_owner_url_from_msg_content(msg_content)
                if url_from_msg is not None:
                    user = get_user_from_url(url_from_msg)
                    if user is not None:
                        add_blacklisted_user(user)
                        user_added = True
            if post_type == "question":
                learned = bayesian_learn_title(fetch_title_from_msg_content(msg_content), "bad")
                if learned and user_added:
                    if not quiet_action:
                        ev.message.reply("Blacklisted user and registered question as true positive: added title to the Bayesian doctype 'bad'.")
                elif learned:
                    if not quiet_action:
                        ev.message.reply("Registered question as true positive: added title to the Bayesian doctype 'bad'.")
                else:
                    ev.message.reply("Something went wrong when registering question as true positive.")
            elif post_type == "answer":
                if user_added:
                    if not quiet_action:
                        ev.message.reply("Blacklisted user.")
                else:
                    ev.message.reply("`true`/`tp` cannot be used for answers because their job is to add the title of the *question* to the Bayesian doctype 'bad'. If you want to blacklist the poster of the answer, use `trueu` or `tpu`.")
        if second_part_lower.startswith("ignore") and is_privileged(ev_room, ev_user_id, wrap2):
            try:
                msg_id = int(message_parts[0][1:])
                msg_content = None
                msg_ignore = wrap2.get_message(msg_id)
                quiet_action = ("-" in second_part_lower)
                if(str(msg_ignore.owner.id) == GlobalVars.smokeDetector_user_id[ev_room]):
                    msg_content = msg_ignore.content_source
                if(msg_content is not None):
                    post_id_site = fetch_post_id_and_site_from_msg_content(msg_content)[0:2]
                    add_ignored_post(post_id_site)
                    if not quiet_action:
                        ev.message.reply("Post ignored; alerts about it will no longer be posted.")
            except:
                pass
        if second_part_lower.startswith("delete") or second_part_lower.startswith("remove") or second_part_lower.startswith("gone") \
                and is_privileged(ev_room, ev_user_id, wrap2):
            try:
                msg_id = int(message_parts[0][1:])
                msg_to_delete = wrap2.get_message(msg_id)
                if str(msg_to_delete.owner.id) == GlobalVars.smokeDetector_user_id[ev_room]:
                    msg_to_delete.delete()
            except:
                pass  # couldn't delete message
    if content_lower.startswith("!!/addblu") \
            and is_privileged(ev_room, ev_user_id, wrap2):
        uid, val = get_user_from_list_command(content_lower)
        if uid > -1 and val != "":
            add_blacklisted_user((uid, val))
            ev.message.reply("User blacklisted (`%s` on `%s`)." % (uid, val))
        elif uid == -2:
            ev.message.reply("Error: %s" % val)
        else:
            ev.message.reply("Invalid format. Valid format: `!!/addblu profileurl` *or* `!!/addblu userid sitename`.")
    if content_lower.startswith("!!/rmblu") \
            and is_privileged(ev_room, ev_user_id, wrap2):
        uid, val = get_user_from_list_command(content_lower)
        if uid > -1 and val != "":
            if remove_blacklisted_user((uid, val)):
                ev.message.reply("User removed from blacklist (`%s` on `%s`)." % (uid, val))
            else:
                ev.message.reply("User is not blacklisted.")
        elif uid == -2:
            ev.message.reply("Error: %s" % val)
        else:
            ev.message.reply("Invalid format. Valid format: `!!/rmblu profileurl` *or* `!!/rmblu userid sitename`.")
    if content_lower.startswith("!!/isblu"):
        uid, val = get_user_from_list_command(content_lower)
        if uid > -1 and val != "":
            if is_blacklisted_user((uid, val)):
                ev.message.reply("User is blacklisted. (`%s` on `%s`)." % (uid, val))
            else:
                ev.message.reply("User is not blacklisted. (`%s` on `%s`)." % (uid, val))
        elif uid == -2:
            ev.message.reply("Error: %s" % val)
        else:
            ev.message.reply("Invalid format. Valid format: `!!/isblu profileurl` *or* `!!/isblu userid sitename`.")
    if content_lower.startswith("!!/addwlu") \
            and is_privileged(ev_room, ev_user_id, wrap2):
        uid, val = get_user_from_list_command(content_lower)
        if uid > -1 and val != "":
            add_whitelisted_user((uid, val))
            ev.message.reply("User whitelisted (`%s` on `%s`)." % (uid, val))
        elif uid == -2:
            ev.message.reply("Error: %s" % val)
        else:
            ev.message.reply("Invalid format. Valid format: `!!/addwlu profileurl` *or* `!!/addwlu userid sitename`.")
    if content_lower.startswith("!!/rmwlu") \
            and is_privileged(ev_room, ev_user_id, wrap2):
        uid, val = get_user_from_list_command(content_lower)
        if uid != -1 and val != "":
            if remove_whitelisted_user((uid, val)):
                ev.message.reply("User removed from whitelist (`%s` on `%s`)." % (uid, val))
            else:
                ev.message.reply("User is not whitelisted.")
        elif uid == -2:
            ev.message.reply("Error: %s" % val)
        else:
            ev.message.reply("Invalid format. Valid format: `!!/rmwlu profileurl` *or* `!!/rmwlu userid sitename`.")
    if content_lower.startswith("!!/iswlu"):
        uid, val = get_user_from_list_command(content_lower)
        if uid > -1 and val != "":
            if is_whitelisted_user((uid, val)):
                ev.message.reply("User is whitelisted. (`%s` on `%s`)." % (uid, val))
            else:
                ev.message.reply("User is not whitelisted. (`%s` on `%s`)." % (uid, val))
        elif uid == -2:
            ev.message.reply("Error: %s" % val)
        else:
            ev.message.reply("Invalid format. Valid format: `!!/iswlu profileurl` *or* `!!/iswlu userid sitename`.")
    if content_lower.startswith("!!/report") \
            and is_privileged(ev_room, ev_user_id, wrap2):
        if len(message_parts) < 2:
            ev.message.reply("Not enough arguments.")
            return
        url = message_parts[1]
        post_data = api_get_post(url)
        if post_data is False:
            ev.message.reply("Could not find data for this post in the API. Check whether the post is not deleted yet.")
            return
        handle_spam(post_data.title, post_data.owner_name, post_data.site, post_data.post_url,
                    post_data.owner_url, post_data.post_id, ["Manually reported " + post_data.post_type],
                    post_data.post_type == "answer")
    if content_lower.startswith("!!/wut"):
        ev.message.reply("Whaddya mean, 'wut'? Humans...")
    if content_lower.startswith("!!/lick"):
        ev.message.reply("*licks ice cream cone*")
    if content_lower.startswith("!!/hats"):
        wb_end = datetime(2015, 1, 5, 0, 0, 0)
        now = datetime.utcnow()
        if wb_end > now:
            diff = wb_end - now
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            daystr = "days" if diff.days != 1 else "day"
            hourstr = "hours" if hours != 1 else "hour"
            minutestr = "minutes" if minutes != 1 else "minute"
            secondstr = "seconds" if seconds != 1 else "second"
            ev.message.reply("HATS ARE AWESOME. Winter Bash will end in %s %s, %s %s, %s %s and %s %s. :(" %
                             (diff.days, daystr, hours, hourstr, minutes, minutestr, seconds, secondstr))
        else:
            ev.message.reply("WINTERBASH IS OVER! :(")
    if content_lower.startswith("!!/so2015"):
        election_start = datetime(2015, 4, 17, 20, 0, 0)
        election_end = datetime(2015, 4, 21, 20, 0, 0)

        now = datetime.utcnow()

        if election_start > now:
            diff = election_start - now
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            daystr = "days" if diff.days != 1 else "day"
            hourstr = "hours" if hours != 1 else "hour"
            minutestr = "minutes" if minutes != 1 else "minute"
            secondstr = "seconds" if seconds != 1 else "second"
            ev.message.reply("Yay for the [2015 Stack Overflow Moderator Election](http://stackoverflow.com/election/6)! Election voting begins in %s %s, %s %s, %s %s and %s %s." % (diff.days, daystr, hours, hourstr, minutes, minutestr, seconds, secondstr))
        elif election_end > now:
            diff = election_end - now
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            daystr = "days" if diff.days != 1 else "day"
            hourstr = "hours" if hours != 1 else "hour"
            minutestr = "minutes" if minutes != 1 else "minute"
            secondstr = "seconds" if seconds != 1 else "second"
            ev.message.reply("Yay for the [2015 Stack Overflow Moderator Election](http://stackoverflow.com/election/6)! Election voting ends in %s %s, %s %s, %s %s and %s %s." % (diff.days, daystr, hours, hourstr, minutes, minutestr, seconds, secondstr))
        elif now < election_end:
            ev.message.reply("Congrats to Martijn Pieters, someone else, and someone else!")
    if content_lower.startswith("!!/alive"):
        if ev_room == GlobalVars.charcoal_room_id:
            ev.message.reply('Of course')
        elif ev_room == GlobalVars.meta_tavern_room_id:
            ev.message.reply(random.choice(['Yup', 'You doubt me?', 'Of course', '... did I miss something?',
                                            'plz send teh coffee',
                                            'Watching this endless list of new questions *never* gets boring',
                                            'Kinda sorta']))
    if content_lower.startswith("!!/rev"):
            ev.message.reply(
                '[' +
                GlobalVars.commit_with_author +
                '](https://github.com/Charcoal-SE/SmokeDetector/commit/' +
                GlobalVars.commit +
                ')'
            )
    if content_lower.startswith("!!/status"):
            now = datetime.utcnow()
            diff = now - UtcDate.startup_utc_date
            minutes, remainder = divmod(diff.seconds, 60)
            minutestr = "minutes" if minutes != 1 else "minute"
            ev.message.reply('Running since %s UTC (%s %s)' % (GlobalVars.startup_utc, minutes, minutestr))
    if content_lower.startswith("!!/reboot"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            post_message_in_room(ev_room, "Goodbye, cruel world")
            os._exit(5)
    if content_lower.startswith("!!/stappit"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            post_message_in_room(ev_room, "Goodbye, cruel world")
            os._exit(6)
    if content_lower.startswith("!!/master"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            ev.message.reply("Checking out to master and restarting...")
            os._exit(8)
    if content_lower.startswith("!!/clearbl"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            if os.path.isfile("blacklistedUsers.txt"):
                os.remove("blacklistedUsers.txt")
                GlobalVars.blacklisted_users = []
                ev.message.reply("Kaboom, blacklisted users cleared.")
            else:
                ev.message.reply("There are no blacklisted users at the moment.")
    if content_lower.startswith("!!/block"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            ev.message.reply("blocked")
            timeToBlock = ev.content[9:].strip()
            timeToBlock = int(timeToBlock) if timeToBlock else 0
            if 0 < timeToBlock < 14400:
                GlobalVars.blockedTime = time.time() + timeToBlock
            else:
                GlobalVars.blockedTime = time.time() + 900
    if content_lower.startswith("!!/unblock"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            GlobalVars.blockedTime = time.time()
            ev.message.reply("unblocked")
    if content_lower.startswith("!!/errorlogs"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            count = -1
            if len(message_parts) != 2:
                ev.message.reply("The !!/errorlogs command requires 1 argument.")
                return
            try:
                count = int(message_parts[1])
            except ValueError:
                pass
            if count == -1:
                ev.message.reply("Invalid argument.")
                return
            logs_part = fetch_lines_from_error_log(count)
            post_message_in_room(ev_room, logs_part, False)
    if content_lower.startswith("!!/pull"):
        if is_privileged(ev_room, ev_user_id, wrap2):
            r = requests.get('https://api.github.com/repos/Charcoal-SE/SmokeDetector/git/refs/heads/master')
            latest_sha = r.json()["object"]["sha"]
            r = requests.get('https://api.github.com/repos/Charcoal-SE/SmokeDetector/commits/' + latest_sha + '/statuses')
            states = []
            for status in r.json():
                state = status["state"]
                states.append(state)
            if "success" in states:
                ev.message.reply("Pulling latest from master -- CI build passed.")
                os._exit(3)
            elif "error" in states or "failure" in states:
                ev.message.reply("CI build failed! :( Please check your commit.")
            elif "pending" in states or not states:
                ev.message.reply("CI build is still pending, wait until the build has finished and then pull again.")
    if content_lower.startswith("!!/help"):
        ev.message.reply("I'm [SmokeDetector](https://github.com/Charcoal-SE/SmokeDetector), a bot that detects spam and low-quality posts on the network and posts alerts to chat. [A command list is available here](https://github.com/Charcoal-SE/SmokeDetector/wiki/Commands).")
    if content_lower.startswith("!!/apiquota"):
        ev.message.reply(GlobalVars.apiquota)
    if content_lower.startswith("!!/location"):
        ev.message.reply(GlobalVars.location)
    if content_lower.startswith("!!/queuestatus"):
        post_message_in_room(ev_room, GlobalVars.bodyfetcher.print_queue(), False)
    if content_lower.startswith("!!/blame") and ev_room == GlobalVars.meta_tavern_room_id:
        GlobalVars.tavern_users_chatting = list(set(GlobalVars.tavern_users_chatting))  # Make unique
        user_to_blame = random.choice(GlobalVars.tavern_users_chatting)
        ev.message.reply("It's " + user_to_blame + "'s fault.")
    if "smokedetector" in content_lower and "fault" in content_lower and ("xkcdbot" in ev_user_name.lower() or "bjb568" in ev_user_name.lower()):
        ev.message.reply("Liar")
