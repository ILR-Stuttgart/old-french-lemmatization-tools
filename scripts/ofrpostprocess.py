#!/usr/bin/python3

#######################################################################
# Post-processor for Old French lemmatizer which standardizes tags to #
# the BFM norm and                                                    #
#######################################################################

import re

correct_lemmas = [
    # preposition + det forms with wrong lemma form
    ('.*', 'ADP.DET', 'au', 'à.le'),
    ('.*', 'ADP.DET', 'des', 'de.le'),
    ('.*', 'ADP.DET', 'du', 'de.le'),
    ('.*', 'ADP.DET', 'del', 'de.le'),
    ('.*', 'ADP.DET', 'ès', 'en.le'),
    ('.*', 'ADP.DET', 'ou', 'en.le'),
    ('.*', 'ADP.DET', 'dudit', 'de.ledit'),
    ('.*', 'ADP.PRON', 'èsquel', 'en.lequel'),
    ('.*', 'ADP.PRON', 'duquel', 'de.lequel'),
    # demonstratives given wrong form
    ('.*', 'DET', 'celui', 'cil'),
    ('.*', 'PRON', 'celui', 'cil'),
    ('.*', 'DET', 'icel', 'cil'),
    ('.*', 'PRON', 'icel', 'cil'),
    ('.*', 'DET', 'icest', 'cist'),
    ('.*', 'PRON', 'ice', 'ce'),
    ('.*', 'PRON', 'icelui', 'cil'),
    ('.*', 'DET', 'icelui', 'cil'),
    # deal with me > je
    ('.*m.*i', 'PRON', 'je', 'moi'),
    ('.*m[^i]*', 'PRON', 'je', 'me'),
    # deal with eux > il, la > il, etc.
    ('[^i][ul].+', 'PRON', 'il', 'eux'),
    ('l.*', 'PRON', 'il', 'le'),
    # get rid of tous
    ('.*', 'PRON', 'tous', 'tout'),
    ('.*', 'DET', 'tous', 'tout'),
    ('.*', 'PRON', 'trèstous', 'trèstout'),
    ('.*', 'DET', 'trèstous', 'trèstout'),
    # get rid / disambiguate uns if it doesn't end in [s] or [z]
    ('.*[^sz]', 'DET', '(.*\|)?uns(\|.*)', 'un'),
    # get rid of itel
    ('.*', 'DET', 'itel', 'tel'),
    # get rid of cui > qui
    ('.*', 'PRON', 'cui', 'qui'),
    # get rid of gens
    ('.*', 'NOUN', 'gens', 'gent'),
    # MCVF: P.D from split tags
    ('es', 'DET', '.*', 'le'),
    ('e', 'ADP', '.*', 'en'),
    # MCVF: de DET > de
    ("[Dd][e']?", 'DET', '.*', 'de'),
    # correct ne.il > ne.le and si.il > si.le
    ('.*', 'ADV.PRON', 'ne.il', 'ne.le'),
    ('.*', 'ADV.PRON', 'si.il', 'si.le'),
    ('en', 'ADV', 'an', 'en'),
    ('[Ll]i', 'PRON', 'il', 'li'),
    ('[Vv]us', 'PRON', 'vu', 'vous'), # Anglo-French vu
    ('[Ss]ire', 'NOUN', 'seigneur', 'sire'),
    ('[Mm]ort', 'NOUN', 'mourir', 'mort'), # pos disambiguation fails here because of mors NOUN
    # saint can be PROPN in gold annotation; confusing sometimes
    ('.*', 'PROPN', '(.*\|)?saint(\|.*)', 'saint')
]

def main(infile, outfile):
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            last_line = []
            for line in fin:
                try:
                    form, pos, lemma, score = line.rstrip().split('\t')
                except:
                    fout.write(line)
                    continue
                for entry in correct_lemmas:
                    if pos == entry[1] and re.fullmatch(entry[2], lemma) and re.fullmatch(entry[0], form):
                        lemma = entry[3]
                        score = '11'
                # Check for l'en, where l' is a determiner, should be "on"
                if last_line and last_line[1].endswith('DET') and last_line[2] == 'le' and pos == 'PRON' and lemma == 'en':
                    lemma = 'on'
                    score = '11'
                fout.write('\t'.join([form, pos, lemma, score]) + '\n')
                last_line = [form, pos, lemma, score]
