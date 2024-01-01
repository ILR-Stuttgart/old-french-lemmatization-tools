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

opj = os.path.join

def normalize_infile(infile, outfile):
    # At the moment, just removes all annotation.
    # Return max number of columns.
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            l = []
            for line in fin:
                x = line.rstrip().split('\t')
                l.append(len(x))
                fout.write(x[0] + '\n')
    return max(l)

def main(infile, rnnpath='', lexicon='', outfile='out.txt'):
    if not rnnpath and not lexicon:
        raise SourceDataError('Nothing to do!')
        
    script_path = os.path.dirname(__file__)
    
    tmpdir = '/home/tmr/tmp'
    max_cols = normalize_infile(infile, opj(tmpdir, 'basefile.txt'))
    #with tempfile.TemporaryDirectory() as tmpdir:
    # 1. Standardize gold pos tags from input file
    if max_cols > 1:
        args = [
            opj(script_path, 'standardize-pos.py'),
            infile, opj(tmpdir, 'infile_normed.txt')
        ]
        print('Standardizing part-of-speech in input file.')
        subprocess.run(args)
    # 2. Call RNN tagger
    if rnnpath:
        args = [
            opj(script_path, 'rnn-tag.py'),
            rnnpath, 'old-french', opj(tmpdir, 'basefile.txt'),
            opj(tmpdir, 'rnn.txt')
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
            opj(tmpdir, 'basefile.txt'), lexicon,
            opj(tmpdir, 'lookup.txt')
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
        '--outfile', outfile
    ]
    if max_cols == 2: args.extend(['--goldpos', infile])
    if max_cols == 3: args.extend(['--goldposlemma', infile])
    if rnnpath: args.extend(['--autoposlemma', opj(tmpdir, 'rnn_normed.txt')])
    if lexicon: args.extend(['--lookupposlemma', opj(tmpdir, 'lookup_normed.txt')])
    print('Comparing results and writing final lemmatization.')
    subprocess.run(args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Old French lemmatizer.'
    )
    parser.add_argument('infile', help='Input text file, one token per line.')
    parser.add_argument('--rnnpath', help='Path to directory containing the RNN tagger.')
    parser.add_argument('--lexicon', help='Lexicon file.')
    parser.add_argument('outfile', help='Output text file.', nargs='?', default='out.txt')
    kwargs = vars(parser.parse_args())
    print(kwargs)
    main(**kwargs)
