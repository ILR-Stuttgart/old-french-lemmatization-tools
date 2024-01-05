#!/usr/bin/python3

import os.path, csv

class Error(Exception):
    pass
    
class UnknownFileType(Error):
    pass

class Convertor():
    
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
                    
class CsvConvertor(Convertor):
    """
    Processes .csv files with a header row. There must be a "word"
    column or it will fail.
    """
    
    def from_source(self, outfile):
        with open(self.source_file, newline='', encoding=self.source_encoding) as fin:
            with open(outfile, 'w', encoding='utf-8') as fout:
                self.dialect = csv.Sniffer().sniff(fin.read(1024))
                fin.seek(0)
                reader = csv.DictReader(fin, dialect)
                for i, row in enumerate(reader):
                    try:
                        word = reader['word']
                    except KeyError:
                        raise UnknownFileType('CSV file must have a header and a "word" column.')
                    fout.write(word)
                    for postag in ['pos', 'cat', 'cattex-pos', 'ud-pos', 'syntag']:
                        if postag in reader: 
                            fout.write('\t' + reader[postag])
                            break
                    for lemmatag in ['lemma_dmf', 'lemma']:
                        if lemmatag in reader:
                            fout.write('\t' + reader[lemmatag])
                            break
                    fout.write('\n')
                    self.linemap.append((i + 1, i))
                    
    def to_source(self, infile, outfile):
        with open(infile, encoding='utf-8') as fin:
            with open(self.source_file, newline='', encoding=self.source_encoding) as source_file:
                dialect = csv.Sniffer().sniff(source_file.read(1024))
                source_file.seek(0)
                reader = csv.DictReader(fin, dialect)
                rows = []
                header = DictReader(fieldnames)
                postag = 'pos_ofl' if 'pos' in header else 'pos'
                lemmatag = 'lemma_ofl' if 'lemma' in header else 'lemma'
                scoretag = 'lemma_score'
                header.extend([postag, lemmatag, scoretag])
                for row in reader:
                    fin_line = fin.readline()
                    word, pos, lemma, score = fin_line.rstrip().split('\t')
                    row[postag], row[lemmatag], row[scoretag] = pos, lemma, score
                    rows.append(row)
            with open(outfile, 'w', newline='', encoding=self.source_encoding) as fout:
                writer = DictWriter(fout, fieldnames=header, dialect=dialect)
                writer.writeheader()
                writer.writerows(rows)
                    
def get_convertor(source_file):
    ext = os.path.splitext(source_file)[1]
    if ext in ['', '.txt', '.tsv']:
        return Convertor(source_file)
    if ext in ['.csv']:
        #raise UnknownFileType('This type of file is not supported.')
        return CsvConvertor(source_file)
    if ext in ['.conllu']:
        raise UnknownFileType('This type of file is not supported.')
        #return CsvConvertor(source_file)
    if ext in ['.psd']:
        raise UnknownFileType('This type of file is not supported.')
        #return PsdConvertor(source_file)
    if ext in ['.xml']:
        raise UnknownFileType('This type of file is not supported.')
        #return TEIConvertor(source_file)
