#!/usr/bin/python3

import base64
import re
import sys
from time import time
from google import genai
from google.genai import types


SEPARATOR = r'(트레이드된 투수가 재능폭발 \d+화)\n'
#SEPARATOR = r'(第\d+章.+?)\n'
INPUT_ENCODING = 'utf-8'
OUTPUT = 'result.txt'
STEP = 500
MIN_CHARS = 20
RETRIES = 10
TIMEOUT_COEF = 25


def has_repeating_chars(text):
    for i in range(0, len(text), STEP):
        s = text[i:min(i+STEP, len(text))]
        if len(s) >= STEP and len(set(s)) < MIN_CHARS:
            print('Found repeating sequence:', s)
            return True

    return False

def is_translated(text):
    l = len(text)
    if l < MIN_CHARS:
        return True
    # Counts number of UTF symbols with high numbers, it's usually untranslated text.
    hi_utf = sum(1 for c in text if ord(c) > 1500)
    if hi_utf > l / 2:
        print('Text remained untranslated: %d out of %d' % (hi_utf, l))
        return False
    return True

def preprocess_text(text):
    # These repeating symbols result in repetitive output.
    text = re.sub(r'ㅋ+', 'ㅋ', text)
    text = re.sub(r'ㄱ+', 'ㄱ', text)
    text = re.sub(r'ㅑ+', 'ㅑ', text)
    text = re.sub(r'ㅓ+', 'ㅓ', text)
    text = re.sub(r'ㅠ+', 'ㅠ', text)
    text = re.sub(r'ㅅ+', 'ㅅ', text)
    return re.sub(r'오+', '오', text)

def generate(text, separator):
    if len(text) < MIN_CHARS:
        # Skipping too short chapter.
        return True

    start_time = time()
    #text = preprocess_text(text)
    try:
        responses = client.models.generate_content(
            model='gemini-2.5-pro-exp-03-25',
            contents=text,
            config=types.GenerateContentConfig(
                candidate_count=1,
                temperature=0,
                system_instruction=system_instruction,
                # Allow more processing time for longer text.
                # The coefficient is empirical value.
                http_options={'timeout': max(TIMEOUT_COEF * len(text), 30 * 1000)}
            ),
        )
    except Exception as e:
        print("Can't process input:", e)
        return False

    cnt = 0

    with open(OUTPUT, "a") as output:
        for c in responses.candidates:
            for part in c.content.parts:
                if has_repeating_chars(part.text) or not is_translated(part.text):
                    return False
                lines = part.text.splitlines()
                if not lines:
                    continue
                # Header.
                output.write("\n" + lines[0].rstrip('.') + "\n\n")
                # Body.
                for line in lines[1:]:
                    if line.strip() == "":
                        continue
                    output.write(line + "\n")
                    cnt += len(line) + 1

    print('Written symbols:', cnt, 'for time:', int(time() - start_time), 'chapter:', separator)
    if cnt == 0:
        print('No output received')
        print(responses)
        return False
    return True

system_instruction = [
        'Вы - переводчик-эксперт.',
        'Ваша задача - сделать перевод текста с корейского на русский.',
        'Используйте длинное тире в диалогах.',
        'Используйте кавычки-ёлочки.',
        'При необходимости используйте букву "ё".',
        'Имена должны переводиться двумя словами, а не тремя.',
        'Пожалуйста, верните только точный перевод документа.',
]

client = genai.Client()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("""Usage: %s txt_file""" % sys.argv[0])
        sys.exit(1)

    input_file = sys.argv[1]
    input_text = ''
    with open(input_file, 'r', encoding=INPUT_ENCODING) as f:
        input_text = f.read()

    with open(OUTPUT, 'w') as output:
        output.write('Starting output...\n')

    parts = re.split(SEPARATOR, input_text, flags=re.IGNORECASE)
    sep = ''
    for part, next_sep in zip(parts[::2], parts[1::2] + ['']):
        if len(part) == 0:
            sep = next_sep
            continue
        print('Processing symbols:', len(part))
        attempts = 0
        while not generate(part, sep):
            attempts += 1
            print('  Retry attempt #' + str(attempts) + '...')
            if attempts >= RETRIES:
                sys.exit(1)
                print('Failed.')
        sep = next_sep
