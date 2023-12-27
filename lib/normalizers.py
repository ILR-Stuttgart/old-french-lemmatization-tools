#!/usr/bin/python3

import sys, re

class Normalizer():
    
    DIACRITIC_MAP = {
        'à': 'a', 
        'á': 'a',
        'â': 'a',
        'ā': 'a',
        'ã': 'a',
        'ä': 'a',
        'ć': 'c',
        'ç': 'c',
        'í': 'i',
        'ì': 'i',
        'î': 'i',
        'ī': 'i',
        'ĩ': 'i',
        'ï': 'i',
        'ó': 'o',
        'ò': 'o',
        'ô': 'o',
        'ō': 'o',
        'õ': 'o',
        'ö': 'o',
        'ú': 'u',
        'ù': 'u',
        'û': 'u',
        'ū': 'u',
        'ũ': 'u',
        'ü': 'u',
        'ý': 'y',
        'ỳ': 'y',
        'ŷ': 'y',
        'ÿ': 'y',
        'À': 'A',
        'Á': 'A',
        'Â': 'A',
        'Ā': 'A',
        'Ã': 'A',
        'Ä': 'A',
        'Ć': 'C',
        'Ç': 'C',
        'Í': 'I',
        'Ì': 'I',
        'Î': 'I',
        'Ī': 'I',
        'Ĩ': 'I',
        'Ï': 'I',
        'Ó': 'O',
        'Ò': 'O',
        'Ô': 'O',
        'Ō': 'O',
        'Õ': 'O',
        'Ö': 'O',
        'Ú': 'U',
        'Ù': 'U',
        'Û': 'U',
        'Ū': 'U',
        'Ũ': 'U',
        'Ü': 'U',
        'Ý': 'Y',
        'Ỳ': 'Y',
        'Ŷ': 'Y',
        'Ÿ': 'Y'
    }
    
    def __init__(self, apostrophe=False, capitalization=False, 
        diacritics=False, end_digits=False):
        self.apostrophe = apostrophe
        self.capitalization = capitalization
        self.diacritics = diacritics
        self.end_digits = end_digits
        
    def normalize(self, obj):
        # If a string, normalize it.
        if isinstance(obj, str):
            return self._normalize(x)
        if isinstance(obj, list):
            try:
                return [self._normalize(x) for x in obj]
            except TypeError:
                print('Warning: normalization failed', file=sys.stderr)
                return obj

    def _normalize(self, s):
        if not isinstance(s, str): raise TypeError
        new_s = ''
        for i, char in enumerate(s):
            if not self.diacritics: char = self.DIACRITIC_MAP[char]
            if not self.capitalization: char = char.lower()
            try:
                last_char = s[i - 1]
            except IndexError:
                last_char = ''
            try:
                next_char = s[i + 1]
            except IndexError:
                next_char = ''
            if last_char and re.fullmatch(r"([^\s]'\s?)", last_char + char + next_char):
                char = ''
            if last_char and re.fullmatch(r"([^\s][0-9]\s?)", last_char + char + next_char):
                char = ''
            new_s += char
        return new_s

            
            
