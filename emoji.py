from transformers import pipeline

pipe = pipeline('text2text-generation', model="cardiffnlp/flan-t5-base-tweet-emoji")
output = pipe("Louis Loudlinson is back with 16 and 18 secs ")
print(output)