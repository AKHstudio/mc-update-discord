import requests , os
from dotenv import load_dotenv

load_dotenv()

url = "https://api-free.deepl.com/v2/glossaries"
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY" , os.getenv("DEEPL_API_KEY"))
GLOSSARY_ID = os.environ.get("GLOSSARY_ID" , None)
OLD_GLOSSARY_CSV = os.environ.get("OLD_GLOSSARY_CSV" , None)

if DEEPL_API_KEY is None:
    print("DEEPL_API_KEY not found")
    exit(1)

source_lang = 'EN'
target_lang = 'JA'


if os.path.exists("glossary.csv"):
    with open("glossary.csv", "r" , encoding="UTF-8") as f:
        entries = f.read()
        print(OLD_GLOSSARY_CSV)
        print(entries.replace("\n" , ""))
        if OLD_GLOSSARY_CSV == entries.replace("\n" , ""):
            print("glossary.csv not changed 登録する用語が変更されていません。")
            exit(0)
else:
    print("glossary.csv not found 登録する用語が見つかりませんでした。")
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

with open("glossary_id.txt" , "w") as f:
    f.write(result.json()["glossary_id"])

if GLOSSARY_ID is not None:
    # delete old glossary
    result = requests.delete(f"{url}/{GLOSSARY_ID}" , headers=headers)

    if result.status_code != 204:
        print(result.status_code)
        print(result.text)
        exit(1)
