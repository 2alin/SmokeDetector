import sys
from threading import Thread
from findspam import FindSpam
from datahandling import *
from parsing import get_user_from_url, unescape_title,\
    escape_special_chars_in_title, to_protocol_relative
from globalvars import GlobalVars
from datetime import datetime
from parsing import url_to_shortlink, user_url_to_shortlink
from metasmoke import Metasmoke
from deletionwatcher import DeletionWatcher
import excepthook


def should_whitelist_prevent_alert(user_url, reasons):
    is_whitelisted = is_whitelisted_user(get_user_from_url(user_url))
    if not is_whitelisted:
        return False
    reasons_copy = list(set(reasons))
    reasons_copy_copy = list(reasons_copy)
    for reason in reasons_copy:
        if "username" in reason:
            reasons_copy_copy.remove(reason)
    return len(reasons_copy_copy) == 0


def check_if_spam(title, body, user_name, user_url, post_site, post_id, is_answer, body_is_summary, owner_rep, post_score):
    if not body:
        body = ""
    test, why = FindSpam.test_post(title, body, user_name, post_site, is_answer, body_is_summary, owner_rep, post_score)
    if is_blacklisted_user(get_user_from_url(user_url)):
        test.append("blacklisted user")
        blacklisted_user_data = get_blacklisted_user_data(get_user_from_url(user_url))
        if len(blacklisted_user_data) > 1:
            message_url = 'http:' + blacklisted_user_data[1]
            blacklisted_post_url = blacklisted_user_data[2]
            if blacklisted_post_url:
                rel_url = blacklisted_post_url.replace("http:", "", 1)
                why += u"\n" + u"Blacklisted user - blacklisted for {} (http://metasmoke.erwaysoftware.com/posts/by-url?url={}) by {}".format(blacklisted_post_url, rel_url, message_url)
            else:
                why += u"\n" + u"Blacklisted user - blacklisted by {}".format(message_url)
    if 0 < len(test):
        if has_already_been_posted(post_site, post_id, title) or is_false_positive((post_id, post_site)) \
                or should_whitelist_prevent_alert(user_url, test) \
                or is_ignored_post((post_id, post_site)) \
                or is_auto_ignored_post((post_id, post_site)):
            return False, None, ""  # Don't repost. Reddit will hate you.
        return True, test, why
    return False, None, ""


def check_if_spam_json(data):
    d = json.loads(json.loads(data)["data"])
    try:
        _ = d["ownerUrl"]  # noqa
    except:
        # owner's account doesn't exist anymore, no need to post it in chat:
        # http://chat.stackexchange.com/transcript/message/18380776#18380776
        return False, None, ""
    title = d["titleEncodedFancy"]
    title = unescape_title(title)
    body = d["bodySummary"]
    poster = d["ownerDisplayName"]
    url = d["url"]
    post_id = str(d["id"])
    print time.strftime("%Y-%m-%d %H:%M:%S"), title.encode("ascii", errors="replace")
    site = d["siteBaseHostAddress"]
    site = site.encode("ascii", errors="replace")
    sys.stdout.flush()
    is_spam, reason, why = check_if_spam(title, body, poster, url, site, post_id, False, True, 1, 0)
    return is_spam, reason, why


def handle_spam(title, body, poster, site, post_url, poster_url, post_id, reasons, is_answer, why="", owner_rep=None, post_score=None, up_vote_count=None, down_vote_count=None, question_id=None):
    post_url = to_protocol_relative(url_to_shortlink(post_url))
    poster_url = to_protocol_relative(user_url_to_shortlink(poster_url))
    reason = ", ".join(reasons)
    reason = reason[:1].upper() + reason[1:]  # reason is capitalised, unlike the entries of reasons list
    append_to_latest_questions(site, post_id, title if not is_answer else "")
    if len(reasons) == 1 and ("all-caps title" in reasons or
                              "repeating characters in title" in reasons or
                              "repeating characters in body" in reasons or
                              "repeating characters in answer" in reasons or
                              "repeating words in title" in reasons or
                              "repeating words in body" in reasons or
                              "repeating words in answer" in reasons):
        add_auto_ignored_post((post_id, site, datetime.now()))
    if why is not None and why != "":
        add_why(site, post_id, why)
    if is_answer and question_id is not None:
        add_post_site_id_link((post_id, site, "answer"), question_id)
    try:
        title = escape_special_chars_in_title(title)

        if not poster.strip():
            s = u"[ [SmokeDetector](//git.io/vgx7b) ] {}: [{}]({}) by a deleted user on `{}`" \
                .format(reason, title.strip(), post_url, site)
            username = ""
            user_link = ""
        else:
            s = u"[ [SmokeDetector](//git.io/vgx7b) ] {}: [{}]({}) by [{}]({}) on `{}`" \
                .format(reason, title.strip(), post_url, poster.strip(), poster_url, site)
            username = poster.strip()
            user_link = poster_url

        t_metasmoke = Thread(target=Metasmoke.send_stats_on_post,
                             args=(title, post_url, reason.split(", "), body, username, user_link, why, owner_rep, post_score, up_vote_count, down_vote_count))
        t_metasmoke.start()

        print GlobalVars.parser.unescape(s).encode('ascii', errors='replace')
        if time.time() >= GlobalVars.blockedTime:
            append_to_latest_questions(site, post_id, title)

            if reason not in GlobalVars.experimental_reasons:
                metasmoke_link = u" [\u2026](//metasmoke.erwaysoftware.com/posts/by-url?url=" + post_url + ")"
                chq_pings = get_user_names_on_notification_list("stackexchange.com", GlobalVars.charcoal_room_id, site, GlobalVars.wrap)
                chq_msg = append_pings(s, chq_pings)
                chq_msg_ms = chq_msg + metasmoke_link
                GlobalVars.charcoal_hq.send_message(chq_msg_ms if len(chq_msg_ms) <= 500 else chq_msg if len(chq_msg) <= 500 else s[0:500])
                if reason not in GlobalVars.non_tavern_reasons and site not in GlobalVars.non_tavern_sites:
                    tavern_pings = get_user_names_on_notification_list("meta.stackexchange.com", GlobalVars.meta_tavern_room_id, site, GlobalVars.wrapm)
                    tavern_msg = append_pings(s, tavern_pings)
                    tavern_msg_ms = tavern_msg + metasmoke_link
                    msg_to_send = tavern_msg_ms if len(tavern_msg_ms) <= 500 else tavern_msg if len(tavern_msg) <= 500 else s[0:500]
                    t_check_websocket = Thread(target=DeletionWatcher.post_message_if_not_deleted, args=((post_id, site, "answer" if is_answer else "question"), msg_to_send, GlobalVars.tavern_on_the_meta))
                    t_check_websocket.daemon = True
                    t_check_websocket.start()
                if site == "stackoverflow.com" and reason not in GlobalVars.non_socvr_reasons and not is_answer:
                    socvr_pings = get_user_names_on_notification_list("stackoverflow.com", GlobalVars.socvr_room_id, site, GlobalVars.wrapso)
                    socvr_msg = append_pings(s, socvr_pings)
                    socvr_msg_ms = socvr_msg + metasmoke_link
                    GlobalVars.socvr.send_message(socvr_msg_ms if len(socvr_msg_ms) <= 500 else socvr_msg if len(socvr_msg) <= 500 else s[0:500])

            for specialroom in GlobalVars.specialrooms:
                sites = specialroom["sites"]
                if site in sites and reason not in specialroom["unwantedReasons"]:
                    room = specialroom["room"]
                    room_site = room._client.host
                    room_id = int(room.id)
                    room_pings = get_user_names_on_notification_list(room_site, room_id, site, room._client)
                    room_msg = append_pings(s, room_pings)
                    room_msg_ms = room_msg + metasmoke_link
                    specialroom["room"].send_message(room_msg_ms if len(room_msg_ms) <= 500 else room_msg if len(room_msg) <= 500 else s[0:500])
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        excepthook.uncaught_exception(exc_type, exc_obj, exc_tb)


def handle_user_with_all_spam(user, why):
    user_id = user[0]
    site = user[1]
    tab = "activity" if site == "stackexchange.com" else "topactivity"
    s = "[ [SmokeDetector](//git.io/vgx7b) ] All of this user's posts are spam: [user {} on {}](//{}/users/{}?tab={})" \
        .format(user_id, site, site, user_id, tab)
    print GlobalVars.parser.unescape(s).encode('ascii', errors='replace')
    if time.time() >= GlobalVars.blockedTime:
        add_why_allspam(user, why)
        GlobalVars.tavern_on_the_meta.send_message(s)
        GlobalVars.charcoal_hq.send_message(s)
        if site == "stackoverflow.com":
            GlobalVars.socvr.send_message(s)
        for specialroom in GlobalVars.specialrooms:
            if site in specialroom["sites"]:
                room = specialroom["room"]
                room.send_message(s)
