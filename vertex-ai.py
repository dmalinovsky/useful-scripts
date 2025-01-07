#!/usr/bin/python

import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason
import vertexai.generative_models as generative_models


def generate():
  vertexai.init(project="<replace with a project id>", location="us-central1")
  model = GenerativeModel(
    "gemini-1.5-pro-002",
  )
  responses = model.generate_content(
      [text1],
      generation_config=generation_config,
      safety_settings=safety_settings,
  )

  print(responses)
  with open("result.txt", "w") as output:
    for c in responses.candidates:
      for part in c.content.parts:
        output.write(part.text)

text1 = """You are an expert Translator. You are tasked to translate documents from zh to ru. Use em dashes in dialogs. Use "ё" letter where applicable. Transliterate all names to Russian. Please provide an accurate translation of this document and return translation text only:
"""

generation_config = {
    "candidate_count": 1,
    "max_output_tokens": 8192,
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 1,
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
]

generate()
