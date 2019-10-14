## Useful scripts

```Shell
source ./py2-e2e-coref/bin/activate

CUDA_VISIBLE_DEVICES=1 python demo.py final
CUDA_VISIBLE_DEVICES=1 python predict.py final playground/test.input playground/test.output
```

## Fine-tune model

config file: `experiments.conf`
original train file: `train.english.jsonlines`

### How to generate train file

```
ontonotes_data -> conll_format._gold_conll by 
    bash conll-2012/v3/scripts/skeleton2conll.sh -D $ontonotes_path/data/files/data conll-2012
conll_format._gold_conll -> train.jsonlines by
    ./minimize.py
```

### jsonlines format
```Json
{
  "speakers": [[], [], []],
  "doc_key": "",
  "sentences": [[], [], []],
  "constituents": [[], [], [], [], [], [], []],
  "clusters": [[], [], [], [], []],
  "ner": [[], [], [], [], [], [], []]
}
```

Do we need all information above? It seems that the paper only uses sentences, clusters and speakers.
A: `./train.english.jsonlines.keep_necessary_columns` justified we only need three columns.
Is it necessary to generate CoNLL format files? http://conll.cemantix.org/2012/data.html
A: Probably no.

```shell
python process_ecbplus.py /home/jlu229/entity-event-extraction/data/ECB+_LREC2014/ECB+/ ecbplus_converted
python playground/convert_gold_jsonlines.py dev.ecbplus_converted.jsonlines playground/dev.ecbplus_converted.input
```

For evaluation, they need conll format file. Is it really important to have?
A: They actually use conll format file for evaluation. 
In `conll.py output_conll(gold_file, prediction_file, predctions)`, the function need gold file as input file.

By invoke `perl scorer.pl`, see if conll gold file need info other that coreference chain column.
A: Only the coreference chain column counts!
`perl conll-2012/scorer/v8.01/scorer.pl muc test_scorer.gold_conll test_scorer.auto_conll`

### split train dev set
total 45 topics in ECB+.
Choose #3, #27, #45 as dev set.

### predict and evaluate
```shell
CUDA_VISIBLE_DEVICES=2 python predict.py final playground/dev.ecbplus_converted.input playground/dev.ecbplus_converted.output
```

## Experiments
1) evaluate e2e-coref on ECB+
`perl conll-2012/scorer/v8.01/scorer.pl all dev.ecbplus_converted.conll playground/dev.ecbplus_converted.output.conll`
2) fine-tune e2e-coref on ECB+, and evaluate it
```
CUDA_VISIBLE_DEVICES=2 python train.py best
```
currently fine-tune without `lm_file`
