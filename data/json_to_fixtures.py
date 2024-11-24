import json

with open('ingredients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

formatted_data = []
for item in data:
    formatted_item = {
        "model": "recipes.ingredient",
        "fields": {
            "name": item["name"],
            "measurement_unit": item["measurement_unit"]
        }
    }
    formatted_data.append(formatted_item)

with open('ingredients_formatted.json', 'w', encoding='utf-8') as f:
    json.dump(formatted_data, f, ensure_ascii=False, indent=2)
