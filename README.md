
![MIDOG 2025 Logo](https://github.com/user-attachments/assets/6e28b009-7dcb-4bc1-b463-8528e943f952)

## MIDOG 2025 - Evaluation container for Track 2 (Atypical Mitosis Classification)

This repository contains the official evaluation container used for the MIDOG 2025 MICCAI challenge. It is based on the starter kit provided by grand-challenge.org, and adds the relevant metrics.

Please note that obviously the ground-truth in this docker container is not part of the real test sets to be used in the challenge.

### How it works:

The ground truth and the predictions are fed to this container. The predictions are fed as the file `predictions.json`, but for each predicted image, an independent json file is provided.

The ground truth format is as follows:
```
[{"image": "stack_1.tiff", 
  "labels": ["normal", "normal", "normal", "atypical", "atypical", "normal", "normal", "atypical", "normal", "normal", "normal", "normal", "normal", "normal", "normal", "normal"], 
  "tumordomains": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}, 
 {"image": "stack_2.tiff", 
  "labels": ["normal", "normal", "normal", "normal", "atypical", "normal", "normal", "atypical", "normal", "normal", "normal", "normal", "normal", "normal", "atypical", "normal"], 
  "tumordomains": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}, 
{"image": "stack_3.tiff", 
 "labels": ["normal", "normal", "normal", "normal", "normal", "atypical", "normal", "normal", "normal", "atypical", "normal", "normal", "normal", "normal", "normal", "normal"], 
 "tumordomains": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]},  
 {"image": "stack_747.tiff", 
 "labels": ["normal"], 
 "tumordomains": [6]}
]
```

The dataset consists of a number of stacks, i.e., TIFF images containing multiple individual images.
Each image stack has up to 16 individual images, that can either carry the label `normal` or `atypical`. Each image also is associated with a numeric tumor domain value.

The multiple-mitotic-figure-classification.json files to be expected from the docker containers of the participants have the following format:
```
[
  {
    "class": "normal",
    "confidence": 0.029465317726135254
  },
  {
    "class": "normal",
    "confidence": 0.36702030897140503
  },
  {
    "class": "normal",
    "confidence": 0.20595765113830566
  },
  {
    "class": "atypical",
    "confidence": 0.6873773634433746
  },
  {
    "class": "normal",
    "confidence": 0.47353261709213257
  },
  {
    "class": "normal",
    "confidence": 0.1758342981338501
  },
  {
    "class": "normal",
    "confidence": 0.17779576778411865
  },
  {
    "class": "normal",
    "confidence": 0.17349058389663696
  },
  {
    "class": "normal",
    "confidence": 0.032076478004455566
  },
  {
    "class": "normal",
    "confidence": 0.2329137921333313
  },
  {
    "class": "normal",
    "confidence": 0.1185464859008789
  },
  {
    "class": "normal",
    "confidence": 0.034657955169677734
  },
  {
    "class": "normal",
    "confidence": 0.38028931617736816
  },
  {
    "class": "normal",
    "confidence": 0.046645522117614746
  },
  {
    "class": "normal",
    "confidence": 0.1984381079673767
  },
  {
    "class": "normal",
    "confidence": 0.05428171157836914
  }
]
```

Here, each of the elements in the list stands for one image in the stack. They are in the same order as in the original stack. As the participants' containers are being run for every stack independently, each container is only required to yield a single of these files. 
