#!/usr/bin/python3

#######################################################################
# Lemmatizes a one-token-per line text file using the forms in a .tsv #
# file. Output is a form pos lemma file.                              #
#######################################################################

## TODO implement sniffer on lexicon file
## TODO normalize fin input on load.

import argparse

from lib.sniffers import FormSniffer

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

            
def main(infile, lexicon, outfile='out.txt', ignore_numbers=False):
    # get normalizers for both files
    # TODO get_normalizers(infile, lexicon)
    lemma_d, pos_d = parse_lexicon(lexicon, ignore_numbers=ignore_numbers)
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            for tok in fin:
                tok = tok.lstrip().rstrip() # strip whitespace
                if tok in lemma_d:
                    fout.write(
                        '\t'.join([
                            tok,
                            # list - set - zip removes lemma doublets, which 
                            # can arise when ignore_numbers = True.
                            '\t'.join([x[0] + '\t' + x[1] for x in list(set(zip(pos_d[tok], lemma_d[tok])))])
                        ])
                    )
                else:
                    fout.write(tok)
                fout.write('\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Lemmatizes a one-token-per line text file using the forms in a ' + \
        '.tsv file.'
    )
    parser.add_argument('infile', help='Input text file.')
    parser.add_argument('lexicon', help='Lexicon file.')
    parser.add_argument('--ignore_numbers', help='Ignores numbers after lemma forms.', action='store_true')
    parser.add_argument('outfile', help='Output text file.', nargs='?', default='out.txt')
    args = vars(parser.parse_args())
    main(args.pop('infile'), args.pop('lexicon'), args.pop('outfile'), args.pop('ignore_numbers'))
