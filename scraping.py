import os , re , requests,json
from time import sleep
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from get_chrome_driver import GetChromeDriver


# 環境変数の読み込み
load_dotenv()

# 環境変数を取得
DEEPL_API_KEY =  os.environ.get("DEEPL_API_KEY" , os.getenv("DEEPL_API_KEY")) 
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL" , os.getenv("DISCORD_WEBHOOK_URL"))

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

# url
minecraft_changelogs_url = "https://feedback.minecraft.net/hc/en-us/sections/360001186971-Release-Changelogs"

get_driver = GetChromeDriver()
get_driver.install()
options = webdriver.ChromeOptions()
options.add_argument('--headless')
# driver
driver = webdriver.Chrome(options=options)

try:
    # スクレイピング
    driver.get(minecraft_changelogs_url)
    # ページのソースを取得
    html = driver.page_source
    # BeautifulSoupでパース
    soup = BeautifulSoup(html, "html.parser")
    # 新しい投稿を取得
    new_post = soup.find(class_="article-list-link", string=re.compile("Bedrock"), href=True)
    
    # print(new_post)

    # スクレイピングログを取得
    if os.path.exists("scraping.log"):
        with open("scraping.log", "r" , encoding="UTF-8") as f:
            scraping_log = f.read()
    else:
        scraping_log = None

    # ログと取得した投稿が一致しているか確認
    if scraping_log == new_post.text:
        print("新しい投稿はありません。")
    else:
        # 投稿をスクレイピング
        driver.get('https://feedback.minecraft.net' + new_post["href"])
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        artical_body = soup.find(class_="article-body")

        artical_h2 = artical_body.find_all("h2")
        artical_ul = artical_body.find_all("ul")

        text_h2 = deepl_translate([h2.text for h2 in artical_h2])
        text_h2_translate = [h2["text"] for h2 in text_h2["translations"]]

        changelog = ""

        for h2 , ul in zip(text_h2_translate , artical_ul):
            changelog += f"## {h2}\n"
            
            li_list = ul.find_all("li")
            text_li = deepl_translate([li.text for li in li_list])
            text_li_translate = [li["text"] for li in text_li["translations"]]

            for li in text_li_translate:
                if "修正" in str(li):
                    changelog += f"- \N{Bug}{li}\n"
                else:
                    changelog += f"- {li}\n"

        discord_webhook_data = {
            "content": f"# {new_post.text}\nhttps://feedback.minecraft.net{new_post['href']}\n" + changelog,
            "username": "Minecraft Changelogs",
            "avatar_url": "https://github.com/AKHstudio/mc-update-discord/blob/main/icon/snail2.png"
        }

        # Discordに投稿
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(discord_webhook_data), headers={"Content-Type": "application/json"})

        # レスポンス確認
        if response.status_code == 204:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")

        # ログを更新
        with open("scraping.log", "w" , encoding="UTF-8") as f:
            f.write(new_post.text)
except Exception as e:
    print(f"エラーが発生しました: {e}")
    exit(1)
finally:
    driver.close()