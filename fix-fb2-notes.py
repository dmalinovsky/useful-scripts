#!/usr/bin/env python3
"""Convert manual or pseudo-linked footnotes in FB2 files to standard FB2 notes."""

import re
import sys
from bs4 import BeautifulSoup, NavigableString, Tag

INLINE_MARKER_RE = re.compile(r'\[(\d+)\]')
START_MARKER_RE = re.compile(r'^\s*\[(\d+)\]\s*')
SEPARATOR_SUBTITLE_RE = re.compile(r'^[\s*•—–\-]+$')
OLD_FN_ID_RE = re.compile(r'^fn-p-\d+$')
ID_PREFIX = 'note'


def get_xlink_attr(soup):
    """Detect the xlink prefix used in <FictionBook> (usually 'l:href' or 'xlink:href')."""
    fb = soup.find('FictionBook')
    if fb:
        for attr, val in fb.attrs.items():
            if val == 'http://www.w3.org/1999/xlink' and attr.startswith('xmlns:'):
                prefix = attr.split(':', 1)[1]
                return f'{prefix}:href'
    return 'l:href'


def get_next_note_index(soup):
    """Avoid ID collisions if the book already contains noteN sections."""
    max_id = 0
    pattern = re.compile(r'^' + re.escape(ID_PREFIX) + r'(\d+)$')
    for sec in soup.find_all('section', id=pattern):
        m = pattern.match(sec['id'])
        if m:
            max_id = max(max_id, int(m.group(1)))
    return max_id + 1


def get_notes_body(soup):
    note_body = soup.find('body', attrs={'name': 'notes'})
    if note_body:
        return note_body

    note_body = soup.new_tag('body')
    note_body['name'] = 'notes'
    main_body = soup.find('body')
    if main_body:
        main_body.insert_after(note_body)
    else:
        root = soup.find('FictionBook') or soup
        root.append(note_body)

    return note_body


def is_leaf_section(section):
    return section.find('section') is None


def extract_footnote_blocks(section):
    """Find footnote definitions at the bottom of a leaf section.

    Walks top-level children from the end of the section upwards so that
    dialogue or body paragraphs starting with '[1]' earlier in the chapter
    are not mistaken for footnotes, while multi-paragraph footnotes at the end
    are captured completely.
    """
    children = [ch for ch in section.children if isinstance(ch, Tag)]
    if not children:
        return {}, None

    # Find all top-level <p> tags that start with [N]
    marker_indices = []
    for i, el in enumerate(children):
        if el.name == 'p':
            m = START_MARKER_RE.match(el.get_text())
            if m:
                marker_indices.append((i, m.group(1)))

    if not marker_indices:
        return {}, None

    # Group contiguous footnote blocks anchored at the end of the section.
    # Every paragraph from a footnote start up to the next footnote start
    # (or end of section) belongs to that footnote.
    footnotes = {}
    end_idx = len(children)

    # Verify that the last marker block reaches the end of the section
    # (ignoring any non-footnote trailing empty tags if present).
    first_footnote_start_idx = None

    for pos in range(len(marker_indices) - 1, -1, -1):
        idx, num = marker_indices[pos]
        block_tags = children[idx:end_idx]

        # Ensure the block only contains valid footnote content tags (e.g. <p>, <empty-line>, <poem>, <cite>)
        # and not chapter <title>. If there is a <subtitle> inside, stop before it unless it's trailing.
        if any(t.name == 'title' for t in block_tags):
            break

        # Check if this [N] also appears earlier in the section (actual reference in body text)
        if not has_body_reference(children[:idx], num):
            break

        footnotes[num] = block_tags
        first_footnote_start_idx = idx
        end_idx = idx

    separator = None
    if first_footnote_start_idx is not None and first_footnote_start_idx > 0:
        prev_tag = children[first_footnote_start_idx - 1]
        if prev_tag.name == 'subtitle' and SEPARATOR_SUBTITLE_RE.match(prev_tag.get_text()):
            separator = prev_tag

    return footnotes, separator


def has_body_reference(body_Elements, num):
    target = f'[{num}]'
    for el in body_Elements:
        if target in el.get_text():
            return True
    return False


def strip_leading_marker(p_tag, num):
    """Remove leading '[num]' (and its wrapper <a> if linked) from the first footnote paragraph,
    preserving surrounding wrappers like <emphasis>."""
    pattern = re.compile(r'^\s*\[' + re.escape(num) + r'\]\s*')

    # First check if the first non-whitespace child (possibly inside <emphasis>) is an <a>[num]</a>
    curr = p_tag
    while isinstance(curr, Tag):
        first_sig = None
        for child in curr.contents:
            if isinstance(child, NavigableString) and not child.strip():
                continue
            first_sig = child
            break

        if first_sig is None:
            break

        if isinstance(first_sig, Tag) and first_sig.name == 'a':
            if first_sig.get_text().strip() == f'[{num}]':
                # Strip leading whitespace after </a> in the next text node
                nxt = first_sig.next_sibling
                if isinstance(nxt, NavigableString):
                    nxt.replace_with(re.sub(r'^\s+', '', str(nxt)))
                first_sig.decompose()
                return
            break
        elif isinstance(first_sig, NavigableString):
            new_text, count = pattern.subn('', str(first_sig), count=1)
            if count > 0:
                first_sig.replace_with(new_text)
                return
            break
        else:
            curr = first_sig


def replace_body_references(section, footnotes_map, soup, href_attr):
    """Replace inline [N] or <a>[N]</a> in body elements with <a l:href="#noteX" type="note">[N]</a>."""
    converted_nums = set()

    # 1. Handle already-linked references: <a ...>[N]</a>
    for a_tag in list(section.find_all('a')):
        m = re.fullmatch(r'\s*\[(\d+)\]\s*', a_tag.get_text())
        if not m:
            continue
        num = m.group(1)
        if num not in footnotes_map:
            continue

        note_id_str = footnotes_map[num]
        # Clear old attributes (l:href, xlink:href, href, etc.) and set standard FB2 note attributes
        a_tag.attrs.clear()
        a_tag[href_attr] = f'#{note_id_str}'
        a_tag['type'] = 'note'
        a_tag.string = f'[{num}]'
        converted_nums.add(num)

    # 2. Handle plain-text references: [N] outside of <a> tags
    for text_node in list(section.find_all(string=INLINE_MARKER_RE)):
        if text_node.find_parent('a') is not None:
            continue

        text = str(text_node)
        matches = list(INLINE_MARKER_RE.finditer(text))
        if not any(m.group(1) in footnotes_map for m in matches):
            continue

        new_nodes = []
        last_idx = 0
        changed = False

        for m in matches:
            num = m.group(1)
            if num not in footnotes_map:
                continue

            if m.start() > last_idx:
                new_nodes.append(NavigableString(text[last_idx:m.start()]))

            a_tag = soup.new_tag('a')
            a_tag[href_attr] = f'#{footnotes_map[num]}'
            a_tag['type'] = 'note'
            a_tag.string = f'[{num}]'
            new_nodes.append(a_tag)

            last_idx = m.end()
            changed = True
            converted_nums.add(num)

        if changed:
            if last_idx < len(text):
                new_nodes.append(NavigableString(text[last_idx:]))
            for node in reversed(new_nodes):
                text_node.insert_after(node)
            text_node.extract()

    return converted_nums


def clean_old_ids(root):
    for tag in root.find_all(attrs={'id': OLD_FN_ID_RE}):
        del tag['id']


def fix_notes(fname):
    with open(fname, 'rb') as f:
        raw_bytes = f.read()

    soup = BeautifulSoup(raw_bytes, 'xml')
    href_attr = get_xlink_attr(soup)
    next_id = get_next_note_index(soup)

    main_body = soup.find('body')
    if not main_body:
        print('No <body> found in the file.')
        return soup, 0

    note_cnt = 0
    note_body = None

    for section in main_body.find_all('section'):
        if not is_leaf_section(section):
            continue

        footnotes_blocks, separator = extract_footnote_blocks(section)
        if not footnotes_blocks:
            continue

        # Preserve numerical order of footnotes found in this section
        ordered_nums = [
            num for num in sorted(footnotes_blocks.keys(), key=lambda x: int(x))
        ]

        # Detach footnote blocks from the chapter first so body search doesn't touch them
        for num in ordered_nums:
            for tag in footnotes_blocks[num]:
                tag.extract()

        # Assign target note IDs
        footnotes_map = {}
        for num in ordered_nums:
            footnotes_map[num] = f'{ID_PREFIX}{next_id}'
            next_id += 1

        converted_nums = replace_body_references(section, footnotes_map, soup, href_attr)

        if converted_nums:
            if note_body is None:
                note_body = get_notes_body(soup)

            if separator is not None:
                separator.decompose()

            for num in ordered_nums:
                if num not in converted_nums:
                    # Put back untouched blocks if for some reason not referenced
                    for tag in footnotes_blocks[num]:
                        section.append(tag)
                    continue

                blocks = footnotes_blocks[num]
                strip_leading_marker(blocks[0], num)

                note_sec = soup.new_tag('section', id=footnotes_map[num])
                title_tag = soup.new_tag('title')
                title_p = soup.new_tag('p')
                title_p.string = num
                title_tag.append(title_p)
                note_sec.append(title_tag)

                for tag in blocks:
                    clean_old_ids(tag)
                    note_sec.append(tag)

                note_body.append(note_sec)
                note_cnt += 1

            clean_old_ids(section)
        else:
            # Restore extracted tags if nothing was converted
            for num in ordered_nums:
                for tag in footnotes_blocks[num]:
                    section.append(tag)

    print('Footnotes processed:', note_cnt)
    return soup, note_cnt


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print(f'Usage: {sys.argv[0]} fb2_file')
        sys.exit(1)

    input_file = sys.argv[1]
    soup, note_cnt = fix_notes(input_file)
    if note_cnt > 0:
        encoding = soup.original_encoding or 'utf-8'
        xml_bytes = soup.encode(encoding=encoding)
        with open(input_file, 'wb') as f:
            f.write(xml_bytes)
    else:
        print('Nothing to change in the book.')
