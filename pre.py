''' texify.py converts "chord lines" to injected \chord{} LaTeX tags '''

import os
import re
import glob
import errno

import argparse

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

def get_all_files_from(directory):
    owd = os.getcwd()
    os.chdir(directory)
    files = []
    for file in glob.glob("*.txt"):
        files.append(file)
    os.chdir(owd)
    return files


def inject_line(line, chords, positions):
    ''' Injects chords onto their positions into line. '''
    injected_line = ""
    last = 0
    for i in range(len(chords)):
        if re.match("\(.*\)", chords[i]):
            injected_line += chords[i]
        else:
            # try to fix chords after the last word in each line (WIP)
            if len(line) >= positions[i]:
                injected_line += line[last:positions[i]]
            else:
                if last < len(line):
                    injected_line += line[last:positions[i]]
                    N = 4 - (len(line) - last) + 2
                else:
                    N = 4
                print(N)
                injected_line += "\phantom{"+ "N"*N +"}"

            injected_line += "\chord{" + chords[i] + "}"
            last = positions[i]
    injected_line += line[last:]
    return mini_tex_escape(injected_line)

def inline_chord_line(line):
    chords = line.split()
    for i in range(len(chords)):
        if re.match("\(.*\)", chords[i]):
            pass
        else:
            chords[i] = "\inlinechord{" + chords[i] + "}"
    return mini_tex_escape('~~'.join(chords))

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

    bars = text.split()

    formated = []

    for bar in bars:
        n = len(bar) // 2

        formated.append('\\begin{tabular}{{@{} ' + ' '.join(['c@{}c' for i in range(n)]) + ' @{}}}')

        arrows = ['$\\downarrow$' if t == 'd' else \
            '$\\uparrow$' if t == 'u' else \
            '$\\times$' if t == 'x' else \
            '$\\downarrowcrossed$' if t == 'y' else \
            '$\\uparrowcrossed$' if t == 'z' else \
            '' for t in bar]
        formated.append(' & '.join(arrows) + '\\\\')

        numbers = [str(i//2 + 1) if i%2 == 0 else '-' for i in range(2*n)]
        formated.append(' & '.join(numbers) + '\\\\')

        formated.append('\\end{tabular}')


    return '\n'.join(formated)

def parse_song_info(data):

    song_info = {'Title': [], 'By': [], 'Capo': [], 'Strumming': {}, 'Note': []}
    song_info['Strumming']['Note'] = []
    song_info['Strumming']['Pattern'] = []

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

        m = re.match(r'Strumming: ([duxyz\-\s]*)(\(.*\))?', line)
        if m:
            strum = strumming_pattern(m.group(1))
            song_info['Strumming']['Note'].append(m.group(2))
            song_info['Strumming']['Pattern'].append(strum)

        m = re.match(r'Note: (.*)', line)
        if m:
            song_info['Note'] = m.group(1)

    formated = '\\addcontentsline{{toc}}{{section}}{{{Title}}}\n'.format(**song_info)
    formated += '{{\\Large\\bfseries {Title}}}~{{\\large\\bfseries\\itshape ({By})}}'.format(**song_info)
    if args.capo or args.note or args.strumming:
        formated += '\\\\[3ex]\n'
    if song_info['Capo'] and args.capo:
        formated += '\\textbf{{Capo}}: {Capo}\\\\[1ex]\n'.format(**song_info)
    if song_info['Strumming'] and args.strumming:
        for note, pattern in zip(song_info['Strumming']['Note'], song_info['Strumming']['Pattern']):
            if note:
                note = ' ' + note
            else:
                note = ''
            formated += '\\textbf{{Strumming}}{}:\\\\[1ex]\n{}\\\\[1ex]\n'.format(note, pattern)
    if song_info['Note'] and args.note:
        formated += '\\textbf{{Note}}: {Note}\\\\[1ex]\n'.format(**song_info)

    # formated text always ends with something like '\\[3ex]\n' - this creates
    # an extra space after the last line -- delete in (i know it's a bad practice) :-)
    formated = re.sub(r'\\\\\[[0-9]ex\]\n$', '\n\n', formated)

    return formated

def split_song(file_location, save_folder):
    ''' Handles anotated txt file. Allowed tags (and file structure):
        [Info]
            Title:
            By:
            Capo:
            Strumming:

        If the tag ends with `*`, it contains only chords:
        e.g. [Intro*], [Outro*], [Ending*], ...

        If the tag ends with `&`, it contains only text:
        e.g. [Verse&], [Chorus&], ...

        Otherwise, it contains chords and text lins:
        e.g. [Bridge], [Pre-Chorus], [Interlude]...

    '''
    with open(file_location, 'r', encoding="utf-8") as f:
        txt = f.read()

    with open(save_folder + '/' + file_location.split("/")[-1] + '.tex', 'w', encoding="utf-8") as f:
        song_parts = re.split(r'(\[[\w\-\*\&]+\])\s*\n', txt)

        if song_parts[0] == '':
            song_parts.pop(0)

        tags = song_parts[::2]
        data = song_parts[1::2]

        for j, tag in enumerate(tags):
            tags[j] = tag.strip()

        used_chords = ''

        for j, (tag, dat) in enumerate(zip(tags, data)):

            if tag.lower() == '[info]':
                pass

            elif re.match(r'\[[\w\-]+\*\]', tag.lower()):
                used_chords += dat.strip() + ' '

            elif re.match(r'\[[\w\-]+\]', tag.lower()):
                lines = [s for s in dat.splitlines() if s]
                chordlines = lines[::2]
                used_chords += ' ' + ' '.join(chordlines) + ' '

            elif re.match(r'\[[\w\-]+\&\]', tag.lower()):
                pass

            else:
                print("Unidentified tag {}".format(tag))
                raise

        # remove all characters except for 'A-Z', 'a-z', '0-9', '/', '#', '()', and whitespace
        used_chords = re.sub(r'([^A-Za-z0-9/#\(\)\s]+)',' ',used_chords)

        used_chords = re.sub(r'(\(.*\))',' ',used_chords)

        # LaTeX does not like '#' character to be used in macros
        # -- better replace it and deal with it in LaTeX
        used_chords = re.sub('#','+',used_chords)

        used_chords = ', '.join(set(used_chords.split()))
        # print(used_chords)

        for j, (tag, dat) in enumerate(zip(tags, data)):

            tag_string = re.sub(r'[\[\]\&\*]','',tag.title())

            if tag.lower() == '[info]':
                f.write(parse_song_info(dat) + '\n' + '\\bigskip\n')

                f.write('\n\\chordlist{{{}}}\\\\\n'.format(used_chords))

            elif re.match(r'\[[\w\-]+\*\]', tag.lower()):
                if args.compact:
                    f.write('\n\\textbf{{{}}}:~'.format(tag_string) + '{{\\sffamily {}}}\n'.format(inline_chord_line(dat.strip())) + '\\\\\n')
                else:
                    f.write('\n\\textbf{{{}}}:\\\\[1ex]\n'.format(tag_string) + '{{\\sffamily {}}}\n'.format(inline_chord_line(dat.strip())) + '\\\\\n')

            elif re.match(r'\[[\w\-]+\&?\]', tag.lower()):

                lines = [s for s in dat.splitlines() if s]

                # print(tag)

                if re.match(r'\[[\w\-]+\]', tag.lower()):
                    chordlines = lines[::2]
                    textlines = lines[1::2]

                    parsed = ''
                    for i in range(len(chordlines)):
                        chords, positions = chord_positions(chordlines[i])
                        # print(chords)
                        injected_line = inject_line(textlines[i], chords, positions)
                        # print(injected_line + "\\\\")
                        parsed += injected_line + '\\\\\n'

                elif re.match(r'\[[\w\-]+\&\]', tag.lower()):
                    parsed = '\\\\\n'.join(lines) + '\\\\\n'

                else:
                    print("Unidentified tag {}".format(tag))
                    raise

                parsed = parsed.replace(' ','~')

                if args.compact:
                    f.write('\n\\textbf{{{}}}:~'.format(tag_string))
                else:
                    f.write('\n\\textbf{{{}}}:\\\\[1ex]\n'.format(tag_string))

                f.write('{{\\sffamily {}}}\n'.format(parsed))

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

parser = argparse.ArgumentParser(description='Preprocessing...')

parser.add_argument('--capo', action='store_true')
parser.add_argument('--compact', action='store_true')
parser.add_argument('--note', action='store_true')
parser.add_argument('--strumming', action='store_true')

args = parser.parse_args()

make_sure_path_exists('songs_tex')

for song in get_all_files_from('songs_txt'):
    print("Preprocessing song {}".format(song))
    split_song('songs_txt/'+song, 'songs_tex')
