#!/bin/bash

python3 pre.py --capo --strumming --note

pdflatex --shell-escape -interaction=nonstopmode songbook.tex
