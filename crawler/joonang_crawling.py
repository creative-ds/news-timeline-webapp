import time, os
from selenium import webdriver
import requests
from bs4 import BeautifulSoup

from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

import time
from datetime import datetime

from pandas import Series as Series
from pandas import DataFrame as DataFrame
import logging

class JoongAngCrawler:
    def __init__(self, logger, start_meta):
        self.logger = logger

        # 드라이버 지정
        self.chrome_path = 'C:/Users/jin/chromedriver_win32/chromedriver.exe'
        self.option = webdriver.ChromeOptions()
        self.option.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 1
        })
        self.option.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=self.option, executable_path=self.chrome_path)
        
        self.url = "https://www.joongang.co.kr/society/accident"
        self.driver.get(self.url)

        self.start_meta = start_meta
        self.save_dir = './data/'

    def is_between(self, request: str, start: str, end: str) -> bool:
        """
        return: whether the request date is between start date and end date.
        """
        start = datetime.strptime(start, '%Y.%m.%d %H:%M')
        request = datetime.strptime(request, '%Y.%m.%d %H:%M')
        end = datetime.strptime(end, '%Y.%m.%d %H:%M')

        return end <= request <= start

    def is_before(self, request: str, base: str) -> bool:
        """
        return: whether the base date is the same as or immediately before the requested date.
        """
        request = datetime.strptime(request, '%Y.%m.%d %H:%M')
        base = datetime.strptime(base, '%Y.%m.%d %H:%M')

        return base <= request

    def finder(self, request_meta, page_num):
        print(f"{request_meta}의 기사를 찾으러 내려가겠습니다!")
        while True:
            # page_num = 0

            print ("로딩 중...")
            time.sleep(3)
            story_list = self.driver.find_element_by_css_selector("#story_list").find_elements_by_class_name("card_body")
            print("현재 페이지의 기사 수: ",len(story_list))

            # 24 articles in one page
            meta_start = self.driver.find_elements_by_class_name("date")[page_num*24] # 0
            meta_end = self.driver.find_elements_by_class_name("date")[(page_num+1)*24-1] # 23

            print(f"해당 범위에서 탐색 시작: {meta_start.text} ~ {meta_end.text}")

            if self.is_between(request_meta, meta_start.text, meta_end.text):
                for idx in range(page_num*24, (page_num+1)*24):
                    base_meta = story_list[idx].find_element_by_class_name("date")
                    if self.is_before(request_meta, base_meta.text):
                        # print(story_list[idx].find_element_by_class_name("headline").text)
                        # print(idx)
                        print("기사를 찾았습니다!")
                        return story_list[idx]
            else:
                print("현재 범위에서 찾고자 하는 날짜가 없습니다!")
                print("더 보기를 클릭합니다.")
                expand_button = self.driver.find_element_by_css_selector("#container > section > div > div.col_lg9 > section > div > a")
                # 버튼을 찾을 때까지 스크롤 이동
                # self.driver.execute_script('arguments[0].scrollIntoView(true);', expand_button)
                # self.driver.execute_script('window.scrollTo(0, 300);')
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#container > section > div > div.col_lg9 > section > div > a")))
                # 더보기 버튼 클릭
                expand_button.click()
                page_num+=1

    def crawling(self):
        start_page = self.finder(self.start_meta, 0)
        print(start_page.find_element_by_class_name("headline").text)


if __name__=="__main__":
    # logger
    logger = logging.getLogger("log")
    logger.setLevel(logging.INFO)
    file_handler= logging.FileHandler('./log/')

    formatter = logging.Formatter('%(asctime)s|%(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    crawler = JoongAngCrawler(logger,'2021.09.01 00:00')
    crawler.crawling()