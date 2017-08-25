#!/usr/bin/env python3

from glob import glob
from helpers import only_blacklists_changed


def test_blacklist_integrity():
    for bl_file in glob('bad_*.txt') + glob('blacklisted_*.txt'):
        with open(bl_file, 'r') as lines:
            seen = dict()
            for lineno, line in enumerate(lines, 1):
                if line.endswith('\r\n'):
                    raise(ValueError('{0}:{1}:DOS line ending'.format(bl_file, lineno)))
                if not line.endswith('\n'):
                    raise(ValueError('{0}:{1}:No newline'.format(bl_file, lineno)))
                if line == '\n':
                    raise(ValueError('{0}:{1}:Empty line'.format(bl_file, lineno)))
                if line in seen:
                    raise(ValueError('{0}:{1}:Duplicate entry {2} (also on line {3})'.format(
                        bl_file, lineno, line.rstrip('\n'), seen[line])))
                seen[line] = lineno


def test_blacklist_pull_diff():
    only_blacklists_diff = """watched_keywords.txt
                              bad_keywords.txt
                              blacklisted_websites.txt"""
    assert only_blacklists_changed(only_blacklists_diff)
    mixed_files_diff = """helpers.py
                          test/test_blacklists.py
                          blacklisted_usernames.txt"""
    assert not only_blacklists_changed(mixed_files_diff)
