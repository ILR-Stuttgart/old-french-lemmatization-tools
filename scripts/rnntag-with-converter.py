#!/usr/bin/python3

#######################################################################
# Old French RNN.                                                     #
# Wrapper for the RNN Tagger for Old French texts                     #
# 1. Converts input files to the format required by the RNN tagger    #
# 2. calls RNN tagger on input file for autolemmas.                   #
# 3. Converts files back to the original format.                      #
#######################################################################

class Error(Exception):
    pass
    
class SourceDataError(Error):
    pass

import argparse, subprocess, os.path, tempfile, shutil, textwrap
from lib.normalizers import Normalizer
from lib.concat import Concatenater
import convertfiles
import rnntag

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

def main(tmpdir, infiles=[], rnnpath='', lang='', outfile='', outdir='', exportlemma=False):
    
    script_path = os.path.dirname(__file__)
    # -1. Run the converter and store converters
    print('Converting and concatenating input files.')
    converters, converted_infiles = [], []
    for infile in infiles:
        if os.path.splitext(infile)[1] not in ['', '.txt', '.tsv']:
            converter = convertfiles.get_converter(infile)
            converter.exportpos = True
            converter.exportlemma = exportlemma
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
    # 1. Call RNN tagger
    # Updated for RNN Tagger v. 1.4.7
    # Still performs better with just the Old French model.
    fname = 'rnn.txt'
    print('Calling the RNN Tagger')
    rnntag.main(
        rnnpath, lang, [opj(tmpdir, 'basefile.txt')],
        outfile=opj(tmpdir, fname)
    )
    # 2. Reconvert output files
    if outdir or \
    (outfile and len(infiles) == 1 and os.path.splitext(outfile)[1] == os.path.splitext(infiles[0])[1]):
        # Only reconverts files if an outdir is given, or one one infile
        # was given with an outfile with an identical extension.
        print('Splitting and back-converting output to original format.')
        concatenater.split(opj(tmpdir, 'rnn.txt'), outdir=tmpdir) # overwrites converted infile.
        for converter, converted_infile in zip(converters, converted_infiles):
            if converter:
                if not outfile: # single outfile case must be handled too
                    outfile = opj(outdir, os.path.basename(converter.source_file))
                converter.to_source(converted_infile, outfile)
                outfile = ''
            else:
                outfile = outfile or opj(outdir, os.path.basename(converted_infile))
                shutil.copy2(opj(tmpdir, 'rnn.txt'), outfile)
    elif outfile:
        shutil.copy2(opj(tmpdir, 'rnn.txt'), outfile)
    else: # Nowhere else to dump the output, print it to stdout.
        with open(opj(tmpdir, 'rnn.txt'), 'r', encoding='utf-8') as f:
            for line in f:
                print(line[:-1])
    
if __name__ == '__main__':
    script_path = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'RNN Tagger converter and wrapper.'
    )
    parser.add_argument('rnnpath', type=str, help='Path to directory containing the RNN tagger.')
    parser.add_argument('lang', help='Name of language.')
    parser.add_argument('infiles', nargs='+', help='Input text files.')
    parser.add_argument('--outdir', help='Output directory.', type=str, default='')
    parser.add_argument('--outfile', help='Output file.', type=str, default='')
    parser.add_argument('--tmpdir', help='Directory for temporary files, if you wish to keep them.', type=str, default='')
    parser.add_argument('--exportlemma', action='store_true', help='Also export lemmas.')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    if kwargs['tmpdir']:
        main(**kwargs)
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            kwargs['tmpdir'] = tmpdir
            main(**kwargs)
    
