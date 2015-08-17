from globalvars import GlobalVars
import json
import requests

class Metasmoke:
    @classmethod
    def send_stats_on_post(self, post, reasons):
        
        payload = { 'post' : { 'title' : 'python', 'reasons': reasons } }

        headers = {'Content-type': 'application/json'}
        r=requests.post("http://localhost:3000/posts.json", data=json.dumps(payload), headers=headers)
