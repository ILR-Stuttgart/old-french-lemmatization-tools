#!/usr/bin/python3

#######################################################################
# Wrapper to call the TreeTagger (Linux version)                      #
# Key features:                                                       #
# + Replaces the bash script                                          #
# + Write output to a file, not stdout.                               # 
# + Designed for TreeTagger 3.2.5.                                    #
#######################################################################

import argparse, os, os.path, shutil, subprocess, tempfile
from lib.concat import Concatenater

opj = os.path.join

class Error(Exception):
    pass

class InputDataError(Exception):
    pass

def remove_empty_lines(infile, outfile):
    empty_lines = []
    with open(infile, encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            remove = 0
            for line in fin:
                if line == '\n':
                    remove += 1
                else:
                    fout.write(line)
                    empty_lines.append(remove)
                    remove = 0
    return empty_lines
    
def restore_empty_lines(infile, outfile, empty_lines):
    with open(infile, encoding='utf-8') as fin:
        with open(outfile, 'w', encoding='utf-8') as fout:
            for line in fin:
                add = empty_lines.pop(0) if empty_lines else 0
                fout.write('\n' * add)
                fout.write(line)

def main(ttpath, infiles, lang='', parpath='', outdir='', outfile=''):
    # Sanity check: must either give a language or a parpath
    if not lang and not parpath:
        raise InputDataError('Must specify either a language or a .par file to use.')
    #tmpdir='/home/tmr/tmp/tt'
    #if True:
    with tempfile.TemporaryDirectory() as tmpdir:
        # First, concatenate input files
        infile_tt = opj(tmpdir, 'base.txt')
        outfile_tt = opj(tmpdir, 'out.txt')
        concatenater = Concatenater()
        concatenater.concatenate(infiles, infile_tt)
        # Next, remove all empty lines
        clean_infile_tt = opj(tmpdir, 'base-clean.txt')
        clean_outfile_tt = opj(tmpdir, 'out-clean.txt')
        empty_lines = remove_empty_lines(infile_tt, clean_infile_tt)
        # Next, call the TreeTagger with HS's shell script
        shell_script_linux(ttpath, clean_infile_tt, clean_outfile_tt, tmpdir, lang, parpath)
        #print(outdir, outfile)
        # Now, add the empty lines back in
        restore_empty_lines(clean_outfile_tt, outfile_tt, empty_lines)
        if outdir:
            concatenater.split(outfile_tt, outdir=outdir)
        elif outfile:
            shutil.copy2(outfile_tt, outfile)
        else: # Nowhere else to dump the output, print it to stdout.
            with open(outfile_tt, 'r', encoding='utf-8') as f:
                for line in f:
                    print(line[:-1])

def shell_script_linux(ttpath, infile, outfile, tmpdir, lang='', parpath=''):
    # Sanity check: must either give a language or a parpath
    if not lang and not parpath:
        raise InputDataError('Must specify either a language or a .par file to use.')
    tagger = opj(ttpath, 'bin', 'tree-tagger')
    parfile = parpath or opj(ttpath, 'lib', lang + '.par')
    args = [tagger, '-token', parfile, infile, outfile]
    subprocess.run(args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Wrapper to call the TreeTagger independent of the shell scripts on ' + \
        'pre-tokenized text, with model selection'
        )
    parser.add_argument('ttpath', help='Path to directory containing the TreeTagger.')
    parser.add_argument('--lang', type=str, help='Name of language.', default='')
    parser.add_argument('--parpath', type=str, help='Path to other .par file.', default='')
    parser.add_argument('--infiles', nargs='+', help='Input files, one token per line.')
    parser.add_argument('--outdir', help='Output directory.', type=str, default='')
    parser.add_argument('--outfile', help='Output file.', type=str, default='')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    main(**kwargs)
