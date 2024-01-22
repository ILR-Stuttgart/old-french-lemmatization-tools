#!/usr/bin/python3

import argparse, csv, os, os.path, tempfile
import scripts.convertfiles
from lib.normalizers import Normalizer

opj = os.path.join

def main(infiles, lexicon='out.tsv'):
    forms_d = {}
    if os.path.exists(os.path.abspath(lexicon)):
        with open(lexicon, encoding='utf-8') as f:
            for line in f:
                l = line.rstrip().split('\t')
                if len(l) < 3: continue
                if '|' in l[0]: continue
                forms_d[l[0] + '||' + l[1]] = set(l[2].split('|'))
                
    normalizer = Normalizer(pnc_in_tok=False, uppercase=False) #ignore case in form
    with tempfile.TemporaryDirectory() as tmpdir:
        for fname in infiles:
            try:
                scripts.convertfiles.convert_from_source(fname, opj(tmpdir, 'tmp.txt'), conllu_xpos=True)
            except scripts.convertfiles.UnknownFileType:
                print(fname)
                raise
            with open(opj(tmpdir, 'tmp.txt'), 'r', encoding='utf-8') as f:
                for line in f:
                    l = line.rstrip().split('\t')
                    if len(l) < 3: continue
                    if '|' in l[2] or not l[2] or l[2] == 'UNKNOWN' or not l[1]: continue
                    key = l[2] + '||' + l[1]
                    form = normalizer.normalize_tok(l[0])
                    if key in forms_d:
                        forms_d[key].add(form)
                    else:
                        forms_d[key] = set([form]) 
                        
    with open(lexicon, 'w', encoding='utf-8') as f:
        for key, forms in forms_d.items():
            l = key.split('||')
            f.write(l[0] + '\t')
            f.write(l[1] + '\t')
            l = list(forms)
            l.sort()
            f.write('|'.join(l) + '\n')

if __name__ == '__main__':
    script_path = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Appends forms from input files to a lexicon.'
    )
    parser.add_argument('infiles', nargs='+', help='Input files.')
    parser.add_argument('--lexicon', type=str, help='Lexicon file.', default='out.tsv')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    main(**kwargs)
