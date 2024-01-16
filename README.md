# Old French Lemmatizer

© Tom Rainsford, Institut für Linguistik/Romanistik, University of Stuttgart, January 2024

## What it does

The Old French lemmatizer lemmatizes tokenized Old French texts.
It uses a combination of lexical lookup and the output of the 
[RNN tagger](https://www.cis.uni-muenchen.de/~schmid/tools/RNNTagger/).

+ [Setup](#setup)
+ [Usage (basic)](#usage-basic)
+ [What do the numbers mean?](#what-do-the-numbers-mean)
+ [How do I extend the lexicon?](#how-do-i-extend-the-lexicon)
+ [Usage (advanced)](#usage-advanced)

## Setup

The instructions below are for Ubuntu users. The script should run
on other platforms but has not been tested.

1. Clone this git repository to your computer.
```
git clone https://github.com/ILR-Stuttgart/lgerm-disambiguator.git
```
2. (Optional but highly recommended) Download and unzip Helmut Schmidt's 
[RNN tagger](https://www.cis.uni-muenchen.de/~schmid/tools/RNNTagger/).
Make sure that it runs by typing
```$./cmd/rnn-tagger-old-french.sh```
You may need to install PyTorch first:
```sudo apt install python3-torch```
3. (Optional) Download and install Helmut Schmidt's 
[Tree Tagger](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/).
You will need the tagger and the Old French parameter files (trained on
the BFM). You can also add Achim Stein's parameter files: download
them from [his research website](https://sites.google.com/site/achimstein/research/resources)
and unzip the `stein-oldfrench.par.zip` file into the Tree Tagger
directory.

## Usage (basic)

Assuming that `myfile1.txt` and `myfile2.txt` are one-token-per-line
UTF-8 text files, the RNN Tagger is installed in `~/RNNTagger`, type
the following to lemmatize the text:
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --rnnpath ~/RNNTagger
```

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
        
Tests on unknown Old French data show that scores of 7 and above have
98-99% accuracy. Scores of 2 and 5, where the lexicon and the RNN
Tagger offer different lemmas, are poor (50%--60%), while lemmas with
a score of -10 are terrible (20%). Everything else is 80-90% accurate.

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

You can also build a lexicon file from your own gold corpus using the
`build-lexicon.py` script:
```
./build-lexicon.py my-gold-file-1.txt my-gold-file-2.txt
```
If you supply the `--lexicon` option on the command line, the lexicon
will be saved to this file. If the file already exists, the existing
lexicon will be extended:
```
./build-lexicon.py my-gold-file-1.txt my-gold-file-2.txt 
--lexicon my-existing-lexicon.tsv
```
If you extend an existing lexicon, you must ensure that the gold corpus
and the lexicon use the **same** part of speech tags, otherwise
the lemmatizer won't recognize the tagset and won't be able to convert
them to UD. Do not extend the default lexicon.


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
+ Achim Stein's Tree Tagger tagset (trained on the NCA)

If you need to add another tagset, take a look at the files in the
[maps](./maps) subdirectory and add a further .tsv file mapping your
tagset onto the UD tags.

### Using the Tree Tagger

The RNN Tagger provides very good automatic tags and lemmas but it
is very resource-intensive.

A quicker but less robust alternative
is just to use lemmas looked up from the lexicon with part-of-speech
disambiguation based on tags supplied by the TreeTagger. To do this,
provide `--ttpath` instead of `--rnnpath`:
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --ttpath ~/TreeTagger
```

Additionally, you can run *both* taggers on the data to improve the
reliability of the POS tagging:
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --ttpath ~/TreeTagger
--rnnpath ~/RNNTagger
```

### Other supported file types

The lemmatizer supports a range of file types which it automatically
converts to form TAB pos TAB lemma format before processing:

+ .csv: A UTF-8 encoded comma-separated csv file with a header and a
        **word** column. **pos** and **lemma** will be read from 
        appropriately named columns.
+ .conllu: A CONLL-U file.

If you set the `--outdir` parameter, the lemmatizer will convert the
output back into the source format.

### Viewing the temporary files

The lemmatizer creates a large number of temporary files containing the
raw output from the taggers and the results of the lexical lookup.
If these are useful to you, you can save them by passing the `--tmpdir`
option to the script:
```
./old-french-lemmatizer.py myfile1.txt myfile2.txt --rnnpath ~/RNNTagger
--tmpdir ~/tmp
```
Otherwise, they are stored in a temporary directory which is deleted
after lemmatization is complete.
