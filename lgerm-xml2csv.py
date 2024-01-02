#!/usr/bin/python3

#######################################################################
# Converts an XML lexicon downloaded from the ATILF website into a    #
# csv table.                                                          #
# Requires "saxonb-xslt" to be on the system path                     #
# Try apt install saxonb                                              #
#######################################################################

import argparse, os.path, sys, subprocess, tempfile, re
    
def main(infile, outfile):
    path = os.path.dirname(os.path.realpath(__file__))
    # Step 1. Convert to utf-8
    # 1a. Open temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
    #tmpdir = '/home/tmr'
        tmp = open(os.path.join(tmpdir, 'tmp.xml'), 'w', encoding='utf-8', errors='replace')
        # 1b. Open xml file
        f = open(infile, 'r', encoding='iso-8859-1', errors='replace')
        for line in f:
            x = xmlentcheck(line)
            tmp.write(x)
        f.close()
        tmp.close()
        # Write call to saxonb parser
        args = ['saxonb-xslt', os.path.join(tmpdir, 'tmp.xml'), os.path.join(path, 'xsl', 'lgerm-xml2tsv.xsl')]
        with open(os.path.join(tmpdir, 'tmp.tsv'), 'wb') as f:
            subprocess.run(args, stdout=f) # XSLT parser prints to stout
        # Capitalize all lemmas which are given as nom propre or nom de lieu
        with open(os.path.join(tmpdir, 'tmp.tsv'), 'r', encoding='utf-8') as fin:
            with open(outfile, 'w', encoding='utf-8') as fout:
                for line in fin:
                    if line.count('nom propre\t') or line.count('nom de lieu\t'):
                        line = line[0].upper() + line[1:]
                    fout.write(line)

def xmlentcheck(s):
    # Replaces ampersands with &amp; (bug in source XML)
    s = s.replace('&', '&amp;')
    for char in s:
        if (ord(char) > 31 and ord(char) < 65534) or ord(char) in [9, 10, 13]: continue
        s = s.replace(char, '?') # replace characters disallowed in XML
    return s

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Converts an XML file from ATILF into a CSV table.'
        )
    parser.add_argument('infile', help='Input XML file to load or import.')
    parser.add_argument('outfile', help='Output CSV file to save or export.')
    args = vars(parser.parse_args())
    main(args.pop('infile'), args.pop('outfile'))
