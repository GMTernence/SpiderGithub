from bs4 import BeautifulSoup
import requests
import time

base_headers = {
    'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/71.0.3578.98 Safari/537.36 ',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',

}


def get_soup(url):
    try:
        response = requests.get(url=url, headers=base_headers, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            return soup
        else:
            time.sleep(60)
            get_soup(url)
    except requests.exceptions:
        print('web error')
        return None
