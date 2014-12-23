# -*- coding: utf-8 -*-
import re
import phonenumbers

class FindSpam:
    rules = [
     {'regex': u"(?i)\\b(baba(ji)?|nike|vashi?k[ae]r[ae]n|sumer|kolcak|porn|molvi|judi bola|ituBola.com|lost lover|11s|acai|skin care|me2.do|black magic|bam2u|Neuro(3X|flexyn)|Nutra|Bowtrol|Forskolin|Blackline Elite|TestCore Pro|Xtreme Antler|fake (passports?|driver'?s? licen[cs]e|ID cards?)|bagprada)\\b|ಌ|(support|service|helpline)( phone)? number|1[ -]?866[ -]?978[ -]?6819", 'all': True,
        'sites': [], 'reason': "Bad keyword in {}", 'title': True, 'username': True},
     {'regex': u"(?i)\\b(weight (los[es]|reduction)|muscles? build(ing)?|muscles?( (grow(th)?|diets?))?|anti aging|SkinCentric|los[es] weight)\\b", 'all': True,
        'sites': ["fitness.stackexchange.com"], 'reason': "Bad keyword in {}", 'title': True, 'username': True},
     {'regex': u"(?i)^(?:(?=.*?\\b(?:online|hd)\\b)(?=.*?(?:free|full|unlimited)).*?movies?\\b|(?=.*?\\b(?:acai|kisn)\\b)(?=.*?care).*products?\\b|(?=.*?packer).*mover)", 'all': True,
        'sites': [], 'reason': "Bad keywords in {}", 'title': True, 'username': True},
     {'regex': u"\\d(?:_*\\d){9}|\\+?\\d_*\\d[\\s\\-]?(?:_*\\d){8,10}|\\d[ -]?\\d{3}[ -]?\\d{3}[ -]?\\d{4}", 'all': True,
        'sites': ["patents.stackexchange.com"], 'reason': "Phone number detected", 'validation_method': 'checkphonenumbers', 'title': True, 'username': False},
     {'regex': u"(?i)\\b(nigg(a|er)|asshole|crap|fag|fuck(ing?)?|shit|whore)s?\\b", 'all': True,
        'sites': [], 'reason': "Offensive {} detected",'insensitive':True, 'title': True, 'username': False},
     {'regex': u"^(?=.*[A-Z])[^a-z]*$", 'all': True, 'sites': [], 'reason': "All-caps title", 'title': True, 'username': False},
     {'regex': u"^(?=.*[0-9])[^a-zA-Z]*$", 'all': True, 'sites': [], 'reason': "Numbers-only title", 'title': True, 'username': False},
     {'regex': u"https?://[a-zA-Z0-9_.-]+\\.[a-zA-Z]{2,4}(/[a-zA-Z0-9_/?=.-])?", 'all': True,
        'sites': ["stackoverflow.com", "superuser.com", "askubuntu.com"], 'reason': "URL in title", 'title': True, 'username': False}
    ]

    @staticmethod
    def testpost(title, user_name, site):
        result = [];
        for rule in FindSpam.rules:
            if rule['all'] != (site in rule['sites']):
                matched_title = re.compile(rule['regex'], re.UNICODE).findall(title)
                matched_username = re.compile(rule['regex'], re.UNICODE).findall(user_name)
                if matched_title and rule['title']:
                    try:
                        if getattr(FindSpam, "%s" % rule['validation_method'])(matched_title):
                            result.append(rule['reason'])
                    except KeyError:                # There is no special logic for this rule
                        result.append(rule['reason'].replace("{}", "title"))
                if matched_username and rule['username']:
                    try:
                        if getattr(FindSpam, "%s" % rule['validation_method'])(matched_username):
                            result.append(rule['reason'])
                    except KeyError:                # There is no special logic for this rule
                        result.append(rule['reason'].replace("{}", "username"))                 
        return result

    @staticmethod
    def checkphonenumbers(matched):
        test_formats = [ "IN", "US", None ]
        for phone_number in matched:
            for testf in test_formats:
                try:
                    z = phonenumbers.parse(phone_number, testf)
                    if phonenumbers.is_possible_number(z) and phonenumbers.is_valid_number(z):
                        print "Possible %s, Valid %s, Explain: %s" % (phonenumbers.is_possible_number(z), phonenumbers.is_valid_number(z), z)
                        return True
                except phonenumbers.phonenumberutil.NumberParseException:
                    pass
        return False
