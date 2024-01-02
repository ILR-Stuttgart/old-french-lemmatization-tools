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
    for i, form in enumerate(forms):
        if ignore_numbers: # Remove all digits from the string
            s = ''
            for char in form:
                if not char.isdigit():
                    s += char
            forms[i] = s
    forms = [x.split('|') for x in forms]
    #print(forms)
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
        if len(set(lookup_poss[0].split('|')) & set(poss)) == 0:
            score += 1
    # Case 2b. There is a single, unambiguous lemma from the lookup but it doesn't
    # match the autolemma
    elif lookup_lemmas and len(lookup_lemmas) == 1 and autolemmas:
        lemma = lookup_lemmas[0]
        score = 3
        # If the pos tag doesn't match, add 1
        if len(set(lookup_poss[0].split('|')) & set(poss)) == 0:
            score += 1
    # Cases 3 and 4. There are multiple lookup lemmas.
    elif lookup_lemmas:
        # We perform POS disambiguation using the standard tagset, then
        # the two simplified tagsets.
        # Score is incremented by 10 with each simplification of the 
        # tagset.
        for d in [{}, udpos_simplified, udpos_very_simple]:
            lemma_ixs = pos_match(d)
            # Case 3a. Exactly one lookup lemma has the correct POS tag.
            # PoS disambiguation has worked, use this lemma, score is 1
            if len(lemma_ixs) == 1:
                lemma = lookup_lemmas[lemma_ixs[0]]
                score += 1
                # Add 2 to score if there are autolemmas and it doesn't match one
                if autolemmas and not lemma in autolemmas:
                    score += 2
            # Multiple lookup lemmas have the correct PoS tag and there are autolemmas
            elif len(lemma_ixs) > 1 and autolemmas:
                # Do any match the autolemmas?
                aset = set(autolemmas) & set([lookup_lemmas[i] for i in lemma_ixs])
                # Case 3b. Exactly one lookup lemma matches the autolemma.
                # Use the autolemma, score is 10
                if len(aset) == 1:
                    lemma = list(aset)[0]
                    score += 10
                # Case 3c. More than one lookup lemma matches more than one autolemma.
                # Can't resolve; return all lemmas; score = 100 [MUST LOOK AT ME!]
                elif len(aset) > 1:
                    lemma = '|'.join(list(aset))
                    score += 100
                # Case 3d. More than one lookup lemma but nothing matches the autolemma
                # Return the AUTOLEMMA, score 1000 (unverified autolemma)
                else:
                    # Always use list - set in case identical lemmas with the same
                    # POS.
                    lemma = '|'.join(autolemmas)
                    score += 1000
            # Case 3e. Multiple lookup lemmas have the correct PoS tag and there are
            # no autolemmas. Can't resolve; return all lookup lemmas; score = 100
            elif len(lemma_ixs) > 1:
                lemma = '|'.join(list(set([lookup_lemmas[i] for i in lemma_ixs])))
                score += 100
            # If this iteration of pos disambiguation has produced a
            # lemma, break out of the for loop
            if lemma: break
            # Otherwise, increment score by 40 and keep going
            score += 40
        # Case 4. All kinds of PoS disambiguation have failed
        else: # else statement attached to FOR loop.
            if autolemmas: # There are autolemmas
                aset = set(lookup_lemmas) & set(autolemmas)
                # Case 4a. One or more autolemmas matches the lookup_lemmas.
                # Use the autolemma but give it a score of 20 (for one)
                # or 120 (for more than one) (autolemma disambiguation)
                if aset:
                    lemma = '|'.join(list(aset))
                    score = 20 if len(aset) == 1 else 120
                # Case 4c. No autolemma matches the lookup lemmas.
                # Can't resolve: return the AUTOLEMMA with a score of
                # 1000
                else:
                    lemma = '|'.join(autolemmas)
                    score = 1000
            # There are no autolemmas and pos_disambiguation has failed.
            # Return all lookup lemmas, with score of 120
            else:
                lemma = '|'.join(lookup_lemmas)
                score = 120
    # Case 5. No goldlemmas and no lookup lemmas, just autolemmas.
    # Return the autolemma with a score of 1000 (uncrosschecked autolemmas)
    elif autolemmas: # Attached to main if statement in module
        lemma = '|'.join(autolemmas)
        score = 1000
    # Case 6. No gold lemmas, no lookup lemmas, no autolemmas, so, er...
    # no lemmas then.
    else:
        lemma = 'UNKNOWN'
        score = 2000
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
    
def main(
    goldpos=[], goldlemma=[], goldposlemma=[], lookupposlemma=[],
    autopos=[], autoposlemma=[], outfile=['out.txt'],
    ignore_numbers=False
):
    outfile = outfile[0]
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
        
    # Step 5. Open the files and begin iteration
    autolemma_f = open(autolemmafile, 'r', encoding='utf-8') if autolemmafile else None
    goldposlemma_f = open(goldposlemma[0], 'r', encoding='utf-8') if goldposlemma else None
    lookupposlemma_f = open(lookupposlemma[0], 'r', encoding='utf-8') if lookupposlemma else None
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
                lookup_poss, lookup_lemmas = [], []
                if lookupposlemma_f:
                    lpl_line = lookupposlemma_f.readline().rstrip().split('\t')
                    lookup_poss, lookup_lemmas, i = [], [], 1
                    while i < len(lpl_line):
                        lookup_poss.append(lpl_line[i])
                        lookup_lemmas.append(lpl_line[i + 1])
                        i += 2
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
    parser.add_argument('--lookupposlemma', nargs=1, help='Lexicon-based form tab pos tab lemma files.', default=[])
    parser.add_argument('--autopos', nargs='*', help='Automated form tab pos file.', default=[])
    parser.add_argument('--autoposlemma', nargs='*', help='Automated form tab pos tab lemma file.', default=[])
    parser.add_argument('--ignore_numbers', help='Ignores numbers after lemma forms.', action='store_true')
    parser.add_argument('--outfile', help='Output text file.', nargs=1, default=['out.txt'])
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    main(**kwargs)

