import json
# JSON 파일 읽기
with open('json/2024-06-18/Narticles_5.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

print(data)
