#!/usr/bin/python3

import argparse, os.path, csv, pickle

class Error(Exception):
    pass
    
class UnknownFileType(Error):
    pass

class Converter():
    
    def __init__(self, source_file, source_encoding='utf-8'):
        self.linemap = []
        self.source_file = source_file
        self.source_encoding = source_encoding
        
    def from_source(self, outfile):
        # Default method, does nothing
        with open(self.source_file, 'r', encoding=self.source_encoding) as fin:
            with open(outfile, 'w', encoding='utf-8') as fout:
                for i, line in enumerate(fin):
                    fout.write(line)
                    self.linemap.append((i, i))
                    
    def to_source(self, infile, outfile):
        with open(infile, 'r', encoding='utf-8') as fin:
            with open(outfile, 'w', encoding=self.source_encoding) as fout:
                for line in fin:
                    fout.write(line)
                    
    def pickle(self):
        with open(self.source_file + '.convert', 'wb') as f:
            pickle.dump(self, f)
                    
class CsvConverter(Converter):
    """
    Processes .csv files with a header row. There must be a "word"
    column or it will fail.
    """
    
    def from_source(self, outfile):
        with open(self.source_file, newline='', encoding=self.source_encoding) as fin:
            with open(outfile, 'w', encoding='utf-8') as fout:
                reader = csv.DictReader(fin, restval='')
                for i, row in enumerate(reader):
                    try:
                        word = row['word']
                    except KeyError:
                        raise UnknownFileType('CSV file must have a header and a "word" column.')
                    fout.write(word)
                    for postag in ['syntag', 'pos', 'cat', 'cattex-pos', 'ud-pos']:
                        if postag in row: 
                            fout.write('\t' + row[postag])
                            break
                    else:
                        fout.write('\t')
                    for lemmatag in ['lemma_dmf', 'lemma']:
                        if lemmatag in row:
                            fout.write('\t' + row[lemmatag])
                            break
                    else:
                        fout.write('\t')
                    fout.write('\n')
                    self.linemap.append((i + 1, i))
                    
    def to_source(self, infile, outfile):
        #print(self.source_file)
        #print(infile)
        #print(outfile)
        with open(infile, encoding='utf-8') as fin:
            with open(self.source_file, newline='', encoding=self.source_encoding) as source_file:
                reader = csv.DictReader(source_file)
                rows = []
                header = reader.fieldnames
                postag = 'pos_ofl' if 'pos' in header else 'pos'
                lemmatag = 'lemma_ofl' if 'lemma' in header else 'lemma'
                scoretag = 'lemma_score'
                header.extend([postag, lemmatag, scoretag])
                for row in reader:
                    fin_line = fin.readline()
                    try:
                        word, pos, lemma, score = fin_line.rstrip().split('\t')
                    except:
                        print(row)
                        print(fin_line)
                        raise
                    row[postag], row[lemmatag], row[scoretag] = pos, lemma, score
                    rows.append(row)
                #print(rows[:10])
            with open(outfile, 'w', newline='', encoding=self.source_encoding) as fout:
                writer = csv.DictWriter(fout, fieldnames=header)
                writer.writeheader()
                writer.writerows(rows)
                    
def get_converter(source_file):
    ext = os.path.splitext(source_file)[1]
    if ext in ['', '.txt', '.tsv']:
        return Converter(source_file)
    if ext in ['.csv']:
        #raise UnknownFileType('This type of file is not supported.')
        return CsvConverter(source_file)
    if ext in ['.conllu']:
        raise UnknownFileType('This type of file is not supported.')
        #return CsvConverter(source_file)
    if ext in ['.psd']:
        raise UnknownFileType('This type of file is not supported.')
        #return PsdConverter(source_file)
    if ext in ['.xml']:
        raise UnknownFileType('This type of file is not supported.')
        #return TEIConverter(source_file)
        
def unpickle_converter(source_file):
    with open(source_file + '.convert', 'rb') as f:
        converter = pickle.load(f)
    return converter

def convert_from_source(infile, outfile='out.txt'):
    converter = get_converter(infile)
    converter.from_source(outfile)
    return converter
    
def main(infile, outfile='out.txt', lemmafile=''):
    
    if lemmafile:
        converter = unpickle_converter(infile)
        converter.to_source(lemmafile, outfile)
    else:
        converter = convert_from_source(infile, outfile)
        converter.pickle()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Converts input file to correct format for lemmatization algorithms.\n' +
        'If lemmafile is provided, merges it back into a converted source file.'
    )
    parser.add_argument('infile', type=str, help='Input file.')
    parser.add_argument('--outfile', type=str, help='Output file.')
    parser.add_argument('--lemmafile', type=str, help='Word-pos-lemma-score file, tab separated.')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    main(**kwargs)
