#!/usr/bin/python3

#######################################################################
# Post-processor for Old French lemmatizer which standardizes tags to #
# the BFM norm and                                                    #
#######################################################################

import re

correct_lemmas = [
    ('.*', 'ADP.DET', 'au', 'à.le'),
    ('.*', 'ADP.DET', 'des', 'de.le'),
    ('.*', 'ADP.DET', 'du', 'de.le'),
    ('.*', 'ADP.DET', 'ès', 'en.le'),
    ('.*', 'ADP.DET', 'ou', 'en.le'),
    ('en', 'ADV', 'an', 'en'),
]

def main(infile, outfile):
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            for line in fin:
                try:
                    form, pos, lemma, score = line.rstrip().split('\t')
                except:
                    fout.write(line)
                    continue
                for entry in correct_lemmas:
                    if pos == entry[1] and lemma == entry[2] and re.fullmatch(entry[0], form):
                        lemma = entry[3]
                        if score == '5': score = '8'
                fout.write('\t'.join([form, pos, lemma, score]) + '\n')
