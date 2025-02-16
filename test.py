import requests
from lxml import etree
import ddddocr
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
session = requests.Session()
response = session.get(url=url, headers=headers)
if(response.status_code != 200):
    print("status error")
else:
    html = response.text
    # print(html)
    with open('./dfcf.html', 'w', encoding='utf-8') as fp:
        fp.write(html)
    tree = etree.HTML(html)
    # 获取验证码图片URL（添加异常处理）
    try:
        yzm_code = tree.xpath('//*[@id="imgValidCode"]/@src')[0]
        yzm_url = f"https://jywg.18.cn{yzm_code}"
        print("验证码URL:", yzm_url)
        
        # 下载验证码图片（添加超时和重试）
        yzm_response = session.get(yzm_url, timeout=10)
        yzm_response.raise_for_status()
    with open('verify_code.jpg', 'wb') as f:
        f.write(yzm_response.content)
        
    # 使用ddddocr识别验证码
    ocr = ddddocr.DdddOcr()
    with open('verify_code.jpg', 'rb') as f:
        img_bytes = f.read()
    yzm_text = ocr.classification(img_bytes)
    
    # 登录参数
    login_data = {
        'userName': 'your_username',
        'password': 'your_password',
        'validCode': yzm_text
    }
    
    # 提交登录请求
    login_url = 'https://jywg.18.cn/Login/Login'
    login_response = session.post(login_url, data=login_data)
    
    # 检查登录结果
    if login_response.status_code == 200:
        print("登录成功")
        print(login_response.json())
    else:
        print("登录失败")
