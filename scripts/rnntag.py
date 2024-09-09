#!/usr/bin/python3

#######################################################################
# Wrapper to call the RNN Tagger.                                     #
# Key features:                                                       #
# + Replaces the bash script                                          #
# + Handles empty lines after punctuation                             #
#   (i.e sentence tokenization requirement)                           #
# + Write output to a file, not stdout.                               # 
# + Designed for RNNTagger 1.4.4.                                     #
# + Applies file converters                                           #
#######################################################################

import argparse, os, os.path, shutil, subprocess, tempfile, sys
from lib.concat import Concatenater

opj = os.path.join

class Error(Exception):
    pass

class InputDataError(Exception):
    pass
    
def main(rnnpath, lang, infiles, outdir='', outfile=''):
    #tmpdir='/home/tmr/tmp/rnn'
    #if True:
    with tempfile.TemporaryDirectory() as tmpdir:
        # First, concatenate input files
        infile_rnn = opj(tmpdir, 'base.txt')
        outfile_rnn = opj(tmpdir, 'out.txt')
        concatenater = Concatenater()
        concatenater.concatenate(infiles, infile_rnn)
        # Second, check that the file is s-tokenized.
        #has_empty_lines = check_empty_lines(infile)
        s_tokenized_infile = opj(tmpdir, 'in.txt')
        s_tokenized_outfile = opj(tmpdir, 'stok_out.txt')
        #if has_empty_lines:
            # Keep original file
        #    shutil.copy2(infile, s_tokenized_infile)
        #else:
        # Standardize empty lines
        empty_lines = tokenize_sentences(infile_rnn, s_tokenized_infile)
        #print(empty_lines)
        # Next, call the RNN Tagger with HS's shell script
        if lang == 'old-french' and os.path.exists(opj(rnnpath, 'Python', 'rnn-annotate.py')):
            shell_script_of(rnnpath, lang, s_tokenized_infile, s_tokenized_outfile, tmpdir)
        else:
            shell_script_standard(rnnpath, lang, s_tokenized_infile, s_tokenized_outfile, tmpdir)
        #if has_empty_lines: # Original file was s-tokenized.
        #    shutil.move(s_tokenized_outfile, outfile)
        #else:
        remove_empty_lines(s_tokenized_outfile, outfile_rnn, empty_lines=empty_lines)
        # Finally, deal with the concatenated files
        if outdir:
            concatenater.split(outfile_rnn, outdir=outdir)
        elif outfile:
            shutil.copy2(outfile_rnn, outfile)
        else: # Nowhere else to dump the output, print it to stdout.
            with open(outfile_rnn, 'r', encoding='utf-8') as f:
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
    # Returns a list of integers recalling how the empty lines were modified.
    # The RNN Tagger is VERY FUSSY.
    # - no double empty lines
    # - no initial empty line
    # This subroutine fixes the input files so these don't exist.
    counter, last_pnc, l, remove = 0, False, [], 0
    with open(infile, 'r') as fin:
        with open(outfile, 'w') as fout:
            for line in fin:
                if counter == 0 and line == '\n': # double space
                    remove += 1 # add this many empty lines before line
                    continue # don't do anything else
                if (last_pnc or counter == 500) and not line == '\n': # max snt length added
                    fout.write('\n')
                    counter, remove = 0, 0
                    l.append(-1) # remove this empty line
                last_pnc = False
                if line[0] in ['.', '!', '?'] and len(line) == 2:
                    last_pnc = True
                fout.write(line) # write the line
                counter += 1 # increment counter
                l.append(remove) # indicate how many preceding empty lines to remove
                remove = 0 # reset remove to 0
                if line == '\n': # if we've just written an empty line from the input file
                    counter = 0 # reset counter to 0
            # Must end with an empty line
            fout.write('\n')
            l.append(-1)
    return l
        
def remove_empty_lines(infile, outfile, empty_lines=[]):
    # Removes blank lines from file
    print('Restoring empty lines')
    with open(infile, 'r') as fin:
        with open(outfile, 'w') as fout:
            for line in fin:
                add = empty_lines.pop(0) if empty_lines else 0
                if add > 0: fout.write('\n' * add) # add extra empty lines back in
                if add >= 0: # if add >= 0, write the line
                    fout.write(line)
    
def shell_script_standard(rnnpath, lang, infile, outfile, tmpdir='/home/tmr/tmp'):
    
    TAGGER = opj('.', 'PyRNN', 'rnn-annotate.py')
    RNNPAR = opj('.', 'lib', 'PyRNN', lang)
    LEMMATIZER = opj('.', 'PyNMT', 'nmt-translate.py')
    NMTPAR = opj('.', 'lib', 'PyNMT', lang)
    _shell_script(
        rnnpath, lang, infile, outfile, tmpdir,
        TAGGER, RNNPAR, LEMMATIZER, NMTPAR
    )
    
def shell_script_of(rnnpath, lang, infile, outfile, tmpdir='/home/tmr/tmp'):
    TAGGER = opj('.', 'Python', 'rnn-annotate.py')
    RNNPAR = opj('.', 'lib', 'tagger')
    LEMMATIZER = opj('.', 'Python', 'nmt-translate.py')
    NMTPAR = opj('.', 'lib', 'lemmatizer')
    _shell_script(
        rnnpath, lang, infile, outfile, tmpdir,
        TAGGER, RNNPAR, LEMMATIZER, NMTPAR
    )
    
def _shell_script(
    rnnpath, lang, infile, outfile, tmpdir,
    TAGGER, RNNPAR, LEMMATIZER, NMTPAR
):
    # Python reimplementation of Helmut Schmidt's shell script,
    # without the tokenization stage.
    cwd = os.getcwd()
    os.chdir(rnnpath)
    
    # Step 1. Run the POS tagger
    l = [
        sys.executable, # gives the venv python executable
        TAGGER, # TAGGER
        RNNPAR, # RNNPAR
        infile,
        #'--gpu', '-1'
    ]
    #if gpu == -1: l.extend(['--gpu', '-1']) # Newer versions of tagger need gpu -1
    with open(opj(tmpdir, 'tmp.tagged'), 'w') as f:
        #print('With GPU')
        #print(l)
        process = subprocess.run(l, stdout=f)
    if process.returncode > 1 or os.path.getsize(opj(tmpdir, 'tmp.tagged')) == 0:
        with open(opj(tmpdir, 'tmp.tagged'), 'w') as f:
            print('Alright, without the GPU then...')
            l.extend(['--gpu', '-1']) #Try GPU -1
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
        sys.executable, # gives the venv python executable
        LEMMATIZER, # LEMMATIZER
        '--print_source',
        NMTPAR, #NMTPAR
        opj(tmpdir, 'tmp.reformatted'),
        #'--gpu', '-1'
    ]
    #print(l)
    with open(opj(tmpdir, 'tmp.lemmas'), 'w') as f:
        process = subprocess.run(l, stdout=f)
        
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
    parser.add_argument('rnnpath', help='Path to directory containing the RNN tagger.')
    parser.add_argument('lang', help='Name of language.')
    parser.add_argument('--infiles', nargs='+', help='Input files, one token per line.')
    parser.add_argument('--outdir', help='Output directory.', type=str, default='')
    parser.add_argument('--outfile', help='Output file.', type=str, default='')
    args = vars(parser.parse_args())
    main(
        args.pop('rnnpath'), args.pop('lang'), args.pop('infiles'), 
        args.pop('outdir'), args.pop('outfile')
    )
