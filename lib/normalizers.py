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
    
    def __init__(self, uppercase=True, 
        is_ascii=False, pnc_in_tok=True,
        pnc_in_tok_except=["'", '’', '-', '.']):
        self.uppercase = uppercase
        self.is_ascii = is_ascii
        self.pnc_in_tok = pnc_in_tok
        self.pnc_in_tok_except = pnc_in_tok_except
        
    def normalize_tok(self, s):
        new_s = ''
        # Test if token contains alphanumeric characters
        l = [x.isalnum() for x in s]
        is_pnc = True if not True in l else False
        for char in s:
            if self.is_ascii and not char.isascii():
                char = self.DIACRITIC_MAP.get(char, '_')
            if not char.isalnum() and not is_pnc and not char in self.pnc_in_tok_except and not self.pnc_in_tok:
                char = ''
            if not self.uppercase: char = char.lower()
            new_s += char
        return new_s
