#!/usr/bin/python3


########################################################################
# Script to lemmatize a file based on multiple sources                 #
# - Gold PoS (standardized) and lemmatization                          #
# - Lemma lookup from a lexicon with standardized PoS                  #
# - Auto lemmatization and tagging                                     #
########################################################################

class Error(Exception):
    pass
    
class SourceDataError(Error):
    pass

import argparse, os.path, tempfile
from lib.common import parse_lexicon

opj = os.path.join

def vote(forms, ignore_numbers=False):
    while '' in forms: forms.remove('') # Remove all empty strings
    if not forms: return '' # If only empty strings were offered, return empty string
    for i, form in enumerate(forms):
        if ignore_numbers: # Remove all digits from the string
            s = ''
            for char in form:
                if not char.isdigit():
                    s += char
            forms[i] = s
    forms = [x.split('|') for x in forms]
    print(forms)
    d = {}
    for i, options in enumerate(forms):
        weight = len(forms) - i + 100 # 100 points plus a weighting
        for option in options:
            if option in d:
                d[option] += weight 
            else:
                d[option] = weight
    maxscore = max(list(d.values()))
    l = []
    for option in d:
        if d[option] == maxscore: l.append(option)
    return '|'.join(l)
    
def score_lemmas(poss, goldlemmas=[], autolemmas=[], lookup_lemmas=[], lookup_poss=[]):
    print(goldlemmas, autolemmas, lookup_lemmas, lookup_poss)
    score = 0
    # Case 1. There is a gold lemma. Score 0.
    # Note that gold lemmas shouldn't be ambiguous...
    if goldlemmas:
        lemma = '|'.join(goldlemmas)
    # Case 2a. There is a single, unambiguous lemma from the lookup which 
    # matches the autolemma.
    elif lookup_lemmas and len(lookup_lemmas) == 1 and lookup_lemmas[0] in autolemmas:
        lemma = lookup_lemmas[0]
        score += 1
        # But if the lookup_lemma part of speech tag doesn't match, add 1 to score
        if not lookup_poss[0] in poss:
            score += 1
    # Case 2b. There is a single, unambiguous lemma from the lookup but it doesn't
    # match the autolemma
    elif lookup_lemmas and len(lookup_lemmas) == 1 and autolemmas:
        lemma = lookup_lemmas[0]
        score = 3
        # If the pos tag doesn't match, add 1
        if not lookup_poss[0] in poss:
            score += 1
    # Case 3. There are multiple lookup lemmas but only one with the correct pos.
    elif lookup_lemmas and len(set(lookup_poss) & set(poss)) == 1 and \
    lookup_poss.count((set(lookup_poss) & set(poss)).pop()) == 1:
        lemma = lookup_lemmas[lookup_poss.index((set(lookup_poss) & set(poss)).pop())]
        score = 1
        # If the autolemma doesn't match, add 1 to the score
        if autolemmas and not lemma in autolemmas:
            score += 1
    # Case 3b. There are multiple lookup lemmas with the correct pos, but
    # only one matches one of the autolemmas.
    #elif lookup_lemmas and len(set(lookup_poss) & set(poss)) > 1 or \
    #(len(set(lookup_poss) & set(poss)) == 1 and lookup_poss.count((set(lookup_poss) & set(poss)).pop()) > 1):
        # TODO
        #pass
    else:
        lemma = 'NOTDONE'
        score = 100
    return lemma, score

def disambiguate_autoposlemma(autoposlemmas, outfile='out.txt', ignore_numbers=False):
    # Open the files
    def get_pos_lemma(line):
        l = line.rstrip().split('\t')
        if len(l) == 3: return (l[1], l[2])
        if len(l) == 2: return (l[1], '')
        return ('', '')
        
    autoposlemma_fs = [open(x, 'r', encoding='utf-8') for x in autoposlemmas]
    with open(outfile, 'w', encoding='utf-8') as fout:
        for line in autoposlemma_fs[0]:
            form = line.rstrip().split('\t')[0]
            lines = [line]
            lines += [f.readline() for f in autoposlemma_fs[1:]]
            autoposlemmas = [get_pos_lemma(x) for x in lines]
            lemma = vote([x[1] for x in autoposlemmas], ignore_numbers=ignore_numbers)
            for autopos, autolemma in autoposlemmas:
                if autolemma == lemma:
                    pos = autopos
            fout.write(form + '\t' + pos + '\t' + lemma + '\n')
            
    for f in autoposlemma_fs: f.close()

def disambiguate_pos(autoposs, goldposs=[], outfile='out.txt'):
    def get_pos(line):
        try:
            return line.rstrip().split('\t')[1]
        except IndexError:
            return ''
    
    goldpos_f = open(goldposs[0], 'r', encoding='utf-8') if goldposs else None
    # Open the autopos files
    autopos_fs = [open(x, 'r', encoding='utf-8') for x in autoposs]
    # Iterate over first autopos file (always provided)
    with open(outfile, 'w', encoding='utf-8') as fout:
        print(outfile + ' opened')
        for line in autopos_fs[0]:
            form = line.rstrip().split('\t')[0]
            lines = [line]
            lines += [f.readline() for f in autopos_fs[1:]]
            autopostags = [get_pos(x) for x in lines]
            goldpostag = goldpos_f.readline().rstrip().split('\t')[1] if goldpos_f else ''
            autotag = vote(autopostags)
            # Case 1. Unambiguous gold pos
            if not goldpostag and not '|' in goldpostag:
                tag = goldpostag
            # Case 2. Ambiguous gold pos tag which doesn't agree with autotag,
            # Use ambiguous gold tag.
            if goldpostag and not autotag in goldpostag.split('|'):
                tag = goldpostag
            else:
                tag = autotag
            fout.write(form + '\t' + tag + '\n')
    if goldpos_f: goldpos_f.close()
    for autopos_f in autopos_fs: autopos_f.close()
    
def main(
    goldpos=[], goldlemma=[], goldposlemma=[], lookupposlemma=[],
    autopos=[], autoposlemma=[], outfile='out.txt',
    ignore_numbers=False
):
    # Step 1. Sanity check
    if not lookupposlemma and not autoposlemma:
        raise SourceDataError('No source for lemmas provided.')
    if not goldpos and not goldposlemma and not autopos and not autoposlemma:
        raise SourceDataError('No source for pos provided.')
    if (goldpos and goldposlemma) or (goldlemma and goldposlemma):
        raise SourceDataError('Multiple sources for gold annotation provided.')
        
    # Step 2. Create a temporary directory for all intermediate operations
    #with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = '/home/tmr/tmp'
    
    # Step 3. Disambiguate sources of PoS data by creating a single
    # file, pospath
    if autopos or autoposlemma:
        disambiguate_pos(
            autoposs=autopos + autoposlemma,
            goldposs=goldpos + goldposlemma,
            outfile=opj(tmpdir, 'pos.txt')
        )
        posfile = opj(tmpdir, 'pos.txt')
    else:
        posfile = (goldpos + goldposlemma)[0]
    
    # Step 4. Combine automatic lemmatization into a single form - pos -
    # lemma file
    if autoposlemma:
        autolemmafile = opj(tmpdir, 'autoposlemma.txt')
        disambiguate_autoposlemma(autoposlemma, outfile=autolemmafile, ignore_numbers=ignore_numbers)
    else:
        autolemmafile = ''
        
        
    # Step 5. Load lexicon files
    if lookupposlemma:
        l = [parse_lexicon(x, ignore_numbers=ignore_numbers) for x in lookupposlemma]
        lemma_d, pos_d = l[0][0], l[0][1]
        for xlemma_d, xpos_d in l[1:]:
            pos_d.update({key: pos_d.get(key, []) + xpos_d[key] for key in xpos_d})
            lemma_d.update({key: lemma_d.get(key, []) + xlemma_d[key] for key in xlemma_d})
    else:
        pos_d, lemma_d = {}, {}
        
    # Step 6. Open the files and begin iteration
    autolemma_f = open(autolemmafile, 'r', encoding='utf-8') if autolemmafile else None
    goldposlemma_f = open(goldposlemma[0], 'r', encoding='utf-8') if goldposlemma else None
    with open(posfile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            for line in fin:
                line_list = line.rstrip().split('\t') # Read the line
                form = line_list[0] # Get the form
                try:
                    poss = line_list[1].split('|') # Get the pos list
                except IndexError:
                    poss = []
                if autolemma_f: # Get the (list of) autolemmas
                    al_line = autolemma_f.readline().rstrip()
                    try:
                        autolemmas = al_line.split('\t')[2].split('|')
                    except IndexError:
                        autolemmas = []
                if goldposlemma_f: # Get the (list of) gold lemmas
                    gpl_line = goldposlemma_f.readline().rstrip()
                    try:
                        goldlemmas = gpl_line.split('\t')[2].split('|')
                    except IndexError:
                        goldlemmas = []
                if lookupposlemma:
                    lookup_lemmas = lemma_d.get(form, [])
                    lookup_poss = pos_d.get(form, [])
                else:
                    lookup_lemmas, lookup_poss = [], []
                lemma, score = score_lemmas(poss, goldlemmas, autolemmas, lookup_lemmas, lookup_poss)
                fout.write('\t'.join([form, lemma, str(score)]) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Script to lemmatize a file based on multiple sources.'
    )
    parser.add_argument('--goldpos', nargs=1, help='Gold form tab pos file.', default=[])
    parser.add_argument('--goldlemma', nargs=1, help='Gold form tab lemma file.', default=[])
    parser.add_argument('--goldposlemma', nargs=1, help='Gold form tab pos tab lemma file.', default=[])
    parser.add_argument('--lookupposlemma', nargs='*', help='Lexicon-based form tab pos tab lemma files.', default=[])
    parser.add_argument('--autopos', nargs='*', help='Automated form tab pos file.', default=[])
    parser.add_argument('--autoposlemma', nargs='*', help='Automated form tab pos tab lemma file.', default=[])
    parser.add_argument('--ignore_numbers', help='Ignores numbers after lemma forms.', action='store_true')
    parser.add_argument('outfile', help='Output text file.', nargs='?', default='out.txt')
    kwargs = vars(parser.parse_args())
    print(kwargs)
    main(**kwargs)

