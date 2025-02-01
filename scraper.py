import os , re , requests,json
from time import sleep
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from get_chrome_driver import GetChromeDriver
from datetime import datetime
from markitdown import MarkItDown
import traceback
from typing import Literal

# 環境変数の読み込み
load_dotenv()

DEEPL_API_KEY =  os.environ.get("DEEPL_API_KEY" , os.getenv("DEEPL_API_KEY")) 
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL" , os.getenv("DISCORD_WEBHOOK_URL"))
GLOSSARY_ID = os.environ.get("GLOSSARY_ID" ,  os.getenv("GLOSSARY_ID"))
SCRAPING_LOG = os.environ.get("SCRAPING_LOG" , None)
SCRAPING_BETA_LOG = os.environ.get("SCRAPING_BETA_LOG" , None)

class Scraper:
    """
    Minecraftの更新情報をスクレイピングしてDiscordに投稿するクラスです
    """


    def __init__(self, type: Literal["Release", "Beta-and-Preview"], username="Minecraft Release Changelog", avatar_url="https://raw.githubusercontent.com/AKHstudio/mc-update-discord/refs/heads/main/icon/snail2.png"):
        """
        Minecraftの更新情報をスクレイピングしてDiscordに投稿するクラス
        """
        self.type = type
        if type == "Release":
            self.url = "https://feedback.minecraft.net/hc/en-us/sections/360001186971-Release-Changelogs"
        elif type == "Beta-and-Preview":
            self.url = "https://feedback.minecraft.net/hc/en-us/sections/360001185332-Beta-and-Preview-Information-and-Changelogs"
        else:
            print("typeはReleaseかBeta-and-Previewを指定してください。")
            exit(1)
        self.username = username
        self.avatar_url = avatar_url

        # get_driver = GetChromeDriver()
        # get_driver.install()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        # driver
        self.driver = webdriver.Chrome(options=options)

        # 定義
        self.new_post = None

    def deepl_translate(self,text: str | list[str]):
        """
        DeepLを使って翻訳する関数
        """
        source_lang = 'EN'
        target_lang = 'JA'
        url = "https://api-free.deepl.com/v2/translate"

        headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
        }
        params = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "glossary_id": GLOSSARY_ID
        }
        response = requests.post(url,  headers=headers, data=params)
        print(response.json())
        sleep(1)
        return response.json()

    def get(self):
        """
        スクレイピングしてDiscordに投稿する関数
        """
        try:
            # スクレイピング
            self.driver.get(self.url)
            # ページのソースを取得
            html = self.driver.page_source
            # BeautifulSoupでパース
            soup = BeautifulSoup(html, "html.parser")
            # 新しい投稿を取得
            if self.type == "Release":
                self.new_post = soup.find(class_="article-list-link", string=re.compile("Bedrock"), href=True)
            else:
                self.new_post = soup.find(class_="article-list-link" ,href=True)

            if not self.new_post:
                print("投稿が見つかりませんでした。")
                exit(1)

            # ログと取得した投稿が一致しているか確認
            if SCRAPING_LOG == self.new_post.text:
                print("新しい投稿はありません。")
                exit(0)
            else:
                # 投稿をスクレイピング
                self.driver.get('https://feedback.minecraft.net' + self.new_post["href"])
                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                artical_body = soup.find(class_="article-body")

                if not artical_body:
                    print("artical_bodyが取得できませんでした。")
                    exit(1)

                for img in artical_body.find_all("img", src=True):
                    img["src"] = "https://feedback.minecraft.net" + img["src"]

                #  h1 タグを取得
                features = artical_body.find("h1")

                if not features:
                    print("featuresが取得できませんでした。")
                    exit(1)
                
                # h1 の次の要素を取得し続ける
                extracted_html = [features.prettify()]
                current = features.find_next_sibling()
                while current:
                    extracted_html.append(str(current))
                    current = current.find_next_sibling()
                    if current and current.name in ["h1" , "footer"]:  # 次の h1 が来たら終了
                        break

                
                extracted_html = "".join(extracted_html)

                extracted_soup = BeautifulSoup(extracted_html , "html.parser")

                text_elements = [tag for tag in extracted_soup.find_all(string=True) if tag.parent.name not in ["script", "style" , "code"] and tag.strip() and tag not in ["MCPE" , "©"]]
                translate_texts = self.deepl_translate([text.strip() for text in text_elements])
                
                for text , translate_text in zip(text_elements , translate_texts["translations"]):
                    text.replace_with(translate_text["text"])
                
                with open("changelog.html" , "w" , encoding="UTF-8") as f:
                    f.write(extracted_soup.prettify())
            

                markitdown = MarkItDown()
                changelog = markitdown.convert("changelog.html")
            

                farst_p = artical_body.find("p").text

                if not farst_p:
                    print("farst_pが取得できませんでした。")
                    print(farst_p)
                    exit(1)

                date_obj = datetime.strptime(farst_p.replace("Posted:" , "").strip(), '%d %B %Y')
                date_str = date_obj.strftime('%Y/%m/%d')

                discord_webhook_data = {
                    "content": f"# {self.new_post.text}\nhttps://feedback.minecraft.net{self.new_post['href']}\n\n**投稿日 : {date_str}**\n" + re.sub(r"[*+]" , "-" , changelog.text_content) + "\n### <:snail:1232230937681596426> and more...",
                    "username": self.username,
                    "avatar_url": self.avatar_url
                }

                # Discordに投稿
                response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(discord_webhook_data), headers={"Content-Type": "application/json"})

                # レスポンス確認
                if response.status_code == 204:
                    print("Message sent successfully!")
                else:
                    print(f"Failed to send message. Status code: {response.status_code}")

                # ログを更新
                if self.type == "Release":
                    with open("scraping-release.log", "w" , encoding="UTF-8") as f:
                        f.write(self.new_post.text)
                else:
                    with open("scraping-beta.log", "w" , encoding="UTF-8") as f:
                        f.write(self.new_post.text)
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            traceback.print_exc()
            exit(1)
        finally:
            self.driver.close()