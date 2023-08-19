import json
import argparse

from llama_cpp import Llama

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", type=str, default="../Llama/models/7B/ggml-model.bin")
args = parser.parse_args()

llm = Llama(model_path=args.model)

stream = llm( 
            "Prompt test",
            stream=True,
        )

text = ""
for output in stream:
    text += output['choices'][0]['text']
    print(text)