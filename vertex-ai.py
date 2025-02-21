#!/usr/bin/python3

import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason
import vertexai.generative_models as generative_models


def generate():
  vertexai.init(project="<project_id>", location="us-central1")
  model = GenerativeModel(
    "gemini-1.5-pro",
    system_instruction=[
        'Вы - переводчик-эксперт.',
        'Ваша задача - перевести текст с китайского на русский.',
        'Используйте длинное тире в диалогах.',
        'Используйте кавычки-ёлочки.',
        'При необходимости используйте букву "ё".',
        'Пожалуйста, верните только точный перевод документа.',

    ],
  )
  responses = model.generate_content(
      [text1],
      generation_config=generation_config,
      safety_settings=None,
  )

  print(responses)
  with open("result.txt", "w") as output:
    for c in responses.candidates:
      for part in c.content.parts:
        output.write(part.text)

text1 = """
"""

generation_config = {
    "candidate_count": 1,
    "max_output_tokens": 8192,
    "temperature": 0,
}

generate()
