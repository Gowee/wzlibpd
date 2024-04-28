#!/usr/bin/python3

from pywikibot import *

site = Site()
site.login()


def page(p):
    return Page(site, p)
