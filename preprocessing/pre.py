#!/usr/bin/env python3
''' texify.py converts "chord lines" to injected \chord{} LaTeX tags '''

import os
import re

def chord_positions(chordline):
    ''' Returns a list of chords and their respective positions in line. '''
    chords = chordline.split()
    start = 0
    positions = []
    for c in chords:
        start = chordline.index(c, start)
        positions.append(start)
        start += len(c)
    return chords, positions


def mini_tex_escape(line):
    ''' Handles minimal TeX escaping (F#, ...). Complicate as needed. '''
    line = line.replace('#', '\#')
    return line


def inject_line(line, chords, positions):
    ''' Injects chords onto their positions into line. '''
    injected_line = ""
    last = 0
    for i in range(len(chords)):
        injected_line += line[last:positions[i]]
        injected_line += "\chord{" + chords[i] + "}"
        last = positions[i]
    injected_line += line[last:]
    return mini_tex_escape(injected_line)


def texify_song(file_location):
    ''' Converts file with structure:
            C         G      D
            lyrics lyrics lyrics lyrics lyrics
        into
            \chord{C}lyrics lyr\chord{G}ics lyr\chord{C}ics lyrics lyrics
        assuming whitespace as chord-separator and always even/odd separation
        for chords/lyrics.
    '''
    with open(file_location, 'r', encoding="utf-8") as f:
        lines = f.read().splitlines()
        chordlines = lines[::2]
        textlines = lines[1::2]
        for i in range(len(chordlines)):
            chords, positions = chord_positions(chordlines[i])
            injected_line = inject_line(textlines[i], chords, positions)
            print(injected_line + "\\\\")

def strumming_pattern(text):
    n = len(text) // 2

    formated = []

    formated.append('\\begin{tabular}{{@{} ' + ' '.join(['c@{}c' for i in range(n)]) + ' @{}}}')

    arrows = ['$\\downarrow$' if t == 'd' else '$\\uparrow$' if t == 'u' else '' for t in text]
    formated.append(' & '.join(arrows) + '\\\\')

    numbers = [str(i//2 + 1) if i%2 == 0 else '-' for i in range(2*n)]
    formated.append(' & '.join(numbers) + '\\\\')

    formated.append('\\end{tabular}')


    return '\n'.join(formated)

def parse_song_info(data):

    song_info = {'Title': [], 'By': [], 'Capo': [], 'Strumming': []}

    for line in data.splitlines():
        m = re.match(r'Title: (.*)', line)
        if m:
            song_info['Title'] = m.group(1)

        m = re.match(r'By: (.*)', line)
        if m:
            song_info['By'] = m.group(1)

        m = re.match(r'Capo: (.*)', line)
        if m:
            song_info['Capo'] = m.group(1)

        m = re.match(r'Strumming: (.*)', line)
        if m:
            song_info['Strumming'] = strumming_pattern(m.group(1))

    formated = '{{\\Large\\bfseries {Title}}}\\\\\n{{\\large\\bfseries\\itshape {By}}}\\\\\n\\textbf{{Capo}}: {Capo}\\\\\n\\textbf{{Strumming}}:\\\\[1ex]\n{Strumming}\n'.format(**song_info)

    return formated

def split_song(file_location):
    ''' Handles anotated txt file. Allowed tags (and file structure):
        [Info]
            Title:
            By:
            Capo:
            Strumming:

        [Intro]
        [Verse]
        [Chorus]
        [Bridge]
    '''
    with open(file_location, 'r', encoding="utf-8") as f:
        txt = f.read()

    with open(file_location + '.tex', 'w', encoding="utf-8") as f:
        song_parts = re.split(r'(\[\w+\])\n', txt)

        if song_parts[0] == '':
            song_parts.pop(0)

        tags = song_parts[::2]
        data = song_parts[1::2]

        for j, (tag, dat) in enumerate(zip(tags, data)):
            if tag.lower() == '[info]':
                f.write(parse_song_info(dat) + "\n")

            elif tag.lower() == '[intro]':
                f.write('\\textbf{{Intro}}:\\\\\n' + dat)

            elif tag.lower() == '[bridge]':
                f.write('\\textbf{{Bridge}}:\\\\\n' + dat)

            elif tag.lower() == '[chorus]' or tag.lower() == '[verse]':

                lines = [s for s in dat.splitlines() if s]

                chordlines = lines[::2]
                textlines = lines[1::2]

                parsed = ''

                for i in range(len(chordlines)):
                    chords, positions = chord_positions(chordlines[i])
                    injected_line = inject_line(textlines[i], chords, positions)
                    # print(injected_line + "\\\\")
                    parsed += injected_line.replace(' ','~') + "\\\\\n"

                if tag.lower() == '[chorus]':
                    f.write('\n\\textbf{{Chorus}}:\\\\\n')
                elif tag.lower() == '[verse]':
                    f.write('\n\\textbf{{Verse}}:\\\\\n')

                f.write(parsed)


        # with open(file_location + '.tex', 'w', encoding="utf-8") as f:
        #
        #     f.write('\n'.join(zip(tags,data)))

# texify_song('input.txt')

split_song('how-to-save-a-life.txt')
