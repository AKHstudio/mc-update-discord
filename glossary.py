import requests , os
from dotenv import load_dotenv

load_dotenv()

url = "https://api-free.deepl.com/v2/glossaries"
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY" , os.getenv("DEEPL_API_KEY"))

if DEEPL_API_KEY is None:
    print("DEEPL_API_KEY not found")
    exit(1)

source_lang = 'EN'
target_lang = 'JA'


if os.path.exists("old_glossary.csv"):
    with open("old_glossary.csv", "r" , encoding="UTF-8") as f:
        old_entries = f.read()
else:
    old_entries = None

if os.path.exists("glossary_id.txt"):
    with open("glossary_id.txt", "r" , encoding="UTF-8" ) as f:
        old_glossary_id = f.read()
else:
    old_glossary_id = None

if os.path.exists("glossary.csv"):
    with open("glossary.csv", "r" , encoding="UTF-8") as f:
        entries = f.read()
        if old_entries == entries:
            print("変更がないため処理を終了します。")
            exit(0)
else:
    print("glossary.csv not found 登録する用語が見つかりませんでした。")
    print("処理を終了します。")
    exit(0)

headers = {
    "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
}

params = {
    "name": "minecraft changelog",
    "source_lang": source_lang,
    "target_lang": target_lang,
    "entries": entries,
    "entries_format" : "csv",
}

result = requests.post(url, data=params , headers=headers)

if result.status_code != 201:
    print(result.status_code)
    print(result.text)
    exit(1)

# print(result.json())    

with open("old_glossary.csv" , "w") as f:
    f.write(entries)

with open("glossary_id.txt" , "w") as f:
    f.write(result.json()["glossary_id"])

if old_glossary_id is not None:
    # delete old glossary
    result = requests.delete(f"{url}/{old_glossary_id}" , headers=headers)

    if result.status_code != 204:
        print(result.status_code)
        print(result.text)
        exit(1)
