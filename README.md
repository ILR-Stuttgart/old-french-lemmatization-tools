# Old French Lemmatizer

© Tom Rainsford, Institut für Linguistik/Romanistik, University of Stuttgart, January 2023

## What it does

The Old French lemmatizer lemmatizes **tokenized** Old French texts.

## Setup

The instructions below are for Ubuntu users although the script will
run on any platform

1. Clone this git repository to your computer.
```
git clone https://github.com/ILR-Stuttgart/lgerm-disambiguator.git
```
2. (Optional but recommended) Download and unzip Helmut Schmidt's 
[RNN tagger](https://www.cis.uni-muenchen.de/~schmid/tools/RNNTagger/).
Make sure that it runs by typing
```$./cmd/rnn-tagger-old-french.sh```
You may need to install PyTorch first:
```sudo apt install python3-torch```

## Usage (basic)

Assuming that `myfile1.txt` and `myfile2.txt` are one-token-per-line
UTF-8 text files and that the RNN Tagger is installed in `~/RNNTagger`,
type the following to lemmatize the text:
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --rnnpath ~/RNNTagger
```

## Usage (advanced)

### Saving the output

If you would rather have your output saved to a file, use 
`--outfile` for writing to a single file.
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --rnnpath ~/RNNTagger
--outfile ~/lemmatized.txt
```

By default, the tagger concatenates the output for all files.
If you would rather have a separate output file for each input file,
use `--outdir` to specify the directory where they should be created.
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --rnnpath ~/RNNTagger
--outdir ~/lemmatized_files
```

### Including annotation in the input

If you want to include part-of-speech tags or even lemmas in the 
input file, simply create a two- or three-columns tab separated file,
e.g.
```
Roland  PROPN
```
or
```
Roland  PROPN   Roland
```

The lemmatizer will assume that annotation in the input is gold
annotation and will not modify it. If it isn't gold, use the
`--inputanno auto` argument to tell the lemmatizer that it's automatic,
in which case it will be compared against the output of the RNN tagger.
```
./old-french-lemmatizer.py mytaggedfile1.txt mytaggedfile2.txt --rnnpath ~/RNNTagger
--inputanno auto
```

If you want the lemmatizer to ignore annotation in the input, set
`--inputanno` to `ignore`
```
./old-french-lemmatizer.py mytaggedfile1.txt mytaggedfile2.txt --rnnpath ~/RNNTagger
--inputanno ignore
```

The lemmatizer converts all pos annotation to UD. It can recognize the
following tagsets:
+ FRANTEXT
+ Cattex (BFM)
+ Penn Treebank

If you need to add another tagset, take a look at the files in the
[maps](./maps) subdirectory and add a further .tsv file mapping your
tagset onto the UD tags.

### Other supported file types

The lemmatizer supports a range of file types which it automatically
converts to form TAB pos TAB lemma format before processing:

+ .csv: A UTF-8 encoded comma-separated csv file with a header and a
        **word** column. **pos** and **lemma** will be read from 
        appropriately named columns.
+ .conllu: A conllu file (not yet supported)
+ .psd: A Penn-format file (not yet supported)
+ .xml: A TEI P5 conforming .xml file (not yet supported)

If you set the `--outdir` parameter, the lemmatizer will convert the
output back into the source format.

## What do the numbers mean?

The fourth column of the lemmatizer's output file gives a "reliability"
score for the lemmatization:

+ 10: unambiguous gold lemma supplied in the input
+ 7-9: lemma taken from a lexicon. If multiple lemmas were found,
        they were successfully disambiguated by the part-of-speech tag.
        The result matches the RNN tagger's autolemma.
+ 3-6: lemma taken from a lexicon but either it doesn't match the RNN
        tagger's lemma, or there were multiple lemmas possible which
        couldn't be disambiguated by the part-of-speech tag.
+ 2: lemma taken from a lexicon but it doesn't match the RNN tagger's
        output in any respect, or the RNN tagger was not run.
+ 1: \[not used\]
+ 0: lemma from the RNN tagger but this form of the lemma is not found in the lexicon.
+ -1: multiple lemmas from the lexicon, impossible to disambiguate them using
        the part-of-speech tag and the automatic lemma.
+ -10: lemma from the RNN tagger but the **lemma** is not attested in the lexicon.
        There is a good chance that this lemma has been invented by the RNN tagger!

## How do I extend the lexicon?

The tagger's default lexicon is found in the [lexicons](./lexicons)
subfolder. 

If you want to manually select the lexicon files the lemmatizer should
use, use the `--lexicons` argument, e.g.
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --rnnpath ~/RNNTagger
--lexicons ./lexicons/old-french/lgerm-medieval.tsv myextraforms.tsv
```

The original lexicon is based on the file `LGeRM-LexiqueMorphologique-MF-2.0.0.xml`
converted using the [lgerm-xml2csv.py](../../scripts/lgerm-xml2csv.py)
script. The [lgerm-medieval.tsv](lexicons/old-french/lgerm-medieval) file
is was downloaded from [http://www.atilf.fr/LGeRM/](http://www.atilf.fr/LGeRM/)
on 22 December 2023 and is made available under a CREATIVE COMMONS LICENSE CC-BY-NC 2.0.

