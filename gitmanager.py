from sh import git
from requests.auth import HTTPBasicAuth
from globalvars import GlobalVars
import requests
import time
import json


class GitManager:
    @classmethod
    def add_to_blacklist(self, items_to_blacklist, username, code_permissions):
        # Check if we're on master
        if git("rev-parse", "--abbrev-ref", "HEAD").strip() != "master":
            return (False, "Not currently on master.")

        # Check that we're up-to-date with origin (GitHub)
        git.remote.update()
        if git("rev-parse", "refs/remotes/origin/master").strip() != git("rev-parse", "master").strip():
            return (False, "HEAD isn't at tip of origin's master branch")

        # Check that blacklisted_websites.txt isn't modified locally. That could get ugly fast
        if "blacklisted_websites.txt" in git.status():  # Also ugly
            return (False, "blacklisted_websites.txt modified locally. This is probably bad.")

        # Store current commit hash
        current_commit = git("rev-parse", "HEAD").strip()

        # Add items to file

        with open("blacklisted_websites.txt", "a") as blacklisted_websites:
            blacklisted_websites.write("\n" + "\n".join(items_to_blacklist))

        # Checkout a new branch (mostly unnecessary, but may help if we create PRs in the future
        branch = "auto-blacklist-%s" % str(time.time())
        git.checkout("-b", branch)

        # Clear HEAD just in case
        git.reset("HEAD")

        git.add("blacklisted_websites.txt")
        git.commit("-m", "Auto blacklist of %s by %s --autopull" % (", ".join(items_to_blacklist), username))

        if code_permissions:
            git.checkout("master")
            git.merge(branch)
            git.push()
        else:
            git.push("origin", branch)
            git.checkout("master")

            if GlobalVars.github_username is None or GlobalVars.github_password is None:
                return (False, "tell someone to set a GH password")

            payload = {"title": "%: Blacklist %" % (username, ", ".join(items_to_blacklist)),
                       "body": "% requests blacklist of domains: \n\n - %" % (username, "\n - ".join(items_to_blacklist)),
                       "head": branch,
                       "base": "master"}
            response = requests.post("https://api.github.com/repos/Undo1/AutoHubTest/pulls", auth=HTTPBasicAuth(GlobalVars.github_username, GlobalVars.github_password), data=json.dumps(payload))
            return (True, "You don't have code privileges, but I've [created a pull request for you](%s)." % response.json()["url"])

        git.checkout(current_commit)  # Return to old commit to await CI. This will make Smokey think it's in reverted mode if it restarts

        if not code_permissions:
            return (False, "Unable to perform action due to lack of code-level permissions. [Branch pushed](https://github.com/Charcoal-SE/SmokeDetector/tree/%s), PR at your leisure." % branch)

        return (True, "Blacklisted {0} - the entry will be applied via autopull if CI succeeds.".format(", ".join(items_to_blacklist)))
