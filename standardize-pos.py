#!/usr/bin/python3

########################################################################
# Script to standardize the part-of-speech tags to UD using a map      #
########################################################################

class Error(Exception):
    pass
    
class MapNotFound(Error):
    pass

import argparse, os, os.path, shutil

MAPSDIR='maps'
opj = os.path.join

def get_map(filepos, mapsdir=MAPSDIR):
    mapspaths = os.listdir(mapsdir)
    for mapspath in mapspaths:
        if mapspath[-4:] != '.tsv': continue # Ignore non .tsv files
        amap = parse_map(opj(mapsdir, mapspath))
        # Allow 10% unrecognized tags discrepancy between the tagsets
        if len(filepos - set(amap.keys())) < len(filepos) / 10:
            print('Using ' + mapspath)
            return amap
    return {}
    
def parse_map(infile):
    with open(infile, 'r') as f:
        d = {}
        for line in f:
            x = line.rstrip().split('\t')
            if not len(x) == 2: continue
            d[x[0]] = x[1]
    return d

def main(infile, outfile='out.txt'):
    # First, read the pos tags in the file
    filepos = set()
    with open(infile, 'r') as f:
        for line in f:
            cols = line.rstrip().split('\t')
            try:
                filepos.add(cols[1])
            except IndexError:
                pass
    # Next, get the map
    themap = get_map(filepos)
    if not themap:
        raise MapNotFound('No map found for this tagset.')
    # Finally, translate the tags and write the outfile
    #print(themap)
    with open(infile, 'r') as fin:
        with open(outfile, 'w') as fout:
            for line in fin:
                cols = line.rstrip().split('\t')
                i = 1
                while i < len(cols): 
                    try:
                        cols[i] = themap[cols[i]]
                    except KeyError: # not in map; delete the tag
                        cols[i] = ''
                    i += 2
                fout.write('\t'.join(cols) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Script to standardize part-of-speech tag to UD.'
    )
    parser.add_argument('infile', help='Input text file.')
    parser.add_argument('outfile', help='Output text file.', nargs='?', default='out.txt')
    args = vars(parser.parse_args())
    main(args.pop('infile'), args.pop('outfile'))
