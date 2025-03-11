import requests
from bs4 import BeautifulSoup

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# 定义要爬取的 Buff 饰品页面 URL
url = 'https://buff.163.com/market/csgo#tab=selling&page_num=1'

try:
    # 发送请求
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # 检查请求是否成功

    # 使用 BeautifulSoup 解析 HTML 内容
    soup = BeautifulSoup(response.text, 'html.parser')

    # 这里需要根据实际网页结构查找饰品信息，以下是示例
    # 假设饰品信息在特定的 class 中
    items = soup.find_all(class_='your-target-class')
    for item in items:
        print(item.text)

except requests.RequestException as e:
    print(f"请求出错: {e}")
except Exception as e:
    print(f"发生错误: {e}")