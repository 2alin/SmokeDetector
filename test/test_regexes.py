# -*- coding: utf-8 -*-
from findspam import FindSpam
import pytest


@pytest.mark.parametrize("title, body, username, site,  body_is_summary, match", [
    ('18669786819 gmail customer service number 1866978-6819 gmail support number', '', '', '', False, True),
    ('18669786819 gmail customer service number 1866978-6819 gmail support number', '', '', '', True, True),
    ('Is there any http://www.hindawi.com/ template for Cloud-Oriented Data Center Networking?', '', '', '', False, True),
    ('', '', 'bagprada', '', False, True),
    ('HOW DO YOU SOLVE THIS PROBLEM?', '', '', '', False, True),
    ('12 Month Loans quick @ http://www.quick12monthpaydayloans.co.uk/Elimination of collateral pledging', '', '', '', False, True),
    ('support for yahoo mail 18669786819 @call for helpline number', '', '', '', False, True),
    ('yahoo email tech support 1 866 978 6819 Yahoo Customer Phone Number ,Shortest Wait', '', '', '', False, True),
    ('kkkkkkkkkkkkkkkkkkkkkkkkkkkk', '<p>bbbbbbbbbbbbbbbbbbbbbb</p>', '', 'stackoverflow.com', False, True),
    ('Yay titles!', 'bbbbbbbbbbbabcdefghijklmnop', '', 'stackoverflow.com', False, True),
    ('kkkkkkkkkkkkkkkkkkkkkkkkkkkk', 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbb', '', 'stackoverflow.com', True, True),
    ('99999999999', '', '', 'stackoverflow.com', False, True),
    ('Spam spam spam', '', 'babylisscurl', 'stackoverflow.com', False, True),
    ('Question', '111111111111', '', 'stackoverflow.com', False, True),
    ('Question', 'I have this number: 111111111111111', '', 'stackoverflow.com', False, False),
    ('Random title', '$$$$$$$$$$$$', '', 'superuser.com', False, True),
    ('Non-spammy title', 'Call baba something today at +91 something', '', 'stackoverflow.com', False, True),
    ('Enhance SD Male Enhancement Supplements', '', '', '', False, True),
    ('Title here', '11111111111111', '', 'communitybuilding.stackexchange.com', False, True),
    ('Gmail Tech Support (1-844-202-5571) Gmail tech support number[Toll Free Number]?', '', '', 'stackoverflow.com', False, True),
    ('<>1 - 866-978-6819<>gmail password reset//gmail contact number//gmail customer service//gmail help number', '', '', 'stackoverflow.com', False, True),
    ('Hotmail technical support1 - 844-780-67 62 telephone number Hotmail support helpline number', '', '', 'stackoverflow.com', False, True),
    ('Valid title', 'Hotmail technical support1 - 844-780-67 62 telephone number Hotmail support helpline number', '', 'stackoverflow.com', True, True),
    ('[[[[[1-844-202-5571]]]]]Gmail Tech support[*]Gmail tech support number', '', '', 'stackoverflow.com', False, True),
    ('@@<>1 -866-978-6819 FREE<><><::::::@Gmail password recovery telephone number', '', '', 'stackoverflow.com', False, True),
    ('1 - 844-780-6762 outlook password recovery number-outlook password recovery contact number-outlook password recovery helpline number', '', '', 'stackoverflow.com', False, True),
    ('hotmail customer <*<*<*[*[ 1 - 844-780-6762 *** support toll free number Hotmail Phone Number hotmail account recovery phone number', '', '', 'stackoverflow.com', False, True),
    ('1 - 844-780-6762 outlook phone number-outlook telephone number-outlook customer care helpline number', '', '', 'stackoverflow.com', False, True),
    ('Repeating word word word word word word word word word', '', '', 'stackoverflow.com', False, True),
    ('Visit this website: optimalstackfacts.net', '', '', 'stackoverflow.com', False, True),
    ('his email address is (SOMEONE@GMAIL.COM)', '', '', 'meta.stackexchange.com', False, True),
    ('something', 'his email address is (SOMEONE@GMAIL.COM)', '', 'meta.stackexchange.com', False, True),
    ('asdf asdf asdf asdf asdf asdf asdf asdf', '', '', 'stackoverflow.com', True, True),
    ('A title', '>>>>  http://', '', 'stackoverflow.com', False, True),
    ('spam', '>>>> http://', '', 'stackoverflow.com', True, False),
    ('Another title', '<code>>>>>http://</code>', '', 'stackoverflow.com', False, False),
    ('This asdf should asdf not asdf be asdf matched asdf because asdf the asdf words do not asdf follow on each asdf other.', '', '', 'stackoverflow.com', False, False),
    ('What is the value of MD5 checksums if the MD5 hash itself could potentially also have been manipulated?', '', '', '', False, False),
    ('Probability: 6 Dice are rolled. Which is more likely, that you get exactly one 6, or that you get 6 different numbers?', '', '', '', False, False),
    ('The Challenge of Controlling a Powerful AI', '', 'Serban Tanasa', '', False, False),
    ('Reproducing image of a spiral using TikZ', '', 'Kristoffer Ryhl', '', False, False),
    ('What is the proper way to say "queryer"', '', 'jedwards', '', False, False),
    ('What\'s a real-world example of "overfitting"?', '', 'user3851283', '', False, False),
    ('How to avoid objects when traveling at greater than .75 light speed. or How Not to Go SPLAT?', '', 'bowlturner', '', False, False),
    ('Is it unfair to regrade prior work after detecting cheating?', '', 'Village', '', False, False),
    ('Inner workings of muscles', '', '', 'fitness.stackexchange.com', False, False),
    ('Cannot access http://stackoverflow.com/ with proxy enabled', '', '', 'superuser.com', False, False),
    ('This is a title.', 'This is a body.<pre>bbbbbbbbbbbbbb</pre>', '', 'stackoverflow.com', False, False),
    ('This is another title.', 'This is another body. <code>bbbbbbbbbbbb</code>', '', 'stackoverflow.com', False, False),
    ('Yet another title.', 'many whitespace             .', '', 'stackoverflow.com', False, False),
    ('Perfectly valid title.', 'bbbbbbbbbbbbbbbbbbbbbb', '', 'stackoverflow.com', True, False),
    ('Yay titles!', 'bbbbbbbbbbbabcdefghijklmnopqrstuvwxyz123456789a1b2c3d4e5', '', 'stackoverflow.com', False, False),
    ('Long double', 'I have this value: 9999999999999999', '', 'stackoverflow.com', False, False),
    ('Another valid title.', 'asdf asdf asdf asdf asdf asdf asdf asdf asdf', '', 'stackoverflow.com', True, False),
    ('Array question', 'I have an array with these values: 10 10 10 10 10 10 10 10 10 10 10 10', '', 'stackoverflow.com', False, False),
    ('Array question', 'I have an array with these values: 0 0 0 0 0 0 0 0 0 0 0 0', '', 'stackoverflow.com', False, False),
    ('his email address is (SOMEONE@GMAIL.COM)', '', '', 'stackoverflow.com', False, False),
    ('something', 'his email address is (SOMEONE@GMAIL.COM)', '', 'stackoverflow.com', False, False),
    ('something', 'URL: &email=someone@gmail.com', '', 'meta.stackexchange.com', False, False),
    ('random title', 'URL: page.html#someone@gmail.com', '', 'rpg.stackexchange.com', False, False),
    (u'Как рандомно получать числа 1 и 2?', 'Body here', u'Сашка', 'ru.stackoverflow.com', False, False),
    ('Should not be caught: http://example.com', '', '', 'drupal.stackexchange.com', False, False),
    ('Should not be caught: https://www.example.com', '', '', 'drupal.stackexchange.com', False, False),
    ('Should not be caught: something@example.com', '', '', 'drupal.stackexchange.com', False, False),
    ('Title here', '<img src="http://example.com/11111111111.jpg" alt="my image">', '', 'stackoverflow.com', False, False),
    ('Title here', '<img src="http://example.com/11111111111111.jpg" alt="my image" />', '', 'stackoverflow.com', False, False),
    ('Title here', '<a href="http://example.com/11111111111111.html">page</a>', '', 'stackoverflow.com', False, False),
    ('Error: 2147467259', '', '', 'stackoverflow.com', False, False)
])
def test_regexes(title, body, username, site, body_is_summary, match):
    # If we want to test answers separately, this should be changed
    is_answer = False
    result = FindSpam.test_post(title, body, username, site, is_answer, body_is_summary, 1, 0)[0]
    print title
    print result
    isspam = False
    if len(result) > 0:
        isspam = True
    assert match == isspam
