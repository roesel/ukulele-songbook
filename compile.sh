#!/bin/bash

python3 pre.py --capo --strumming --note --compact

pdflatex --shell-escape -interaction=nonstopmode songbook.tex > compile.log
