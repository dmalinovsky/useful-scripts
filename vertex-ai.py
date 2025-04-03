#!/usr/bin/python3

import base64
from google import genai
from google.genai import types


text = """
"""

system_instruction=[
    'Вы - переводчик-эксперт.',
    'Ваша задача - сделать перевод текста с китайского на русский.',
    'Используйте длинное тире в диалогах.',
    'Используйте кавычки-ёлочки.',
    'При необходимости используйте букву "ё".',
    'Названия компаний должны быть приведены кириллицей.',
    'Пожалуйста, верните только точный перевод документа.',
]

client = genai.Client(
)
response = client.models.generate_content(
    model='gemini-2.0-pro-exp-02-05',
    #model='gemini-1.5-pro-002',
    contents=text,
    config=types.GenerateContentConfig(
        candidate_count=1,
        max_output_tokens=65535,
        temperature=0,
        seed=1313,
        system_instruction=system_instruction,
        http_options={'timeout': 120 * 1000}
    ),
)

cnd = response.candidates[0]

with open("result.txt", "w") as output:
    for part in cnd.content.parts:
        output.write(part.text)

print(response.usage_metadata.model_dump_json(indent=2))
print(cnd.finish_reason)
