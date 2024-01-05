#!/usr/bin/python3

#######################################################################
# Old French Lemmatizer.                                              #
# Calls full workflow:                                                #
# 1. standardizes gold POS tags from input file (if present)          #
# 2. calls RNN tagger on input file for autolemmas                    #
# 3. standardizes POS tags from RNN tagger                            #
# 4. calls lemma lookup on ATILF .tsv file                            #
# 5. standardizes POS tags from lemma lookup                          #
# 6. runs lemma comparison                                            #
#######################################################################

class Error(Exception):
    pass
    
class SourceDataError(Error):
    pass

import argparse, subprocess, os.path, tempfile, shutil
from lib.normalizers import Normalizer
from lib.concat import Concatenater
import scripts.ofrpostprocess
import scripts.standardizepos
import scripts.lemmacompare

opj = os.path.join

def normalize_infile(infile, outfile):
    # Removes all annotation.
    # Removes all punctuation within tokens except apostrophes and hyphens,
    # except for Old French numbers
    # Return max number of columns.
    normalizer = Normalizer(pnc_in_tok=False)
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            l = []
            for line in fin:
                x = line.rstrip().split('\t')
                l.append(len(x))
                if not x:
                    fout.write('\n') # Empty line
                else:
                    if not x[0][0] == '.' and not x[0][-1] == '.': # don't normalize numbers
                        x[0] = normalizer.normalize_tok(x[0])
                    fout.write(x[0] + '\n')
    return max(l)

def main(tmpdir, infiles=[], rnnpath='', lexicons=[], outfile='', outdir=''):
    
    script_path = os.path.dirname(__file__)
    
    catfile = opj(tmpdir, 'cat.txt')
    concatenater = Concatenater()
    concatenater.concatenate(infiles, catfile)
    max_cols = normalize_infile(catfile, opj(tmpdir, 'basefile.txt'))
    # 1. Standardize gold pos tags from input file
    if max_cols > 1:
        print('Converting gold part-of-speech tags to UD.')
        try:
            scripts.standardizepos.main(catfile, opj(tmpdir, 'infile_normed.txt'))
        except scripts.standardizepos.MapNotFound:
            print("Warning: Couldn't standardize pos. Assuming already in UD.")
            shutil.copy(catfile, opj(tmpdir, 'infile_normed.txt'))
    # 2. Call RNN tagger
    if rnnpath:
        args = [
            opj(script_path, 'rnn-tag.py'),
            rnnpath, 'old-french', '--infiles', opj(tmpdir, 'basefile.txt'),
            '--outfile', opj(tmpdir, 'rnn.txt')
        ]
        print('Calling the RNN tagger.')
        subprocess.run(args)
        # 3. Standardize pos tags
        print('Converting part-of-speech tags from the RNN tagger to UD.')
        try:
            scripts.standardizepos.main(opj(tmpdir, 'rnn.txt'), opj(tmpdir, 'rnn_normed.txt'))
        except scripts.standardizepos.MapNotFound:
            print("Warning: Couldn't standardize pos. Assuming already in UD.")
            shutil.copy(opj(tmpdir, 'rnn.txt'), opj(tmpdir, 'rnn_normed.txt'))
    if lexicons:
        # 4. Call lemma lookup on each lexicon file
        print('Lemmatizing using lexicon files and converting PoS tags to UD.')
        for i, lexicon in enumerate(lexicons):
            args = [
                opj(script_path, 'lemma-lookup.py'), '--ignore_numbers',
                lexicon, '--infiles', opj(tmpdir, 'basefile.txt'), 
                '--outfile', opj(tmpdir, 'lookup' + str(i) + '.txt')
            ]
            subprocess.run(args)
            # 5. Standardize pos tags
            try:
                scripts.standardizepos.main(
                    opj(tmpdir, 'lookup' + str(i) + '.txt'),
                    opj(tmpdir, 'lookup_normed' + str(i) + '.txt')
                )
            except scripts.standardizepos.MapNotFound:
                print("Warning: Couldn't standardize pos. Assuming already in UD.")
                shutil.copy(
                    opj(tmpdir, 'lookup' + str(i) + '.txt'),
                    opj(tmpdir, 'lookup_normed' + str(i) + '.txt')
                )
    # 6. Run lemma comparison
    kwargs = {
        'ignore_numbers': True,
        'outfile': opj(tmpdir, 'out.txt')
    }
    if max_cols == 2: kwargs['goldpos'] =  infile
    if max_cols == 3: kwargs['goldposlemma'] = infile
    if rnnpath: kwargs['autoposlemma'] = opj(tmpdir, 'rnn_normed.txt')
    if lexicons:
        kwargs['lookupposlemma'] = [opj(tmpdir, 'lookup_normed' + str(i) + '.txt') for i in range(len(lexicons))]
        kwargs['lexicons'] = [x for x in lexicons]
    print('Comparing results and scoring final lemmatization.')
    scripts.lemmacompare.main(**kwargs)
    # 7. Post process
    print('Running post-processor.')
    scripts.ofrpostprocess.main(opj(tmpdir, 'out.txt'), opj(tmpdir, 'out-pp.txt'))
    if outdir:
        concatenater.split(opj(tmpdir, 'out-pp.txt'), outdir=outdir)
    elif outfile:
        shutil.copy2(opj(tmpdir, 'out-pp.txt'), user_outfile)
    else: # Nowhere else to dump the output, print it to stdout.
        with open(opj(tmpdir, 'out-pp.txt'), 'r', encoding='utf-8') as f:
            for line in f:
                print(line[:-1])
    
if __name__ == '__main__':
    script_path = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Old French lemmatizer.'
    )
    parser.add_argument('infiles', nargs='+', help='Input text files.')
    parser.add_argument('--rnnpath', help='Path to directory containing the RNN tagger.')
    parser.add_argument('--lexicons', nargs='*', help='Lexicon files (overrides supplied default lexicons)', 
        default=[
            opj(script_path, 'lexicons', 'old-french', 'lgerm-medieval.tsv'),
            opj(script_path, 'lexicons', 'punct.tsv')
        ]
    )
    parser.add_argument('--outdir', help='Output directory.', type=str, default='')
    parser.add_argument('--outfile', help='Output file.', type=str, default='')
    parser.add_argument('--tmpdir', help='Directory for temporary files, if you wish to keep them.', type=str, default='')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    if kwargs['tmpdir']:
        main(**kwargs)
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            kwargs['tmpdir'] = tmpdir
            main(**kwargs)
    
