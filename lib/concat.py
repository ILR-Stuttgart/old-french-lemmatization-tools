#!/usr/bin/python3

import os, os.path

class Concatenater():
    
    def __init__(self):
        self.path_lines = []
        
    def concatenate(self, paths, outfile):
        with open(outfile, 'w', encoding='utf-8') as fout:
            for path in paths:
                with open(path, 'r', encoding='utf-8') as fin:
                    for i, line in enumerate(fin):
                        fout.write(line)
                    self.path_lines.append((path, i))
    
    def split(self, infile, outdir=''):
        if outdir and not os.path.exists(outdir):
            os.mkdir(outdir)
        # Either use the same file name and dump them in outdir
        # or rename the files with a .out.txt extension
        outfile, i, path_line, fout = '', 0, ('', -1), None
        path_lines = self.path_lines[:]
        with open(infile, 'r', encoding='utf-8') as fin:
            for line in fin:
                if i > path_line[1]:
                    i = 0
                    path_line = path_lines.pop(0)
                    if fout: fout.close()
                    if outdir:
                        fout = open(
                            os.path.join(outdir, os.path.basename(path_line[0])),
                            'w', encoding='utf-8'
                        )
                    else:
                        l = os.path.splitext(path_line[0])
                        fout = open(l[0] + '.out' + l[1], 'w', encoding = 'utf-8')
                fout.write(line)
                i += 1
        fout.close()
