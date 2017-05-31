#!/usr/bin/env python3
''' texify.py converts "chord lines" to injected \chord{} LaTeX tags '''


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


texify_song('input.txt')
