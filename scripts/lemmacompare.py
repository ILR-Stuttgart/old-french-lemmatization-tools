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

opj = os.path.join

udpos_simplified = { # Removes INTJ, PROPN, AUX, DET, NUM, PART, SYM tags
    'ADJ': 'ADJ', 'ADV': 'ADV', 'INTJ': 'ADV', 'NOUN': 'NOUN',
    'PROPN': 'NOUN', 'VERB': 'VERB', 'ADP': 'ADP', 'AUX': 'VERB',
    'CCONJ': 'CCONJ', 'DET': 'ADJ', 'NUM': 'ADJ', 
    'PART': 'ADV', 'PRON': 'PRON', 'SCONJ': 'SCONJ',
    'PUNCT': 'PUNCT', 'SYM': 'PUNCT', 'X': 'X'
}

udpos_very_simple = { # Simplifies to FNC / LEX tags

    'ADJ': 'LEX', 'ADV': 'LEX', 'INTJ': 'LEX', 'NOUN': 'LEX', 
    'PROPN': 'LEX', 'VERB': 'LEX', 'ADP': 'FNC', 'AUX': 'LEX',
    'CCONJ': 'FNC', 'DET': 'FNC', 'NUM': 'FNC', 'PART': 'FNC',
    'PRON': 'FNC', 'SCONJ': 'FNC', 'PUNCT': 'PUNCT', 'SYM': 'PUNCT',
    'X': 'X'

}

def vote(forms, ignore_numbers=False):
    while '' in forms: forms.remove('') # Remove all empty strings
    if not forms: return '' # If only empty strings were offered, return empty string
    l = []
    for i, form in enumerate(forms):
        s = ''
        for char in form:
            if not ignore_numbers or not char.isdigit():
                s += char
        forms[i] = s
    #print(forms)
    forms = [x.split('|') for x in forms]
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
    #print(goldlemmas, autolemmas, lookup_lemmas, lookup_poss)
    # Guide to scores attributed
    # -1: more than one option.
    # 0: autolemma which contradicts the lookup lemma
    # 1: unverifiable autolemma
    # 2: single lookup lemma, unverified by tagging
    # 3: multiple lookup lemmas, pos disambiguation fails but one does match the autolemma(s)
    # 4: single lookup lemma, doesn't match the pos but does match the autolemma(s)
    # 5: multiple lookup lemmas, pos_disambiguated but doesn't match the autolemma
    # 6: single lookup lemma, pos matches but the autolemma doesn't
    # 7: multiple lookup lemmas, simplified pos_disambiguated and matches the autolemma(s)
    # 8: multiple lookup lemmas, pos_disambiguated and matches the autolemma(s)
    # 9: single lookup lemma which matches the pos and the autolemma(s)
    # 10: gold lemma
    
    def pos_match(simplify = {}):
        nonlocal lookup_poss, poss
        # Now, work out which lookup lemmas have the correct POS tag (simple mode)
        lemma_ixs = []
        set2 = set([simplify.get(x, x) for x in poss])
        for i, lookup_pos in enumerate(lookup_poss):
            # Simplify the pos tags using the passed dictionary
            set1 = set([simplify.get(x, x) for x in lookup_pos.split('|')])
            if set1 & set2: # PoS match for this lemma
                lemma_ixs.append(i)
        return(lemma_ixs)
        
    lemma, score = '', 0
    # Case 1. There is a gold lemma. Score 10.
    # Note that gold lemmas shouldn't be ambiguous...
    if goldlemmas:
        lemma = '|'.join(goldlemmas)
        score = 10
    # Case 2a. There is a single, unambiguous lemma from the lookup which 
    # matches the autolemma.
    elif lookup_lemmas and len(lookup_lemmas) == 1 and lookup_lemmas[0] in autolemmas:
        lemma = lookup_lemmas[0]
        # If the lookup_lemma part of speech tag doesn't match, score is 4, else 9
        if len(set(lookup_poss[0].split('|')) & set(poss)) == 0:
            score = 4
        else:
            score = 9
    # Case 2b. There is a single, unambiguous lemma from the lookup but it doesn't
    # match the autolemma
    elif lookup_lemmas and len(lookup_lemmas) == 1 and autolemmas:
        lemma = lookup_lemmas[0]
        # If the pos tag doesn't match, either, score is 2. Else 6
        if len(set(lookup_poss[0].split('|')) & set(poss)) == 0:
            score = 2
        else:
            score = 6
    # Cases 3 and 4. There are multiple lookup lemmas.
    elif lookup_lemmas:
        # We perform POS disambiguation using the standard tagset, then
        # the two simplified tagsets.
        for i, d in enumerate([{}, udpos_simplified, udpos_very_simple]):
            lemma_ixs = pos_match(d)
            # Case 3a. Exactly one lookup lemma has the correct POS tag.
            # PoS disambiguation has worked, use this lemma, score is 1
            if len(lemma_ixs) == 1:
                lemma = lookup_lemmas[lemma_ixs[0]]
                # Score is 5 if there are autolemmas and it doesn't match one,
                # otherwise 8 if i == 0 or 7 if i > 0
                if autolemmas and not lemma in autolemmas:
                    score = 5
                elif i == 0:
                    score = 8
                else:
                    score = 7
            # Multiple lookup lemmas have the correct PoS tag and there are autolemmas
            elif len(lemma_ixs) > 1 and autolemmas:
                # Do any match the autolemmas?
                aset = set(autolemmas) & set([lookup_lemmas[i] for i in lemma_ixs])
                # Case 3b. Exactly one lookup lemma matches the autolemma.
                # Use the autolemma, score is 10
                if len(aset) == 1:
                    lemma = list(aset)[0]
                    score = 3
                # Case 3c. More than one lookup lemma matches more than one autolemma.
                # Can't resolve; return all lemmas; score = 0 [MUST LOOK AT ME!]
                elif len(aset) > 1:
                    lemma = '|'.join(list(aset))
                    score = -1
                # Case 3d. More than one lookup lemma but nothing matches the autolemma
                # Return the AUTOLEMMA, score 0 (unverified autolemma)
                else:
                    # Always use list - set in case identical lemmas with the same
                    # POS.
                    lemma = '|'.join(autolemmas)
                    score = 0 if len(autolemmas) == 1 else -1
            # Case 3e. Multiple lookup lemmas have the correct PoS tag and there are
            # no autolemmas. Can't resolve; return all lookup lemmas; score = -1
            elif len(lemma_ixs) > 1:
                lemma = '|'.join(list(set([lookup_lemmas[i] for i in lemma_ixs])))
                score = -1
            # If this iteration of pos disambiguation has produced a
            # lemma, break out of the for loop
            if lemma: break
        # Case 4. All kinds of PoS disambiguation have failed
        else: # else statement attached to FOR loop.
            if autolemmas: # There are autolemmas
                aset = set(lookup_lemmas) & set(autolemmas)
                # Case 4a. One or more autolemmas matches the lookup_lemmas.
                # Use the autolemma. Score = 3 if only one matches the autolemma,
                # else -1 (ambiguous)
                if aset:
                    lemma = '|'.join(list(aset))
                    score = 3 if len(aset) == 1 else -1
                # Case 4c. No autolemma matches the lookup lemmas.
                # Can't resolve: return the AUTOLEMMA with a score of
                # 0
                else:
                    lemma = '|'.join(autolemmas)
                    score = 0 if len(autolemmas) == 1 else -1
            # There are no autolemmas and pos_disambiguation has failed.
            # Return all lookup lemmas, with score of -1
            else:
                lemma = '|'.join(lookup_lemmas)
                score = -1
    # Case 5. No goldlemmas and no lookup lemmas, just autolemmas.
    # Return the autolemma with a score of 1000 (uncrosschecked autolemmas)
    elif autolemmas: # Attached to main if statement in module
        lemma = '|'.join(autolemmas)
        score = 0 if len(autolemmas) == 1 else -1
    # Case 6. No gold lemmas, no lookup lemmas, no autolemmas, so, er...
    # no lemmas then. Score is -2.
    else:
        lemma = 'UNKNOWN'
        score = -2
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
                if lemma == autolemma:
                    pos = autopos
            try:
                fout.write(form + '\t' + pos + '\t' + lemma + '\n')
            except:
                print(form)
                print(line)
                print(lemma)
                print(autoposlemmas)
                raise
            
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
        #print(outfile + ' opened')
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
    
def load_lexicons(lexicons, ignore_numbers=False):
    aset = set([])
    for lexicon in lexicons:
        with open(lexicon, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    x = line.split('\t')[0]
                except IndexError:
                    continue
                if ignore_numbers and x[-1].isdigit():
                    x = x[:-1] # remove number
                aset.add(x)
    #print(list(aset)[:100])
    return aset
    
def main(
    goldpos='', goldposlemma='', lookupposlemma=[],
    autopos=[], autoposlemma=[], outfile='out.txt',
    ignore_numbers=False, lexicons=[]
):
    # Step 1. Sanity check
    if not lookupposlemma and not autoposlemma:
        raise SourceDataError('No source for lemmas provided.')
    if not goldpos and not goldposlemma and not autopos and not autoposlemma:
        raise SourceDataError('No source for pos provided.')
    if goldpos and goldposlemma:
        raise SourceDataError('Multiple sources for gold annotation provided.')
        
    # Step 2. Create a temporary directory for all intermediate operations
    #with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = '/home/tmr/tmp'
    
    # Step 3. Disambiguate sources of PoS data by creating a single
    # file, pospath
    goldposs = [goldpos, goldposlemma]
    while '' in goldposs: goldposs.remove('')
    if autopos or autoposlemma:
        disambiguate_pos(
            autoposs=autopos + autoposlemma,
            goldposs=goldposs,
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
        
    # Step 5. Load lexicon file for list of available lemmas
    if lexicons:
        attested_lemmas = load_lexicons(lexicons, ignore_numbers)
    else:
        attested_lemmas = None
        
    # Step 5. Open the files and begin iteration
    autolemma_f = open(autolemmafile, 'r', encoding='utf-8') if autolemmafile else None
    goldposlemma_f = open(goldposlemma, 'r', encoding='utf-8') if goldposlemma else None
    lookupposlemma_fs = [open(x, 'r', encoding='utf-8') for x in lookupposlemma]
    with open(posfile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            for line in fin:
                line_list = line.rstrip().split('\t') # Read the line
                form = line_list[0] # Get the form
                try:
                    poss = line_list[1].split('|') # Get the pos list
                except IndexError:
                    poss = []
                autolemmas = []
                if autolemma_f: # Get the (list of) autolemmas
                    al_line = autolemma_f.readline().rstrip()
                    try:
                        autolemmas = al_line.split('\t')[2].split('|')
                    except IndexError:
                        pass
                goldlemmas = []
                if goldposlemma_f: # Get the (list of) gold lemmas
                    gpl_line = goldposlemma_f.readline().rstrip()
                    try:
                        goldlemmas = gpl_line.split('\t')[2].split('|')
                    except IndexError:
                        pass
                    if ignore_numbers:
                        # strip digits from gold lemmas too
                        goldlemmas = [x[:-1] if x[-1].isdigit() else x for x in goldlemmas]
                lookup_poss, lookup_lemmas = [], []
                if lookupposlemma_fs:
                    lookup_poss, lookup_lemmas = [], []
                    for lookupposlemma_f in lookupposlemma_fs:
                        lpl_line = lookupposlemma_f.readline().rstrip().split('\t')
                        i = 1
                        while i < len(lpl_line):
                            lookup_poss.append(lpl_line[i])
                            lookup_lemmas.append(lpl_line[i + 1])
                            i += 2
                    if lookup_poss:
                        # If nothing is found, the following commands
                        # which eliminate all duplicate values will
                        # fail at the unzip stage to x, y.
                        x, y = list(zip(*set(zip(lookup_poss, lookup_lemmas))))
                        lookup_poss, lookup_lemmas = list(x), list(y)
                lemma, score = score_lemmas(poss, goldlemmas, autolemmas, lookup_lemmas, lookup_poss)
                if attested_lemmas and not '|' in lemma and not lemma in attested_lemmas and score != 10:
                    # This autolemma is not in the lexicon. Give it a score of -10.
                    # Unless it's already a gold lemma and has a score of 10.
                    score = -10
                fout.write('\t'.join([form, '|'.join(poss), lemma, str(score)]) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Script to lemmatize a file based on multiple sources.'
    )
    parser.add_argument('--goldpos', type=str, help='Gold form tab pos file.', default='')
    parser.add_argument('--goldposlemma', type=str, help='Gold form tab pos tab lemma file.', default='')
    parser.add_argument('--lookupposlemma', nargs='*', help='Lexicon-based form tab pos tab lemma files.', default=[])
    parser.add_argument('--autopos', nargs='*', help='Automated form tab pos file.', default=[])
    parser.add_argument('--autoposlemma', nargs='*', help='Automated form tab pos tab lemma file.', default=[])
    parser.add_argument('--ignore_numbers', help='Ignores numbers after lemma forms.', action='store_true')
    parser.add_argument('--outfile', type=str, help='Output text file.', default='out.txt')
    parser.add_argument('--lexicons', help='Lexicon files with all attested lemmas.', nargs='*', default=[])
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    main(**kwargs)

