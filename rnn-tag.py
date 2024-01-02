#!/usr/bin/python3

#######################################################################
# Wrapper to call the RNN Tagger.                                     #
# Key features:                                                       #
# + Replaces the bash script                                          #
# + Handles empty lines after punctuation                             #
#   (i.e sentence tokenization requirement)                           #
# + Write output to a file, not stdout.                               # 
# + Designed for RNNTagger 1.4.4.                                     #
#######################################################################

import argparse, os, os.path, shutil, subprocess, tempfile
from lib.concat import Concatenater

opj = os.path.join

class Error(Exception):
    pass

class InputDataError(Exception):
    pass
    
def main(rnnpath, lang, infiles, outdir='', user_outfile='', gpu=0):
    with tempfile.TemporaryDirectory() as tmpdir:
        # First, concatenate input files
        infile = opj(tmpdir, 'base.txt')
        outfile = opj(tmpdir, 'out.txt')
        concatenater = Concatenater()
        concatenater.concatenate(infiles, infile)
        # Second, check that the file is s-tokenized.
        has_empty_lines = check_empty_lines(infile)
        s_tokenized_infile = opj(tmpdir, 'in.txt')
        s_tokenized_outfile = opj(tmpdir, 'stok_out.txt')
        if has_empty_lines:
            # Keep original file
            shutil.copy2(infile, s_tokenized_infile)
        else:
            # Add empty lines after punctuation
            empty_lines = tokenize_sentences(infile, s_tokenized_infile)
        # Next, call the RNN Tagger with HS's shell script
        if lang == 'old-french' and os.path.exists(opj('.', 'PyRNN', 'rnn-annotate.py')):
            shell_script_standard(rnnpath, lang, s_tokenized_infile, s_tokenized_outfile, gpu, tmpdir)
        else:
            shell_script_of(rnnpath, lang, s_tokenized_infile, s_tokenized_outfile, gpu, tmpdir)
        if has_empty_lines: # Original file was s-tokenized.
            shutil.move(s_tokenized_outfile, outfile)
        else:
            remove_empty_lines(s_tokenized_outfile, outfile, empty_lines=empty_lines)
        # Finally, deal with the concatenated files
        if outdir:
            concatenater.split(opj(tmpdir, 'out.txt'), outdir=outdir)
        elif user_outfile:
            shutil.copy2(outfile, user_outfile)
        else: # Nowhere else to dump the output, print it to stdout.
            with open(outfile, 'r', encoding='utf-8') as f:
                for line in f:
                    print(line[:-1])

def check_empty_lines(infile):
    # Checks whether file contains empty lines from a sample
    with open(infile, 'r') as f:
        for i, line in enumerate(f):
            if i > 1000: break
            if line == '\n': return True
    return False

def tokenize_sentences(infile, outfile):
    # Ensures that the input file is tokenized into sentences before
    # calling the RNN tagger.
    # Returns a list of booleans recorded which lines were added.
    counter, last_pnc, l = 0, False, []
    with open(infile, 'r') as fin:
        with open(outfile, 'w') as fout:
            for line in fin:
                if last_pnc and not line == '\n':
                    fout.write('\n')
                    l.append(True)
                last_pnc = False
                if line[0] in ['.', '!', '?'] and len(line) == 2:
                    last_pnc = True
                    counter += 1
                elif line == '\n':
                    counter += 1
                fout.write(line)
                l.append(False)
    if counter == 0:
        raise InputDataError('Cannot sentence-tokenize source file.')
    return l
        
def remove_empty_lines(infile, outfile, empty_lines=[]):
    # Removes blank lines from file
    print('Removing empty lines')
    with open(infile, 'r') as fin:
        with open(outfile, 'w') as fout:
            for line in fin:
                delete = empty_lines.pop(0) if empty_lines else False
                if not delete: fout.write(line)
    
def shell_script_standard(rnnpath, lang, infile, outfile, gpu=0, tmpdir='/home/tmr/tmp'):
    
    TAGGER = opj('.', 'PyRNN', 'rnn-annotate.py')
    RNNPAR = opj('.', 'lib', 'PyRNN', lang)
    LEMMATIZER = opj('.', 'PyNMT', 'nmt-translate.py')
    NMTPAR = opj('.', 'lib', 'PyNMT', lang)
    _shell_script(
        rnnpath, lang, infile, outfile, gpu, tmpdir,
        TAGGER, RNNPAR, LEMMATIZER, NMTPAR
    )
    
def shell_script_of(rnnpath, lang, infile, outfile, gpu=0, tmpdir='/home/tmr/tmp'):
    TAGGER = opj('.', 'Python', 'rnn-annotate.py')
    RNNPAR = opj('.', 'lib', 'tagger')
    LEMMATIZER = opj('.', 'Python', 'nmt-translate.py')
    NMTPAR = opj('.', 'lib', 'lemmatizer')
    _shell_script(
        rnnpath, lang, infile, outfile, gpu, tmpdir,
        TAGGER, RNNPAR, LEMMATIZER, NMTPAR
    )
    
def _shell_script(
    rnnpath, lang, infile, outfile, gpu, tmpdir,
    TAGGER, RNNPAR, LEMMATIZER, NMTPAR
):
    # Python reimplementation of Helmut Schmidt's shell script,
    # without the tokenization stage.
    cwd = os.getcwd()
    os.chdir(rnnpath)
    
    # Step 1. Run the POS tagger
    l = [
        TAGGER, # TAGGER
        RNNPAR, # RNNPAR
        infile
    ]
    if gpu == -1: l.extend(['--gpu', '-1']) # Newer versions of tagger need gpu -1
    with open(opj(tmpdir, 'tmp.tagged'), 'w') as f:
        subprocess.run(l, stdout=f)
    # Step 2. Reformat using perl script
    l = [
        'perl', opj('.', 'scripts', 'reformat.pl'), # REFORMAT
        opj(tmpdir, 'tmp.tagged')
    ]
    with open(opj(tmpdir, 'tmp.reformatted'), 'w') as f:
        subprocess.run(l, stdout=f)
    # Step 3. Run the lemmatizer
    l = [
        LEMMATIZER, # LEMMATIZER
        '--print_source',
        '--gpu', str(gpu), # GPU parameter
        NMTPAR, #NMTPAR
        opj(tmpdir, 'tmp.reformatted')
    ]
    #print(l)
    with open(opj(tmpdir, 'tmp.lemmas'), 'w') as f:
        subprocess.run(l, stdout=f)
        
    # Step 4. Lemma lookup
    l = [
        'perl',
        opj('.', 'scripts', 'lemma-lookup.pl'),
        opj(tmpdir, 'tmp.lemmas'),
        opj(tmpdir, 'tmp.tagged')
    ]
    with open(outfile, 'w') as f:
        subprocess.run(l, stdout=f)
    
    # Change back to cwd
    os.chdir(cwd)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Wrapper to call the RNN Tagger independent of the shell scripts on ' + \
        'pre-tokenized text, with model selection'
        )
    parser.add_argument('--gpu', type=int, default=-1,
               help='selection of the GPU (default is GPU -1)')
    parser.add_argument('rnnpath', help='Path to directory containing the RNN tagger.')
    parser.add_argument('lang', help='Name of language.')
    parser.add_argument('--infiles', nargs='+', help='Input files, one token per line.')
    parser.add_argument('--outdir', help='Output directory.', type=str, default='')
    parser.add_argument('--outfile', help='Output file.', type=str, default='')
    args = vars(parser.parse_args())
    main(
        args.pop('rnnpath'), args.pop('lang'), args.pop('infiles'), 
        args.pop('outdir'), args.pop('outfile'), args.pop('gpu')
    )
