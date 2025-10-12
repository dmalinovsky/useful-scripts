#!/usr/bin/python3

import base64
import os
from google import genai
from google.genai import types


text = """
"""

system_instruction=[
    'Вы - переводчик-эксперт.',
    'Ваша задача - сделать художественный перевод текста с китайского на русский.',
    'Используйте длинное тире в диалогах.',
    'Используйте кавычки-ёлочки.',
    'При необходимости используйте букву "ё".',
    'Добавляйте сноски для китайских идиом или непонятных мест.',
    'Пожалуйста, верните только перевод документа.',
]

client = genai.Client(
    vertexai=True,
    api_key=os.environ.get("GOOGLE_CLOUD_API_KEY"),
)
response = client.models.generate_content(
    model='gemini-2.5-pro',
    contents=text,
    config=types.GenerateContentConfig(
        candidate_count=1,
        max_output_tokens=65535,
        temperature=0,
        safety_settings = [types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="OFF"
        ),types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="OFF"
        ),types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="OFF"
        ),types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="OFF"
        )],
        system_instruction=system_instruction,
        thinking_config=types.ThinkingConfig(
            thinking_budget=128,
        ),
        http_options={'timeout': 120 * 1000}
    ),
)

cnd = response.candidates[0]

with open("result.txt", "w") as output:
    for part in cnd.content.parts:
        output.write(part.text)

print(response.usage_metadata.model_dump_json(indent=2))
print(cnd.finish_reason)
