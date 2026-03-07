import json
import markdownify


def swagger_to_markdown(swagger_json_path, output_md_path):
    # Читаем JSON
    with open(swagger_json_path, 'r', encoding='utf-8') as f:
        swagger = json.load(f)

    # Формируем Markdown
    md = []
    md.append(f"# {swagger.get('info', {}).get('title', 'API')}\n")
    md.append(f"*Версия: {swagger.get('info', {}).get('version', '')}*\n")
    md.append(f"{swagger.get('info', {}).get('description', '')}\n")

    md.append("## 🔐 Авторизация\n")
    md.append("Для доступа к API требуется токен. Добавьте заголовок:\n")
    md.append("```\nAuthorization: Token <ваш_токен>\n```\n")

    # Эндпоинты
    md.append("## 📡 Эндпоинты\n")

    for path, methods in swagger.get('paths', {}).items():
        for method, details in methods.items():
            md.append(f"### {method.upper()} `{path}`\n")
            md.append(f"{details.get('summary', '')}\n")
            md.append(f"{details.get('description', '')}\n")

            # Параметры
            if 'parameters' in details:
                md.append("**Параметры:**\n")
                for param in details['parameters']:
                    required = "✅" if param.get('required') else "❌"
                    md.append(f"- `{param['name']}` {required} {param.get('description', '')}\n")

            # Ответы
            if 'responses' in details:
                md.append("\n**Ответы:**\n")
                for code, response in details['responses'].items():
                    md.append(f"- **{code}**: {response.get('description', '')}\n")

            md.append("\n---\n")

    # Модели данных (Schemas)
    if 'components' in swagger and 'schemas' in swagger['components']:
        md.append("## 📊 Модели данных (Schemas)\n")
        for schema_name, schema in swagger['components']['schemas'].items():
            md.append(f"### {schema_name}\n")
            md.append("```json\n")
            md.append(json.dumps(schema, indent=2, ensure_ascii=False))
            md.append("\n```\n")

    # Сохраняем
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f"✅ Конвертация завершена! Создан файл: {output_md_path}")


# Используйте:
swagger_to_markdown('schemas.json', 'API_Documentation.md')