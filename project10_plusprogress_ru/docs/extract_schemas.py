# extract_schemas.py
import json
import yaml

# Читаем swagger.json
with open('swagger.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Извлекаем schemas
schemas = data.get('components', {}).get('schemas', {})

# Сохраняем JSON
with open('schemas.json', 'w', encoding='utf-8') as f:
    json.dump(schemas, f, indent=2, ensure_ascii=False)

# Сохраняем YAML
with open('schemas.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(schemas, f, allow_unicode=True, indent=2)

print(f'✅ Найдено {len(schemas)} схем')
print('✅ Сохранено в schemas.json и schemas.yaml')