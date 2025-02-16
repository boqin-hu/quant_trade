import requests
from lxml import etree
url = "https://jywg.18.cn/"
headers = {   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'jywg.18.cn',
            'Origin': 'https://jywg.18.cn',
            'Referer': 'https://jywg.18.cn/Login/Login',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
response = requests.get(url=url, headers=headers)
if(response.status_code != 200):
    print("status error")
else:
    html = response.text
    # print(html)
    # with open('./dfcf.html', 'w', encoding='utf-8') as fp:
    #     fp.write(html)
    tree = etree.html(html)
    yzm_code = tree.xpath('//*[@id="imgValidCode"]/')
