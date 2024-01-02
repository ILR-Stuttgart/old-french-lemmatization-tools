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

import argparse, subprocess, os.path, tempfile
from lib.normalizers import Normalizer
from lib.concat import Concatenater

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

def main(infiles=[], rnnpath='', lexicon='', outfile='', outdir=''):
    if (not rnnpath and not lexicon) or not infiles:
        raise SourceDataError('Nothing to do!')
        
    script_path = os.path.dirname(__file__)
    
    #tmpdir = '/home/tmr/tmp'
    with tempfile.TemporaryDirectory() as tmpdir:
        catfile = opj(tmpdir, 'cat.txt')
        concatenater = Concatenater()
        concatenater.concatenate(infiles, catfile)
        max_cols = normalize_infile(catfile, opj(tmpdir, 'basefile.txt'))
        # 1. Standardize gold pos tags from input file
        if max_cols > 1:
            args = [
                opj(script_path, 'standardize-pos.py'),
                catfile, opj(tmpdir, 'infile_normed.txt')
            ]
            print('Standardizing part-of-speech in input file.')
            subprocess.run(args)
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
            args = [
                opj(script_path, 'standardize-pos.py'),
                opj(tmpdir, 'rnn.txt'),
                opj(tmpdir, 'rnn_normed.txt')
            ]
            print('Standardizing part-of-speech from the RNN tagger.')
            subprocess.run(args)
        if lexicon:
            # 4. Call lemma lookup on lexicon file
            args = [
                opj(script_path, 'lemma-lookup.py'), '--ignore_numbers',
                lexicon, '--infiles', opj(tmpdir, 'basefile.txt'), 
                '--outfile', opj(tmpdir, 'lookup.txt')
            ]
            print('Lemmatizing using the lexicon file.')
            subprocess.run(args)
            # 5. Standardize pos tags
            args = [
                opj(script_path, 'standardize-pos.py'),
                opj(tmpdir, 'lookup.txt'),
                opj(tmpdir, 'lookup_normed.txt')
            ]
            print('Standardizing part-of-speech from the lexicon file.')
            subprocess.run(args)
        # 6. Run lemma comparison
        args = [
            opj(script_path, 'lemma-compare.py'), '--ignore_numbers',
            '--outfile', opj(tmpdir, 'out.txt')
        ]
        if max_cols == 2: args.extend(['--goldpos', infile])
        if max_cols == 3: args.extend(['--goldposlemma', infile])
        if rnnpath: args.extend(['--autoposlemma', opj(tmpdir, 'rnn_normed.txt')])
        if lexicon: args.extend(['--lookupposlemma', opj(tmpdir, 'lookup_normed.txt')])
        print('Comparing results and writing final lemmatization.')
        subprocess.run(args)
        if outdir:
            concatenater.split(opj(tmpdir, 'out.txt'), outdir=outdir)
        elif outfile:
            shutil.copy2(opj(tmpdir, 'out.txt'), user_outfile)
        else: # Nowhere else to dump the output, print it to stdout.
            with open(opj(tmpdir, 'out.txt'), 'r', encoding='utf-8') as f:
                for line in f:
                    print(line[:-1])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Old French lemmatizer.'
    )
    parser.add_argument('--infiles', nargs='+', help='Input text file.')
    parser.add_argument('--rnnpath', help='Path to directory containing the RNN tagger.')
    parser.add_argument('--lexicon', help='Lexicon file.')
    parser.add_argument('--outdir', help='Output directory.', type=str, default='')
    parser.add_argument('--outfile', help='Output file.', type=str, default='')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    main(**kwargs)
