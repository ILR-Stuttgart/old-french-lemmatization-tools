#!/usr/bin/python3


import argparse, csv, os, os.path

opj = os.path.join

def main(autodir, golddir, outfile='out.txt', datafile=''):
    
    fnames = os.listdir(autodir)
    evals = []
    
    # Parse_files and build evals
    for fname in fnames:
        textname = fname[:-4]
        with open(opj(autodir, fname), encoding='utf-8', newline='') as fauto:
            with open(opj(golddir, fname), encoding='utf-8', newline='') as fgold:
                gold_reader = csv.DictReader(fgold, restval='')
                auto_reader = csv.DictReader(fauto, restval='')
                gold_lemma = 'lemma_gold' if 'lemma_gold' in gold_reader.fieldnames else 'lemma'
                auto_lemma = 'lemma_ofl' if 'lemma_ofl' in auto_reader.fieldnames else 'lemma'
                gold_pos = 'pos_gold' if 'pos_gold' in gold_reader.fieldnames else 'pos'
                auto_pos = 'pos_ofl' if 'pos_ofl' in auto_reader.fieldnames else 'pos'
                for auto_row in auto_reader:
                    gold_row = gold_reader.__next__()
                    try: 
                        d = {
                            'text': textname, 
                            'word': gold_row['word'],
                            'pos_auto': auto_row[auto_pos],
                            'pos_gold': gold_row[gold_pos],
                            'lemma_auto': auto_row[auto_lemma],
                            'lemma_gold': gold_row[gold_lemma],
                            'lemma_score': auto_row['lemma_score'],
                            'lemma_correct': auto_row[auto_lemma] == gold_row[gold_lemma],
                            'pos_correct': auto_row[auto_pos] == gold_row[gold_pos]
                        }
                    except KeyError:
                        print('KeyError in file ' + textname)
                        print(auto_row)
                        print(gold_row)
                        raise
                    evals.append(d)
        # Dump datafile if necessary
        if datafile:
            with open(datafile, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(
                    f, fieldnames=[
                        'text', 'word', 'pos_auto', 'pos_gold', 'lemma_auto',
                        'lemma_gold', 'lemma_score', 'lemma_correct', 'pos_correct'
                    ]
                )
                writer.writeheader()
                writer.writerows(evals)
        # Print summary
        with open(outfile, 'w', encoding='utf-8') as f:
            f.write('Lemmas correct (tokens)\n')
            f.write('=======================\n\n')
            f.write('Condition            Correct  Total Percent\n')
            # 1. Overall
            template = '{:<20} {:>7} {:>6} {:>#7.2f}\n'
            correct = [x['lemma_correct'] for x in evals].count(True)
            f.write(template.format('Total', correct, len(evals), (correct / len(evals)) * 100))
            # By text
            for text in list(set([x['text'] for x in evals])):
                l = list(filter(lambda x: x['text'] == text, evals))
                correct = [x['lemma_correct'] for x in l].count(True)
                total = len(l)
                f.write(template.format('Text ' + text, correct, len(l), (correct / len(l)) * 100))
            # By PoS tag
            for pos in list(set([x['pos_gold'] for x in evals])):
                l = list(filter(lambda x: x['pos_gold'] == pos, evals))
                correct = [x['lemma_correct'] for x in l].count(True)
                f.write(template.format('POS ' + pos, correct, len(l), (correct / len(l)) * 100))
            # By score
            for score in list(set([x['lemma_score'] for x in evals])):
                l = list(filter(lambda x: x['lemma_score'] == score, evals))
                correct = [x['lemma_correct'] for x in l].count(True)
                f.write(template.format('Score ' + str(score), correct, len(l), (correct / len(l)) * 100))
            f.write('\nCommon errors\n')
            f.write('=============\n')
            # Get types
            types = list(set(zip(
                [x['pos_auto'] for x in evals],
                [x['lemma_auto'] for x in evals]
            )))
            wrong = [0] * len(types)
            total = [0] * len(types)
            gold = [set() for i in range(len(types))]
            # Calculate type errors
            for d in evals:
                thetype = (d['pos_auto'], d['lemma_auto'])
                ix = types.index(thetype)
                total[ix] += 1
                if not d['lemma_correct']:
                    wrong[ix] += 1
                    gold[ix].add(d['lemma_gold'])
            # Print results
            types_eval = list(zip(types, wrong, total, gold))
            types_eval.sort(key=lambda x: x[1] / x[2], reverse=True)
            f.write('pos_auto lemma_auto   correct total percent gold_lemmas\n')
            template = '{:<8} {:<12} {:>7} {:>6} {:>#7.2f} {}\n'
            for tup, wrong, total, gold in types_eval:
                if wrong > 0:
                    f.write(template.format(
                        tup[0], tup[1], wrong, total, (wrong / total) * 100,
                        '|'.join(list(gold))
                    ))

if __name__ == '__main__':
    script_path = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = \
        'Evaluates results of lemmatizer. CSV input only; gold CSV ' + \
        'contains lemma_gold or lemma; annotated CSV contains lemma_ofl or lemma.'
    )
    parser.add_argument('autodir', type=str, help='Directory with autolemma files.')
    parser.add_argument('golddir', type=str, help='Directory with gold files.')
    parser.add_argument('--outfile', help='Output file.', type=str, default='out.txt')
    parser.add_argument('--datafile', help='Dataset file for R.', type=str, default='')
    kwargs = vars(parser.parse_args())
    #print(kwargs)
    main(**kwargs)
