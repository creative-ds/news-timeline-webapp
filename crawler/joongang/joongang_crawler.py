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

import pandas as pd
from pandas import Series as Series
from pandas import DataFrame as DataFrame
import logging


class JoongAngCrawler:
    def __init__(self, logger, start_meta):
        self.logger = logger

        # 드라이버 지정
        self.chrome_path = 'C:/Users/jin/chromedriver_win32/chromedriver.exe'
        self.option = webdriver.ChromeOptions()
        self.option.add_argument("start-maximized")
        self.option.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 1
        })
        self.option.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=self.option, executable_path=self.chrome_path)
        
        self.url = "https://www.joongang.co.kr/society/accident"
        self.driver.get(self.url)

        self.action = ActionChains(self.driver)
        self.start_meta = start_meta

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
        self.logger.info(f"Finder Start! To Find {request_meta}")
        while True:
            # page_num = 0

            time.sleep(3)
            story_list = self.driver.find_element_by_css_selector("#story_list").find_elements_by_class_name("card_body")
            self.logger.info(f"Number of articles in current page: {len(story_list)}")

            # 24 articles in one page
            meta_start = self.driver.find_elements_by_class_name("date")[page_num*24] # 0
            meta_end = self.driver.find_elements_by_class_name("date")[(page_num+1)*24-1] # 23

            self.logger.info(f"Navigation in the range: {meta_start.text} ~ {meta_end.text}")

            if self.is_between(request_meta, meta_start.text, meta_end.text):
                for idx in range(page_num*24, (page_num+1)*24):
                    base_meta = story_list[idx].find_element_by_class_name("date")
                    if self.is_before(request_meta, base_meta.text):
                        # print(story_list[idx].find_element_by_class_name("headline").text)
                        # print(idx)
                        self.logger.info("Found Article!")

                        # 기사를 찾았으나 페이지의 마지막이라면 더보기 버튼 클릭 후 return해야함
                        if idx == (len(story_list)-1):
                            expand_button = self.driver.find_element_by_css_selector("#container > section > div > div.col_lg9 > section > div > a")
                            # 버튼을 찾을 때까지 대기
                            # WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#container > section > div > div.col_lg9 > section > div > a")))
                            # action = ActionChains(self.driver)
                            self.action.move_to_element(expand_button).perform()
                            # 더보기 버튼 클릭
                            expand_button.click()

                        return story_list, idx
            else:
                self.logger.info("Date is not included in the range.")
                self.logger.info("Click See More...")
                self.driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)

                expand_button = self.driver.find_element_by_css_selector("#container > section > div > div.col_lg9 > section > div > a")
                # 버튼을 찾을 때까지 대기
                #WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#container > section > div > div.col_lg9 > section > div > a")))
                #action = ActionChains(self.driver)
                self.action.move_to_element(expand_button).perform()
                # 더보기 버튼 클릭
                expand_button.click()
                page_num+=1

    def crawling(self):
        self.logger.info("=======Crawler Start!=======")
        story_list, idx = self.finder(self.start_meta, 0)
        print(story_list[idx].find_element_by_class_name("headline").text)

        df = pd.DataFrame(columns={'date', 'title', 'body', 'url'})
        
        cnt=0

        try:
            while cnt<10000:
                time.sleep(3)
                #WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#story_list")))
                story_list = self.driver.find_element_by_css_selector("#story_list").find_elements_by_class_name("card_body")

                print(f"기사 수: {len(story_list)} 현재 기사번호: {idx}")
                
                self.driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
                #WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#story_list")))
                date = story_list[idx].find_element_by_class_name("date").text
                title = story_list[idx].find_element_by_class_name("headline").text
                url = story_list[idx].find_element_by_css_selector("h2 > a").get_attribute("href")
                parent_window = self.driver.current_window_handle 

                print(date, title, url)

                # Get parent window
                parent_window = self.driver.current_window_handle 
                # Open "Bing" page in child window
                self.driver.execute_script("window.open('"+url+"')")
                # Get list of all windows currently opened (parent + child)
                all_windows = self.driver.window_handles 
                # Get child window
                child_window = [window for window in all_windows if window != parent_window][0] 
                self.driver.switch_to.window(child_window) 
                time.sleep(1)
                body = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#article_body"))).text
                # Close child window
                self.driver.close() 
                # Switch back to parent window
                self.driver.switch_to.window(parent_window) 

                df=df.append({'date' : date , 'title' : title, 'body' : body, 'url' : url} , ignore_index=True)
                cnt += 1
                idx += 1 

                # self.driver.execute_script("window.history.go(-1)")

                if idx == len(story_list):
                    self.logger.info("Click See More...")
                    self.driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
                    expand_button = self.driver.find_element_by_css_selector("#container > section > div > div.col_lg9 > section > div > a")
                    # 버튼을 찾을 때까지 대기
                    #WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#container > section > div > div.col_lg9 > section > div > a")))
                    #action = ActionChains(self.driver)
                    self.action.move_to_element(expand_button).perform()
                    # 더보기 버튼 클릭
                    expand_button.click()

        
        except Exception as e:
            print(e)
            self.logger.warning("=======Crawler Stoped!=======")
            if cnt==0:
                raise Exception("No article brought.")
            self.logger.warning(f"Last aticle date : {date}")
            return date, df
        


if __name__=="__main__":
    # logger
    logger = logging.getLogger("log")
    logger.setLevel(logging.INFO)
    file_handler= logging.FileHandler('./joongang/log/')

    formatter = logging.Formatter('%(asctime)s|%(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    crawler = JoongAngCrawler(logger,'2021.08.31 05:00')
    try:
        end_date, df = crawler.crawling() # 다음 수행 시 오류난  end_date의 전 기사부터 시작
    except Exception as e:
        print(e)

    save_dir = ('./joongang/data/joongang_accident_df.csv')

    origin_df = pd.read_csv(save_dir)
    origin_df = origin_df.iloc[:-1]
    expand_df = pd.concat([origin_df, df], ignore_index=True)
    expand_df.to_csv(save_dir, index=False)