# LGeRM disambiguator

© Tom Rainsford, Institut für Linguistik/Romanistik, University of Stuttgart, January 2023

Script to disambiguate forms returned from the LGeRM lemmatizer. 
Based on a design by Alexei Lavrentiev (ENS de Lyon).

## Usage

Filters the LGeRM output based on results from a POS tagger. Input is a
CSV file with at least word, cattex_pos, and lgerm_out columns.

```
lgerm.py [-h] infile [outfile]

positional arguments:
  infile      Input file to import.
  outfile     Output file to export.
```
  
## Demo

```
./lgerm.py demo/lgermed.csv out.csv
```


