import random
from threading import Thread, Lock
from parsing import *
from datahandling import *
from metasmoke import Metasmoke
from globalvars import GlobalVars
import os
import re
from datetime import datetime
from utcdate import UtcDate
from apigetpost import api_get_post
from spamhandling import handle_spam, handle_user_with_all_spam
from termcolor import colored
from findspam import FindSpam
from deletionwatcher import DeletionWatcher
from ChatExchange.chatexchange.messages import Message
import chatcommands


# Please note: If new !!/ commands are added or existing ones are modified, don't forget to
# update the wiki at https://github.com/Charcoal-SE/SmokeDetector/wiki/Commands.

add_latest_message_lock = Lock()

command_aliases = {
    "f": "fp-",
    "notspam": "fp-",
    "k": "tpu-",
    "spam": "tpu-",
    "rude": "tpu-",
    "abuse": "tpu-",
    "abusive": "tpu-",
    "offensive": "tpu-",
    "n": "naa",
}


cmds = chatcommands.command_dict

def post_message_in_room(room_id_str, msg, length_check=True):
    if room_id_str == GlobalVars.charcoal_room_id:
        GlobalVars.charcoal_hq.send_message(msg, length_check)
    elif room_id_str == GlobalVars.meta_tavern_room_id:
        GlobalVars.tavern_on_the_meta.send_message(msg, length_check)
    elif room_id_str == GlobalVars.socvr_room_id:
        GlobalVars.socvr.send_message(msg, length_check)


def is_smokedetector_message(user_id, room_id):
    return user_id == GlobalVars.smokeDetector_user_id[room_id]


def add_to_listen_if_edited(host, message_id):
    if host + str(message_id) not in GlobalVars.listen_to_these_if_edited:
        GlobalVars.listen_to_these_if_edited.append(host + str(message_id))
    if len(GlobalVars.listen_to_these_if_edited) > 500:
        GlobalVars.listen_to_these_if_edited = GlobalVars.listen_to_these_if_edited[-500:]


def print_chat_message(ev):
    message = colored("Chat message in " + ev.data["room_name"] + " (" + str(ev.data["room_id"]) + "): \"", attrs=['bold'])
    message += ev.data['content']
    message += "\""
    print message + colored(" - " + ev.data['user_name'], attrs=['bold'])


def special_room_watcher(ev, wrap2):
    if ev.type_id != 1:
        return
    ev_user_id = str(ev.data["user_id"])
    content_source = ev.message.content_source
    if is_smokedetector_message(ev_user_id, GlobalVars.charcoal_room_id):
        post_site_id = fetch_post_id_and_site_from_msg_content(content_source)
        post_url = fetch_post_url_from_msg_content(content_source)
        if post_site_id is not None and post_url is not None:
            t_check_websocket = Thread(target=DeletionWatcher.check_if_report_was_deleted, args=(post_site_id, post_url, ev.message))
            t_check_websocket.daemon = True
            t_check_websocket.start()


def watcher(ev, wrap2):
    if ev.type_id != 1 and ev.type_id != 2:
        return
    if ev.type_id == 2 and (wrap2.host + str(ev.message.id)) not in GlobalVars.listen_to_these_if_edited:
        return

    print_chat_message(ev)

    ev_room = str(ev.data["room_id"])
    ev_user_id = str(ev.data["user_id"])
    ev_room_name = ev.data["room_name"].encode('utf-8')
    if ev.type_id == 2:
        ev.message = Message(ev.message.id, wrap2)
    content_source = ev.message.content_source
    message_id = ev.message.id
    if is_smokedetector_message(ev_user_id, ev_room):
        add_latest_message_lock.acquire()
        add_latest_smokedetector_message(ev_room, message_id)
        add_latest_message_lock.release()

        post_site_id = fetch_post_id_and_site_from_msg_content(content_source)
        post_url = fetch_post_url_from_msg_content(content_source)
        if post_site_id is not None and (ev_room == GlobalVars.meta_tavern_room_id or ev_room == GlobalVars.socvr_room_id):
            t_check_websocket = Thread(target=DeletionWatcher.check_if_report_was_deleted, args=(post_site_id, post_url, ev.message))
            t_check_websocket.daemon = True
            t_check_websocket.start()
    message_parts = re.split('[ ,]+', content_source)

    ev_user_name = ev.data["user_name"]
    ev_user_link = "//chat.{host}/users/{user_id}".format(host=wrap2.host, user_id=ev.user.id)
    if ev_user_name != "SmokeDetector":
        GlobalVars.users_chatting[ev_room].append((ev_user_name, ev_user_link))

    shortcut_messages = []
    if message_parts[0].lower() == "sd":
        message_parts = preprocess_shortcut_command(content_source).split(" ")
        latest_smokedetector_messages = GlobalVars.latest_smokedetector_messages[ev_room]
        commands = message_parts[1:]
        if len(latest_smokedetector_messages) == 0:
            ev.message.reply("I don't have any messages posted after the latest reboot.")
            return
        if len(commands) > len(latest_smokedetector_messages):
            ev.message.reply("I've only posted {} messages since the latest reboot; that's not enough to execute all commands. No commands were executed.".format(len(latest_smokedetector_messages)))
            return
        for i in xrange(0, len(commands)):
            shortcut_messages.append(u":{message} {command_name}".format(message=latest_smokedetector_messages[-(i + 1)], command_name=commands[i]))
        reply = ""
        amount_none = 0
        amount_skipped = 0
        amount_unrecognized = 0
        length = len(shortcut_messages)
        for i in xrange(0, length):
            current_message = shortcut_messages[i]
            if length > 1:
                reply += str(i + 1) + ". "
            reply += u"[{0}] ".format(current_message.split(" ")[0])
            if current_message.split(" ")[1] != "-":
                result = handle_commands(content_lower=current_message.lower(),
                                         message_parts=current_message.split(" "),
                                         ev_room=ev_room,
                                         ev_room_name=ev_room_name,
                                         ev_user_id=ev_user_id,
                                         ev_user_name=ev_user_name,
                                         wrap2=wrap2,
                                         content=current_message,
                                         message_id=message_id)
                r = result
                if type(result) == tuple:
                    result = result[1]
                if result is not None and result is not False:
                    reply += result + os.linesep
                elif result is None:
                    reply += "<processed without return value>" + os.linesep
                    amount_none += 1
                elif result is False or r[0] is False:
                    reply += "<unrecognized command>" + os.linesep
                    amount_unrecognized += 1
            else:
                reply += "<skipped>" + os.linesep
                amount_skipped += 1
        if amount_unrecognized == length:
            add_to_listen_if_edited(wrap2.host, message_id)
        if amount_none + amount_skipped + amount_unrecognized == length:
            reply = ""

        reply = reply.strip()
        if reply != "":
            message_with_reply = u":{} {}".format(message_id, reply)
            if len(message_with_reply) <= 500 or "\n" in reply:
                ev.message.reply(reply, False)
    else:
        result = handle_commands(content_source.lower(), message_parts, ev_room, ev_room_name, ev_user_id, ev_user_name, wrap2, content_source, message_id)
        if type(result) != tuple:
            result = (True, result)
        if result[1] is not None:
            if wrap2.host + str(message_id) in GlobalVars.listen_to_these_if_edited:
                GlobalVars.listen_to_these_if_edited.remove(wrap2.host + str(message_id))
            message_with_reply = u":{} {}".format(message_id, result[1])
            if len(message_with_reply) <= 500 or "\n" in result[1]:
                ev.message.reply(result[1], False)
        if result[0] is False:
            add_to_listen_if_edited(wrap2.host, message_id)


def handle_commands(content_lower, message_parts, ev_room, ev_room_name, ev_user_id, ev_user_name, wrap2, content, message_id):
    message_url = "//chat.{host}/transcript/message/{id}#{id}".format(host=wrap2.host, id=message_id)
    second_part_lower = "" if len(message_parts) < 2 else message_parts[1].lower()
    if command_aliases.get(second_part_lower):
        second_part_lower = command_aliases.get(second_part_lower)
    command = content_lower.split()[0]
    if re.compile("^:[0-9]{4,}$").search(message_parts[0]):
        msg_id = int(message_parts[0][1:])
        msg = wrap2.get_message(msg_id)
        msg_content = msg.content_source
        quiet_action = ("-" in second_part_lower)
        if str(msg.owner.id) != GlobalVars.smokeDetector_user_id[ev_room] or msg_content is None:
            return
        post_url = fetch_post_url_from_msg_content(msg_content)
        post_site_id = fetch_post_id_and_site_from_msg_content(msg_content)
        if post_site_id is not None:
            post_type = post_site_id[2]
        else:
            post_type = None
        if (second_part_lower.startswith("false") or second_part_lower.startswith("fp")) \
                and is_privileged(ev_room, ev_user_id, wrap2):
            if not chatcommands.is_report(post_site_id):
                return "That message is not a report."

            t_metasmoke = Thread(target=Metasmoke.send_feedback_for_post,
                                 args=(post_url, second_part_lower, ev_user_name, ev_user_id, ))
            t_metasmoke.start()

            add_false_positive((post_site_id[0], post_site_id[1]))
            user_added = False
            user_removed = False
            url_from_msg = fetch_owner_url_from_msg_content(msg_content)
            user = None
            if url_from_msg is not None:
                user = get_user_from_url(url_from_msg)
            if second_part_lower.startswith("falseu") or second_part_lower.startswith("fpu"):
                if user is not None:
                    add_whitelisted_user(user)
                    user_added = True
            if "Blacklisted user:" in msg_content:
                if user is not None:
                    remove_blacklisted_user(user)
                    user_removed = True
            if post_type == "question":
                if user_added and not quiet_action:
                    return "Registered question as false positive and whitelisted user."
                elif user_removed and not quiet_action:
                    return "Registered question as false positive and removed user from the blacklist."
                elif not quiet_action:
                    return "Registered question as false positive."
            elif post_type == "answer":
                if user_added and not quiet_action:
                    return "Registered answer as false positive and whitelisted user."
                elif user_removed and not quiet_action:
                    return "Registered answer as false positive and removed user from the blacklist."
                elif not quiet_action:
                    return "Registered answer as false positive."
            try:
                msg.delete()
            except:
                pass
        if (second_part_lower.startswith("true") or second_part_lower.startswith("tp")) \
                and is_privileged(ev_room, ev_user_id, wrap2):
            if not chatcommands.is_report(post_site_id):
                return "That message is not a report."

            t_metasmoke = Thread(target=Metasmoke.send_feedback_for_post,
                                 args=(post_url, second_part_lower, ev_user_name, ev_user_id, ))
            t_metasmoke.start()

            user_added = False
            if second_part_lower.startswith("trueu") or second_part_lower.startswith("tpu"):
                url_from_msg = fetch_owner_url_from_msg_content(msg_content)
                if url_from_msg is not None:
                    user = get_user_from_url(url_from_msg)
                    if user is not None:
                        add_blacklisted_user(user, message_url, "http:" + post_url)
                        user_added = True
            if post_type == "question":
                if quiet_action:
                    return None
                if user_added:
                    return "Blacklisted user and registered question as true positive."
                return "Recorded question as true positive in metasmoke. Use `tpu` or `trueu` if you want to blacklist a user."
            elif post_type == "answer":
                if quiet_action:
                    return None
                if user_added:
                    return "Blacklisted user."
                return "Recorded answer as true positive in metasmoke. If you want to blacklist the poster of the answer, use `trueu` or `tpu`."

        if second_part_lower.startswith("ignore") and is_privileged(ev_room, ev_user_id, wrap2):
            if not chatcommands.is_report(post_site_id):
                return "That message is not a report."

            t_metasmoke = Thread(target=Metasmoke.send_feedback_for_post,
                                 args=(post_url, second_part_lower, ev_user_name, ev_user_id,))
            t_metasmoke.start()

            add_ignored_post(post_site_id[0:2])
            if not quiet_action:
                return "Post ignored; alerts about it will no longer be posted."
            else:
                return None
        if second_part_lower.startswith("naa") and is_privileged(ev_room, ev_user_id, wrap2):
            if not chatcommands.is_report(post_site_id):
                return "That message is not a report."
            if post_type != "answer":
                return "That report was a question; questions cannot be marked as NAAs."

            t_metasmoke = Thread(target=Metasmoke.send_feedback_for_post,
                                 args=(post_url, second_part_lower, ev_user_name, ev_user_id, ))
            t_metasmoke.start()

            add_ignored_post(post_site_id[0:2])
            if quiet_action:
                return None

            return "Recorded answer as an NAA in metasmoke."

        if (second_part_lower.startswith("delete") or second_part_lower.startswith("remove") or second_part_lower.startswith("gone") or second_part_lower.startswith("poof") or second_part_lower == "del") and is_privileged(ev_room, ev_user_id, wrap2):
            try:
                msg.delete()
            except:
                pass  # couldn't delete message
        if second_part_lower.startswith("postgone") and is_privileged(ev_room, ev_user_id, wrap2):
            edited = edited_message_after_postgone_command(msg_content)
            if edited is None:
                return "That's not a report."
            msg.edit(edited)
            return None
        if second_part_lower.startswith("why"):
            post_info = fetch_post_id_and_site_from_msg_content(msg_content)
            if post_info is None:
                post_info = fetch_user_from_allspam_report(msg_content)
                if post_info is None:
                    return "That's not a report."
                why = get_why_allspam(post_info)
                if why is not None or why != "":
                    return why

            else:
                post_id, site, _ = post_info
                why = get_why(site, post_id)
                if why is not None or why != "":
                    return why

            return "There is no `why` data for that user (anymore)."

    parameters = {
        'content': content,
        'content_lower': content_lower,
        'ev_room': ev_room,
        'ev_room_name': ev_room_name,
        'ev_user_id': ev_user_id,
        'ev_user_name': ev_user_name,
        'message_parts': message_parts,
        'message_url': message_url,
        'wrap2': wrap2,
    }
    try:
        return cmds[command](**parameters)
    except KeyError:
        return False, None  # Unrecognized command, can be edited later.


