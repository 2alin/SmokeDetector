# coding=utf-8
import json
import requests
import time
# noinspection PyPackageRequirements
import websocket
# noinspection PyPackageRequirements
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import chatcommunicate
import metasmoke
from globalvars import GlobalVars
import datahandling
from parsing import fetch_post_id_and_site_from_url
from tasks import Tasks


# noinspection PyClassHasNoInit,PyBroadException,PyMethodParameters
class DeletionWatcher:
    @classmethod
    def update_site_id_list(self):
        soup = BeautifulSoup(requests.get("https://meta.stackexchange.com/topbar/site-switcher/site-list").text,
                             "html.parser")
        site_id_dict = {}
        for site in soup.findAll("a", attrs={"data-id": True}):
            site_name = urlparse(site["href"]).netloc
            site_id = site["data-id"]
            site_id_dict[site_name] = site_id
        GlobalVars.site_id_dict = site_id_dict

    @classmethod
    def check_websocket_for_deletion(self, post_site_id, post_url, timeout):
        time_to_check = time.time() + timeout
        post_id = post_site_id[0]
        post_type = post_site_id[2]
        if post_type == "answer":
            question_id = str(datahandling.get_post_site_id_link(post_site_id))
            if question_id is None:
                return
        else:
            question_id = post_id
        post_site = post_site_id[1]
        if post_site not in GlobalVars.site_id_dict:
            return
        site_id = GlobalVars.site_id_dict[post_site]

        ws = websocket.create_connection("wss://qa.sockets.stackexchange.com/")
        ws.send(site_id + "-question-" + question_id)

        while time.time() < time_to_check:
            ws.settimeout(time_to_check - time.time())
            try:
                a = ws.recv()
            except websocket.WebSocketTimeoutException:
                Tasks.do(metasmoke.Metasmoke.send_deletion_stats_for_post, post_url, False)
                return False
            if a is not None and a != "":
                try:
                    action = json.loads(a)["action"]
                    if action == "hb":
                        ws.send("hb")
                        continue
                    else:
                        d = json.loads(json.loads(a)["data"])
                except:
                    continue
                if d["a"] == "post-deleted" and str(d["qId"]) == question_id \
                        and ((post_type == "answer" and "aId" in d and str(d["aId"]) == post_id) or
                             post_type == "question"):

                    Tasks.do(metasmoke.Metasmoke.send_deletion_stats_for_post, post_url, True)
                    return True

        Tasks.do(metasmoke.Metasmoke.send_deletion_stats_for_post, post_url, False)
        return False

    @classmethod
    def check_if_report_was_deleted(self, post_url, message):
        post_site_id = fetch_post_id_and_site_from_url(post_url)
        was_report_deleted = self.check_websocket_for_deletion(post_site_id, post_url, 1200)

        if was_report_deleted:
            try:
                message.delete()
            except:
                pass

    @classmethod
    def post_message_if_not_deleted(self, message_text, room, report_data):
        post_url = report_data[0]

        post_site_id = fetch_post_id_and_site_from_url(post_url)
        was_report_deleted = self.check_websocket_for_deletion(post_site_id, post_url, 300)

        if not was_report_deleted and not datahandling.is_false_positive(post_site_id[0:2]) and not \
                datahandling.is_ignored_post(post_site_id[0:2]):

            chatcommunicate._msg_queue.put((room, message_text, report_data))
