#!/usr/bin/env python3
"""Quick and dirty way to convert manual footnotes to the real ones.
We assume that a footnote has "[1]" form and takes a single paragraph."""

import re
import sys

from bs4 import BeautifulSoup

FOOTNOTE_REGEXP = re.compile('\[\d+\]')
ID_PREFIX = 'note'
note_id = 1


def fix_notes(fname):
    f = open(fname)
    soup = BeautifulSoup(f, 'xml')
    note_body = soup.new_tag('body')
    note_body['name'] = 'notes'
    soup.append(note_body)

    for section in soup.find_all('section'):
        visited = set()
        for tag in section.find_all(string=FOOTNOTE_REGEXP):
            parent = tag.parent
            new_text = str(parent)
            for substr in re.findall(FOOTNOTE_REGEXP, tag.text):
                if substr in visited:
                    # Skipping already visited footnote.
                    continue
                visited.add(substr)

                # Find the tag with the footnote text.
                footnotes = section.find_all(string=re.compile(re.escape(substr)), limit=2)
                if len(footnotes) != 2:
                    print("Can't find footnote", repr(substr))
                    continue
                footnote = footnotes[-1]
                idx = append_footnote(soup, note_body, footnote.parent)

                # Insert link to the new footnote.
                new_text = new_text.replace(substr,
                    '<a l:href="#note%d" type="note">%s</a>' % (idx, substr))
            new_tag = BeautifulSoup(new_text, 'xml')
            parent.replace_with(new_tag)

    f.close()
    return soup


def append_footnote(soup, note_body, footnote):
    global note_id

    note = soup.new_tag('section')
    note['id'] = ID_PREFIX + str(note_id)
    note.append(footnote)
    note_body.append(note)

    note_id += 1
    return note_id - 1


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("""Usage: %s fb2_file""" % sys.argv[0])
        sys.exit(1)

    input_file = sys.argv[1]
    soup = fix_notes(input_file)
    with open(input_file, 'w') as f:
        f.write(str(soup))
