import os
from datetime import datetime
from ChatExchange.chatexchange.client import Client
import HTMLParser
import md5
import ConfigParser


class GlobalVars:
    false_positives = []
    whitelisted_users = []
    blacklisted_users = []
    ignored_posts = []
    auto_ignored_posts = []
    startup_utc = datetime.utcnow().strftime("%H:%M:%S")
    latest_questions = []
    blockedTime = 0
    charcoal_room_id = "11540"
    meta_tavern_room_id = "89"
    site_filename = {"electronics.stackexchange.com": "ElectronicsGood.txt",
                     "gaming.stackexchange.com": "GamingGood.txt", "german.stackexchange.com": "GermanGood.txt",
                     "italian.stackexchange.com": "ItalianGood.txt", "math.stackexchange.com": "MathematicsGood.txt",
                     "spanish.stackexchange.com": "SpanishGood.txt", "stats.stackexchange.com": "StatsGood.txt"}

    experimental_reasons = ["Code block"]  # Don't widely report these

    parser = HTMLParser.HTMLParser()
    wrap = Client("stackexchange.com")
    wrapm = Client("meta.stackexchange.com")
    wrapso = Client("stackoverflow.com")
    privileged_users = {charcoal_room_id: ["117490",  # Yes aka Pizza aka 1999
                                           "66258",  # Andy
                                           "31768",  # ManishEarth
                                           "103081",  # hichris123
                                           "73046",  # Undo
                                           "88521",  # ProgramFOX
                                           "59776",  # Doorknob
                                           "31465",  # Seth
                                           "88577",  # Santa Claus
                                           "34124",  # Andrew Leach
                                           "32436"],  # tchrist
                        meta_tavern_room_id: ["259867",  # Yes
                                              "244519",  # Roombatron5000
                                              "244382",  # TGMCians
                                              "194047",  # Jan Dvorak
                                              "158100",  # rene
                                              "178438",  # Manishearth
                                              "237685",  # hichris123
                                              "215468",  # Undo
                                              "229438",  # ProgramFOX
                                              "180276",  # Doorknob
                                              "161974",  # Lynn Crumbling
                                              "186281",  # Andy
                                              "266094",  # Unihedro
                                              "245167",  # Infinite Recursion (No.)
                                              "230261",  # Jason C
                                              "213575",  # Braiam
                                              "241919",  # Andrew T.
                                              "203389",  # backwards-Seth
                                              "202832",  # Mooseman
                                              "160017",  # DragonLord the Fiery
                                              "201151",  # bummi
                                              "188558",  # Frank
                                              "229166",  # Santa Claus
                                              "159034",  # Kevin Brown
                                              "203972",  # PeterJ
                                              "188673",  # Alexis King
                                              "258672",  # AstroCB
                                              "227577",  # Sam
                                              "255735",  # cybermonkey
                                              "279182",  # Ixrec
                                              "271104",  # James
                                              "220428",  # Qantas 94 Heavy
                                              "153355",  # tchrist
                                              "238426",  # Ed Cottrell
                                              "166899",  # Second Rikudo
                                              "287999",  # ASCIIThenANSI
                                              "208518",  # JNat
                                              "284141",  # michaelpri
                                              "260312",  # vaultah
                                              "244062",  # SouravGhosh
                                              "152859",  # Shadow Wizard
                                              "200235"]}  # durron597
    smokeDetector_user_id = {charcoal_room_id: "120914", meta_tavern_room_id: "266345"}

    censored_committer_names = {"3f4ed0f38df010ce300dba362fa63a62": "Undo1"}

    commit = os.popen('git log --pretty=format:"%h" -n 1').read()
    commit_author = os.popen('git log --pretty=format:"%cn" -n 1').read()

    if md5.new(commit_author).hexdigest() in censored_committer_names:
        commit_author = censored_committer_names[md5.new(commit_author).hexdigest()]

    commit_with_author = os.popen('git log --pretty=format:"%h (' + commit_author + ': *%s*)" -n 1').read()
    on_master = os.popen("git rev-parse --abbrev-ref HEAD").read().strip() == "master"
    charcoal_hq = None
    tavern_on_the_meta = None
    s = ""
    s_reverted = ""
    specialrooms = []
    bayesian_testroom = None
    apiquota = -1
    bodyfetcher = None
    se_sites = []
    tavern_users_chatting = []
    frequent_sentences = []

    config = ConfigParser.RawConfigParser()
    config.read('config')

    latest_smokedetector_messages = {meta_tavern_room_id: [], charcoal_room_id: []}

    location = config.get("Config", "location")
    print location
