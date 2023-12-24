#!/usr/bin/python3

class FormSniffer():
    
    def __init__(self):
        self.capitalization = False
        self.apostrophe = False
        self.punctuation = []
        self.diacritics = []
    
    def sniff(self, sample):
        if not sample.islower(): self.capitalization = True
        if ["'", "’"] in sample: self.apostrophe = True
        if ['.', ',', ';', ':', '?', '!'] in sample: self.punctuation = True
        if not sample.isascii(): self.diacritics = True
