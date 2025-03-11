#!/usr/bin/python3

import base64
import re
import sys
import vertexai
from time import time
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason


#SEPARATOR = r'(Chapter \(\d+\))'
SEPARATOR = r'(第\d+章)'
INPUT_ENCODING = 'utf-8'
OUTPUT = 'result.txt'
STEP = 500
MIN_CHARS = 20


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
    hi_utf = sum(1 for c in text if ord(c) > 10000)
    if hi_utf > l / 2:
        return False
    return True

def generate(model, text, separator):
    start_time = time()
    try:
        responses = model.generate_content(
            [text],
            generation_config=generation_config,
            safety_settings=None,
        )
    except Exception as e:
        print("Can't process input:", e)
        return False

    cnt = 0

    with open(OUTPUT, "a") as output:
        output.write("\n" + separator + "\n\n")
        for c in responses.candidates:
            for part in c.content.parts:
                if has_repeating_chars(part.text) or not is_translated(text):
                    return False
                new_text = part.text.replace("\n\n", "\n")
                output.write(new_text)
                cnt += len(new_text)

    print('Written symbols:', cnt, 'for time:', int(time() - start_time), 'chapter:', separator)
    if cnt == 0:
        print('No output received')
        print(responses)
        return False
    return True

generation_config = {
    "candidate_count": 1,
    "max_output_tokens": 8192,
    "temperature": 0,
}
system_instruction = [
        'Вы - переводчик-эксперт.',
        'Ваша задача - сделать перевод текста с китайского на русский.',
        'Используйте длинное тире в диалогах.',
        'Используйте кавычки-ёлочки.',
        'При необходимости используйте букву "ё".',
        'Пожалуйста, верните только точный перевод документа.',
]

vertexai.init(project="<project_id>", location="us-central1")

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

    model = GenerativeModel(
        "gemini-2.0-pro-exp-02-05",
        system_instruction=system_instruction
    )
    fallback_model = GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=system_instruction
    )
    parts = re.split(SEPARATOR, input_text, flags=re.IGNORECASE)
    sep = ''
    for part, next_sep in zip(parts[::2], parts[1::2] + ['']):
        if len(part) == 0:
            sep = next_sep
            continue
        print('Processing symbols:', len(part))
        if not generate(model, part, sep):
            print('Retrying with the fallback model...')
            if not generate(fallback_model, part, sep):
                sys.exit(1)
                print('Failed.')
        sep = next_sep
