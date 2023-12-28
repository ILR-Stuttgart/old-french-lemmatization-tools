#!/usr/bin/python3

#######################################################################
# Wrapper to call the RNN Tagger.                                     #
# Key features:                                                       #
# + Replaces the bash script                                          #
# + Handles empty lines after punctuation                             #
#   (i.e sentence tokenization requirement)                           #
# + Write output to a file, not stdout.                               # 
#######################################################################

import argparse, os, os.path, shutil, subprocess, tempfile

opj = os.path.join

class Error(Exception):
    pass

class InputDataError(Exception):
    pass
    
def main(rnnpath, lang, infile, outfile, gpu=0):
    # First, check that the file is s-tokenized.
    has_empty_lines = check_empty_lines(infile)
    with tempfile.TemporaryDirectory() as tmpdir:
        s_tokenized_infile = opj(tmpdir, 'in.txt')
        s_tokenized_outfile = opj(tmpdir, 'out.txt')
        if has_empty_lines:
            # Keep original file
            shutil.copy2(infile, s_tokenized_infile)
        else:
            # Add empty lines after punctuation
            tokenize_sentences(infile, s_tokenized_infile)
        # Next, call the RNN Tagger with HS's shell script
        shell_script(rnnpath, lang, s_tokenized_infile, s_tokenized_outfile, gpu, tmpdir)
        if has_empty_lines: # Original file was s-tokenized.
            shutil.move(s_tokenized_outfile, outfile)
        else:
            remove_empty_lines(s_tokenized_outfile, outfile)

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
    counter, last_pnc = 0, False
    with open(infile, 'r') as fin:
        with open(outfile, 'w') as fout:
            for line in fin:
                if last_pnc and not line == '\n':
                    fout.write('\n')
                last_pnc = False
                if line[0] in ['.', '!', '?'] and len(line) == 2:
                    last_pnc = True
                    counter += 1
                elif line == '\n':
                    counter += 1
                fout.write(line)
    if counter == 0:
        raise InputDataError('Cannot sentence-tokenize source file.')
        
def remove_empty_lines(infile, outfile):
    # Removes blank lines from file
    print('Removing empty lines')
    with open(infile, 'r') as fin:
        with open(outfile, 'w') as fout:
            for line in fin:
                if line != '\n': fout.write(line)
    
def shell_script(rnnpath, lang, infile, outfile, gpu=0, tmpdir='/home/tmr/tmp'):
    # Python reimplementation of Helmut Schmidt's shell script,
    # without the tokenization stage.
    cwd = os.getcwd()
    os.chdir(rnnpath)
    # Abbreviate os.path.join
    
    # Step 1. Run the POS tagger
    l = [
        opj('.', 'PyRNN', 'rnn-annotate.py'), # TAGGER
        opj('.', 'lib', 'PyRNN', lang), # RNNPAR
        infile
    ]
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
        opj('.', 'PyNMT', 'nmt-translate.py'), # LEMMATIZER
        '--print_source',
        '--gpu', str(gpu), # GPU parameter
        opj('.', 'lib', 'PyNMT', lang), #NMTPAR
        opj(tmpdir, 'tmp.reformatted')
    ]
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
    parser.add_argument('--gpu', type=int, default=0,
               help='selection of the GPU (default is GPU 0)')
    parser.add_argument('rnnpath', help='Path to directory containing the RNN tagger.')
    parser.add_argument('lang', help='Name of language.')
    parser.add_argument('infile', help='One token per line input file.')
    parser.add_argument('outfile', help='Output file.')
    args = vars(parser.parse_args())
    main(
        args.pop('rnnpath'), args.pop('lang'), args.pop('infile'), 
        args.pop('outfile'), args.pop('gpu')
    )
