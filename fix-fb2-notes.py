#!/usr/bin/env python3
"""Quick and dirty way to convert manual footnotes to the real ones.
We assume that a footnote has "[1]" form and takes a single paragraph."""

import re
import sys

from bs4 import BeautifulSoup

FOOTNOTE_REGEXP = re.compile(r'\[\d+\]')
ID_PREFIX = 'note'
note_id = 1


def fix_notes(fname):
    f = open(fname)
    soup = BeautifulSoup(f, 'xml')
    note_body = get_notes_body(soup)

    note_cnt = 0
    for section in soup.find_all('section'):
        visited = set()
        while True:
            section_notes = process_section(section, visited, soup, note_body)
            if section_notes == 0:
                break
            note_cnt += section_notes

    f.close()
    print('Footnotes processed:', note_cnt)
    return soup, note_cnt


def process_section(section, visited, soup, note_body):
    note_cnt = 0
    for tag in section.find_all(string=FOOTNOTE_REGEXP):
        parent = tag.parent
        new_xml = str(parent)
        for substr in re.findall(FOOTNOTE_REGEXP, tag.text):
            if substr in visited:
                # Skipping already visited footnote.
                continue
            visited.add(substr)

            # Find the tag with the footnote text.
            footnotes = section.find_all(string=re.compile(re.escape(substr)), limit=2)
            if len(footnotes) != 2:
                # Can't find footnote.
                continue
            footnote = footnotes[-1]
            idx = append_footnote(soup, note_body, footnote.parent)

            # Insert link to the new footnote.
            new_xml = new_xml.replace(substr,
                '<a l:href="#note%d" type="note">%s</a>' % (idx, substr))
            note_cnt += 1
        # Repeat again with updated DOM tree.
        if note_cnt > 0:
            new_parent = BeautifulSoup(new_xml, 'xml')
            parent.replace_with(new_parent)
            break

    return note_cnt


def append_footnote(soup, note_body, footnote):
    global note_id

    note = soup.new_tag('section')
    note['id'] = ID_PREFIX + str(note_id)
    note.append(footnote)
    note_body.append(note)

    note_id += 1
    return note_id - 1


def get_notes_body(soup):
    note_body = soup.find('body', attrs={'name': 'notes'})
    if note_body:
        return note_body

    note_body = soup.new_tag('body')
    note_body['name'] = 'notes'
    body = soup.find('body')
    body.insert_after(note_body)

    return note_body


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("""Usage: %s fb2_file""" % sys.argv[0])
        sys.exit(1)

    input_file = sys.argv[1]
    soup, note_cnt = fix_notes(input_file)
    if note_cnt > 0:
        with open(input_file, 'w') as f:
            f.write(str(soup))
    else:
        print('Nothing to change in the book.')
