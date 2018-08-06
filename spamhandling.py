# coding=utf-8
import sys
import random
from findspam import FindSpam
import datahandling
import chatcommunicate
from globalvars import GlobalVars
from datetime import datetime
import parsing
import metasmoke
import excepthook
from classes import Post, PostParseError
from helpers import log, to_metasmoke_link, escape_format
from tasks import Tasks


# noinspection PyMissingTypeHints
def should_whitelist_prevent_alert(user_url, reasons):
    is_whitelisted = datahandling.is_whitelisted_user(parsing.get_user_from_url(user_url))
    if not is_whitelisted:
        return False
    return not any(r for r in set(reasons) if "username" not in r)


# noinspection PyMissingTypeHints
def check_if_spam(post):
    # if not post.body:
    #     body = ""
    # test, why = FindSpam.test_post(title, body, user_name, post_site,
    # is_answer, body_is_summary, owner_rep, post_score)
    test, why = FindSpam.test_post(post)
    if datahandling.is_blacklisted_user(parsing.get_user_from_url(post.user_url)):
        test.append("blacklisted user")
        blacklisted_user_data = datahandling.get_blacklisted_user_data(parsing.get_user_from_url(post.user_url))
        if len(blacklisted_user_data) > 1:
            if blacklisted_user_data[1] == "metasmoke":
                blacklisted_by = "the metasmoke API"
            else:
                blacklisted_by = blacklisted_user_data[1]
            blacklisted_post_url = blacklisted_user_data[2]
            if blacklisted_post_url:
                rel_url = blacklisted_post_url.replace("http:", "", 1)
                why += u"\nBlacklisted user - blacklisted for {} ({}) by {}".format(
                    blacklisted_post_url, to_metasmoke_link(rel_url), blacklisted_by
                )
            else:
                why += u"\n" + u"Blacklisted user - blacklisted by {}".format(blacklisted_by)
    if test:
        result = None
        if datahandling.has_already_been_posted(post.post_site, post.post_id, post.title):
            result = "post has already been reported"
        elif datahandling.is_false_positive((post.post_id, post.post_site)):
            result = "post is marked as false positive"
        elif should_whitelist_prevent_alert(post.user_url, test):
            result = "user is whitelisted"
        elif datahandling.is_ignored_post((post.post_id, post.post_site)):
            result = "post is ignored"
        elif datahandling.is_auto_ignored_post((post.post_id, post.post_site)):
            result = "post is automatically ignored"
        elif datahandling.has_community_bumped_post(post.post_url, post.body):
            result = "post is bumped by Community \u2666\uFE0F"
        # Dirty approach
        if result is None:  # Post not ignored
            return True, test, why
        else:
            return False, (test, why), result

    # XXX: Return an empty string for "why" if the post isn't scanned as spam
    # Don't touch if unsure, you'll break !!/report
    return False, None, ""


# noinspection PyMissingTypeHints
def check_if_spam_json(json_data):
    try:
        post = Post(json_data=json_data)
    except PostParseError as err:
        log('error', 'Parse error {0} when parsing json_data {1!r}'.format(
            err, json_data))
        return False, '', ''
    is_spam, reason, why = check_if_spam(post)
    return is_spam, reason, why


# noinspection PyBroadException,PyProtectedMember
def handle_spam(post, reasons, why):
    post_url = parsing.to_protocol_relative(parsing.url_to_shortlink(post.post_url))
    poster_url = parsing.to_protocol_relative(parsing.user_url_to_shortlink(post.user_url))
    shortened_site = post.post_site.replace("stackexchange.com", "SE")  # site.stackexchange.com -> site.SE
    datahandling.append_to_latest_questions(post.post_site, post.post_id, post.title if not post.is_answer else "")
    if len(reasons) == 1 and ("all-caps title" in reasons or
                              "repeating characters in title" in reasons or
                              "repeating characters in body" in reasons or
                              "repeating characters in answer" in reasons or
                              "repeating words in title" in reasons or
                              "repeating words in body" in reasons or
                              "repeating words in answer" in reasons):
        datahandling.add_auto_ignored_post((post.post_id, post.post_site, datetime.now()))
    if why is not None and why != "":
        datahandling.add_why(post.post_site, post.post_id, why)
    if post.is_answer and post.post_id is not None and post.post_id is not "":
        datahandling.add_post_site_id_link((post.post_id, post.post_site, "answer"), post.parent.post_id)
    try:
        # If the post is an answer type post, the 'title' is going to be blank, so when posting the
        # message contents we need to set the post title to the *parent* title, so the message in the
        # chat is properly constructed with parent title instead. This will make things 'print'
        # in a proper way in chat messages.
        sanitized_title = parsing.sanitize_title(post.title if not post.is_answer else post.parent.title)
        sanitized_title = escape_format(sanitized_title).strip()

        prefix = u"[ [SmokeDetector](//goo.gl/eLDYqh) ]"
        if GlobalVars.metasmoke_key:
            prefix_ms = u"[ [SmokeDetector](//goo.gl/eLDYqh) | [MS]({}) ]".format(
                to_metasmoke_link(post_url, protocol=False))
        else:
            prefix_ms = prefix

        # We'll insert reason list later
        edited = '' if not post.edited else ' \u270F\uFE0F'
        if not post.user_name.strip() or (not poster_url or poster_url.strip() == ""):
            s = u" {{}}: [{}]({}){} by a deleted user on `{}`".format(
                sanitized_title, post_url, edited, shortened_site)
            username = ""
        else:
            username = post.user_name.strip()
            escaped_username = escape_format(parsing.escape_markdown(username))
            s = u" {{}}: [{}]({}){} by [{}]({}) on `{}`".format(
                sanitized_title, post_url, edited, escaped_username, poster_url, shortened_site)

        Tasks.do(metasmoke.Metasmoke.send_stats_on_post,
                 post.title_ignore_type, post_url, reasons, post.body, username,
                 post.user_link, why, post.owner_rep, post.post_score,
                 post.up_vote_count, post.down_vote_count)

        log('debug', GlobalVars.parser.unescape(s).encode('ascii', errors='replace'))
        GlobalVars.deletion_watcher.subscribe(post_url)

        reason = message = None
        for reason_count in range(5, 0, -1):  # Try 5 reasons and all the way down to 1
            reason = ", ".join(reasons[:reason_count])
            if len(reasons) > reason_count:
                reason += ", +{} more".format(len(reasons) - reason_count)
            reason = reason.capitalize()
            message = prefix_ms + s.format(reason)  # Insert reason list
            if len(message) <= 500:
                break  # Problem solved, stop attempting

        s = s.format(reason)  # Later code needs this variable
        if len(message) > 500:
            message = (prefix_ms + s)[:500]  # Truncate directly and keep MS link

        without_roles = tuple("no-" + reason for reason in reasons) + ("site-no-" + post.post_site,)

        if set(reasons) - GlobalVars.experimental_reasons == set() and \
                not why.startswith("Post manually "):
            chatcommunicate.tell_rooms(message, ("experimental",),
                                       without_roles, notify_site=post.post_site, report_data=(post_url, poster_url))
        else:
            chatcommunicate.tell_rooms(message, ("all", "site-" + post.post_site),
                                       without_roles, notify_site=post.post_site, report_data=(post_url, poster_url))
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        excepthook.uncaught_exception(exc_type, exc_obj, exc_tb)
