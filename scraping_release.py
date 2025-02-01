# scraper.pyからScraperクラスをインポート

from scraper import Scraper


scraper = Scraper("Release" , username="Minecraft Release Changelog")

scraper.get()