#!/usr/bin/python3

# Common functions

def parse_lexicon(fname, ignore_numbers=False):
    # For this script, need to parse the file into two lookup
    # dictionaries with key = form
    with open(fname, 'r', encoding='utf-8') as f:
        lemma_d = {}
        pos_d = {}
        for line in f:
            line = line.rstrip() # remove any trailing whitespace.
            x = line.split('\t')
            if len(x) != 3: continue # ignore malformed lines
            lemma, pos, forms = x[0], x[1], x[2].split('|')
            if ignore_numbers: # Remove numbers if ignore numbers is enabled
                s = ''
                for char in lemma:
                    if not char.isdigit():
                        s += char
                lemma = s
            for form in forms:
                if form in lemma_d:
                    lemma_d[form].append(lemma)
                    pos_d[form].append(pos)
                else:
                    lemma_d[form] = [lemma]
                    pos_d[form] = [pos]
    return lemma_d, pos_d # Return the two lookup dictionaries
