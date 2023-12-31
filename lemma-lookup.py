#!/usr/bin/python3

#######################################################################
# Lemmatizes a one-token-per line text file using the forms in a .tsv #
# file. Output is a form pos lemma file.                              #
#######################################################################

## TODO implement sniffer on lexicon file
## TODO normalize fin input on load.

import argparse

from lib.sniffers import FormSniffer
from lib.common import parse_lexicon
            
def main(infile, lexicon, outfile='out.txt'):
    # get normalizers for both files
    # TODO get_normalizers(infile, lexicon)
    lemma_d, pos_d = parse_lexicon(lexicon)
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            for tok in fin:
                tok = tok.lstrip().rstrip() # strip whitespace
                if tok in lemma_d:
                    fout.write(
                        '\t'.join([
                            tok,
                            '\t'.join([x[0] + '\t' + x[1] for x in zip(pos_d[tok], lemma_d[tok])])
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
    parser.add_argument('outfile', help='Output text file.', nargs='?', default='out.txt')
    args = vars(parser.parse_args())
    main(args.pop('infile'), args.pop('lexicon'), args.pop('outfile'))
