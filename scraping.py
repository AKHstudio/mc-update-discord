import os , re , requests
from time import sleep
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver

# 環境変数の読み込み
load_dotenv()

# 環境変数を取得
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

def deepl_translate(text: str | list[str]):
    source_lang = 'EN'
    target_lang = 'JA'
    url = "https://api-free.deepl.com/v2/translate"
    
    with open("glossary_id.txt" , "r" , encoding="UTF-8") as f:
        glossary_id = f.read()

    headers = {
    "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
    }
    params = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "glossary_id": glossary_id
    }
    response = requests.post(url,  headers=headers, data=params)
    # print(response.json())
    sleep(2)
    return response.json()

def scraping():
    print('Scraping data from the web')
    return 'data'