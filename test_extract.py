import drive, extract, json

doc = drive.list_docs()[0]
print(f"Testing extraction on: {doc['name']}")

text = drive.get_doc_text(doc["id"])
result = extract.extract_action_items(text)
print(json.dumps(result, indent=2))