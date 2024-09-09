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

import argparse, subprocess, os.path, tempfile, shutil, textwrap
from lib.normalizers import Normalizer
from lib.concat import Concatenater
import scripts.ofrpostprocess
import scripts.standardizepos
import scripts.lemmacompare
import scripts.convertfiles
import scripts.rnntag

opj = os.path.join


def normalize_infile(infile, outfile):
    # Removes all annotation.
    # Removes all punctuation within tokens except apostrophes and hyphens,
    # except for Old French numbers
    # Return max number of columns.
    normalizer = Normalizer(pnc_in_tok=False)
    #normalizer.pnc_in_tok_except.extend(['@', '#']) # Used in MCVF
    with open(infile, 'r', encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            l = []
            for line in fin:
                x = line.rstrip().split('\t')
                l.append(len(x))
                if not x[0]: # empty line will split to give a list with an empty string
                    fout.write('\n') # Empty line
                else:
                    if not x[0][0] == '.' and not x[0][-1] == '.': # don't normalize numbers
                        x[0] = normalizer.normalize_tok(x[0])
                    fout.write(x[0] + '\n')
    return max(l)

def main(tmpdir, infiles=[], rnnpath='', ttpath='', lexicons=[], outfile='', outdir='', inputanno='gold', printunk=False):
    
    script_path = os.path.dirname(__file__)
    # -1. Run the converter and store converters
    print('Converting and concatenating input files.')
    converters, converted_infiles = [], []
    for infile in infiles:
        if os.path.splitext(infile)[1] not in ['', '.txt', '.tsv']:
            converter = scripts.convertfiles.get_converter(infile)
            converters.append(converter)
            converted_infiles.append(opj(tmpdir, os.path.basename(infile + '.txt')))
            converter.from_source(converted_infiles[-1])
        else:
            converted_infiles.append(infile)
            converters.append(None)
    
    # 0. Concatenate input files
    catfile = opj(tmpdir, 'cat.txt')
    concatenater = Concatenater()
    concatenater.concatenate(converted_infiles, catfile)
    max_cols = normalize_infile(catfile, opj(tmpdir, 'basefile.txt'))
    # 1. Standardize gold pos tags from input file
    if max_cols > 1:
        print('Converting input part-of-speech tags to UD.')
        try:
            scripts.standardizepos.main(catfile, opj(tmpdir, 'infile_normed.txt'))
        except scripts.standardizepos.MapNotFound:
            print("Warning: Couldn't standardize pos. Assuming already in UD.")
            shutil.copy(catfile, opj(tmpdir, 'infile_normed.txt'))
    taggerouts = []
    # 2. Call RNN tagger
    for lang, fname in [('old-french', 'rnn_of.txt')]:#, ('middle-french', 'rnn_midf.txt')]:
    # Updated for RNN Tagger v. 1.4.7
    # Still performs better with just the Old French model.
    #lang, fname = 'middle-french', 'rnn.txt'
        if rnnpath: # Inherit venv; call script
            print('Calling the RNN Tagger')
            scripts.rnntag.main(rnnpath, lang, [opj(tmpdir, 'basefile.txt')],
                outfile=opj(tmpdir, fname))
            taggerouts.append(opj(tmpdir, fname))
        elif os.path.exists(opj(tmpdir, fname)):
            print('Using RNN tags from ' + opj(tmpdir, fname))
            print("(Move this file or give --rnnpath to disable this.)")
            taggerouts.append(opj(tmpdir, fname))
            rnnpath = 'yes'
    # 2b. Call the Tree Tagger
    if rnnpath and ttpath:
        print('WARNING: Tests suggest that better results are achieved with the RNN Tagger alone.')
    if ttpath:
        # BFM fro model
        args = [
            opj(script_path, 'tree-tag.py'),
            ttpath, '--lang', 'old-french', '--infiles', opj(tmpdir, 'basefile.txt'),
            '--outfile', opj(tmpdir, 'tt-fro.txt')
        ]
        print('Calling the TreeTagger (fro model).')
        process = subprocess.run(args)
        if process.returncode == 0:
            taggerouts.append(opj(tmpdir, 'tt-fro.txt'))
        # Stein OF model (in TreeTagger root dir)
        args = [
            opj(script_path, 'tree-tag.py'),
            ttpath, '--parpath', opj(ttpath, 'stein-oldfrench.par'),
            '--infiles', opj(tmpdir, 'basefile.txt'),
            '--outfile', opj(tmpdir, 'tt-stein.txt')
        ]
        print('Calling the TreeTagger (Stein model).')
        process = subprocess.run(args)
        if process.returncode == 0:
            taggerouts.append(opj(tmpdir, 'tt-stein.txt'))
    # 3. Standardize pos tags
    print(taggerouts)
    for i, taggerout in enumerate(taggerouts):
        print('Converting part-of-speech tags from the tagger to UD.')
        new_taggerout = taggerout[:-4] + '_normed.txt'
        try:
            scripts.standardizepos.main(taggerout, new_taggerout)
        except scripts.standardizepos.MapNotFound:
            print("Warning: Couldn't standardize pos. Assuming already in UD.")
            shutil.copy(taggerout, new_taggerout)
        taggerouts[i] = new_taggerout
        
    if lexicons:
    #if False:
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
    if max_cols == 2 and inputanno == 'gold':
        kwargs['goldpos'] = opj(tmpdir, 'infile_normed.txt')
    if max_cols == 3 and inputanno == 'gold':
        kwargs['goldposlemma'] = opj(tmpdir, 'infile_normed.txt')
    if max_cols == 2 and inputanno == 'auto':
        kwargs['autopos'] = [opj(tmpdir, 'infile_normed.txt')]
    kwargs['autoposlemma'] = []
    if max_cols == 3 and inputanno == 'auto':
        kwargs['autoposlemma'].append(opj(tmpdir, 'infile_normed.txt'))
    if rnnpath:
        kwargs['autoposlemma'].append(taggerouts.pop(0))
        #kwargs['autoposlemma'].append(taggerouts.pop(0)) # mf model
    if ttpath and taggerouts:
        kwargs['autopos'] = taggerouts[:]
    if lexicons:
    #if False:
        kwargs['lookupposlemma'] = [opj(tmpdir, 'lookup_normed' + str(i) + '.txt') for i in range(len(lexicons))]
        kwargs['lexicons'] = [x for x in lexicons]
    print('Comparing results and scoring final lemmatization.')
    #print(kwargs)
    scripts.lemmacompare.main(**kwargs)
    # 7. Post process
    print('Running post-processor.')
    unks = scripts.ofrpostprocess.main(opj(tmpdir, 'out.txt'), opj(tmpdir, 'out-pp.txt'))
    if printunk:
        unktups = [(unks.count(x), x) for x in list(set(unks))]
        unktups.sort(key=lambda x: x[0], reverse=True)
        print('Unknown lemmas')
        for freq, lem in unktups:
            print(str(freq) + '\t' + lem)
    
    #shutil.copy2(opj(tmpdir, 'out.txt'), opj(tmpdir, 'out-pp.txt'))
    if outdir or \
    (outfile and len(infiles) == 1 and os.path.splitext(outfile)[1] == os.path.splitext(infiles[0])[1]):
        # Only reconverts files if an outdir is given, or one one infile
        # was given with an outfile with an identical extension.
        print('Splitting and back-converting output to original format.')
        concatenater.split(opj(tmpdir, 'out-pp.txt'), outdir=tmpdir) # overwrites converted infile.
        for converter, converted_infile in zip(converters, converted_infiles):
            print(converter.source_file)
            print(converted_infile)
            if converter:
                if not outfile: # single outfile case must be handled too
                    outfile = opj(outdir, os.path.basename(converter.source_file))
                print(outfile)
                converter.to_source(converted_infile, outfile)
                outfile = ''
            else:
                outfile = outfile or opj(outdir, os.path.basename(converted_infile))
                shutil.copy2(opj(tmpdir, 'out-pp.txt'), outfile)
    elif outfile:
        shutil.copy2(opj(tmpdir, 'out-pp.txt'), outfile)
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
    parser.add_argument('--rnnpath', type=str, help='Path to directory containing the RNN tagger.')
    parser.add_argument('--ttpath', type=str, help=\
        'Path to directory containing the TreeTagger. Directory should contain bin/tree-tagger, ' + \
        'lib/old-french.par and/or stein-oldfrench.par.')
    parser.add_argument('--lexicons', nargs='*', help='Lexicon files (overrides supplied default lexicons)', 
        default=[
            opj(script_path, 'lexicons', 'old-french', 'lgerm', 'lgerm-medieval.tsv'),
            opj(script_path, 'lexicons', 'old-french', 'lgerm-medieval-corrections.tsv'),
            opj(script_path, 'lexicons', 'old-french', 'bfm', 'bfmgoldlem2022.tsv')
            #opj(script_path, 'lexicons', 'punct.tsv')
        ]
    )
    parser.add_argument('--outdir', help='Output directory.', type=str, default='')
    parser.add_argument('--outfile', help='Output file.', type=str, default='')
    parser.add_argument('--tmpdir', help='Directory for temporary files, if you wish to keep them.', type=str, default='')
    parser.add_argument('--inputanno', type=str, default='gold',
        choices=['gold', 'auto', 'ignore'], 
        help=textwrap.dedent('''
            Treat POS annotation and lemmas in the input files as:
            gold        Gold annotation (default).
            auto        Automatic annotation.
            ignore      Ignore it.
            '''
        )
    )
    parser.add_argument('--printunk', action='store_true', help='Print unknown lemmas to screen')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    if kwargs['tmpdir']:
        main(**kwargs)
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            kwargs['tmpdir'] = tmpdir
            main(**kwargs)
    
