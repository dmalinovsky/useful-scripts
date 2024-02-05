#!/usr/bin/env python3

import sys
from ebooklib import epub


def update_epub(file_name):
    book = epub.read_epub(file_name, {'ignore_ncx': True})
    book.set_language('ru')
    epub.write_epub(file_name, book, {})


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("""Usage: %s epub_file""" % sys.argv[0])
        sys.exit(1)

    input_file = sys.argv[1]
    update_epub(input_file)
