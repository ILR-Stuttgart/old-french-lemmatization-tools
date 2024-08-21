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
    ('m.i', 'PRON', 'je', 'moi'),
    ('m.?', 'PRON', 'je', 'me'),
    # deal with eux > il, la > il, etc.
    ('[^i][ul].+', 'PRON', 'il', 'eux'),
    ('l.*', 'PRON', 'il', 'le'),
    # deal with te > tu
    ('t.i', 'PRON', 'tu', 'toi'),
    ('t[^u]?', 'PRON', 'tu', 'te'),
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
    ("d[e']?", 'DET', '.*', 'de'),
    # correct ne.il > ne.le and si.il > si.le
    ('.*', 'ADV.PRON', 'ne.il', 'ne.le'),
    ('.*', 'ADV.PRON', 'si.il', 'si.le'),
    ('.*', 'PRON.PRON', 'je.il', 'je.le'),
    ('en', 'ADV', 'an', 'en'),
    ('li', 'PRON', 'il', 'li'),
    ('vus', 'PRON', 'vu', 'vous'), # Anglo-French vu
    ('sire', 'NOUN', 'seigneur', 'sire'),
    ('mort', 'NOUN', 'mourir', 'mort'), # pos disambiguation fails here because of mors NOUN
    # saint can be PROPN in gold annotation; confusing sometimes
    ('.*', 'PROPN', 'saint', 'saint'),
    # Correct some common forms that cause problems in QLR
    ('é', 'CCONJ', '.*', 'et'),
    ('ú', 'CCONJ', '.*', 'ou'),
    ('ú', 'PRON', '.*', 'où'),
]

def main(infile, outfile):
    unks = []
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            last_line = []
            for line in fin:
                try:
                    form, pos, lemma, score = line.rstrip().split('\t')
                except:
                    fout.write(line)
                    continue
                # Correct certain lemmas
                for entry in correct_lemmas:
                    if pos == entry[1] and re.fullmatch('(.*\|)?' + entry[2] + '(\|.*)?', lemma) and re.fullmatch(entry[0], form.lower()):
                        lemma = entry[3]
                        score = '11'
                # Check for l'en, where l' is a determiner, should be "on"
                if last_line and last_line[1].endswith('DET') and last_line[2] == 'le' and pos == 'PRON' and lemma == 'en':
                    lemma = 'on'
                    score = '11'
                # Add a big fat '?' in front of -10 scored lemmas
                if str(score) == '-10' and lemma != 'UNKNOWN':
                    lemma = '?' + lemma
                    unks.append(lemma)
                    #print(lemma)
                fout.write('\t'.join([form, pos, lemma, score]) + '\n')
                last_line = [form, pos, lemma, score]
    return unks
