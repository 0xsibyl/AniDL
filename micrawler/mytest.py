
from DrissionPage import Chromium

browser = Chromium()
# 打开页面
page = browser.latest_tab
page.get('https://hanime1.me/download?v=105262')

# 获取所有下载行
# 2. 等待表格加载完毕（最多等 15 秒）
# 等待所有行被加载到 DOM（至少一行出现），最多等待 15 秒
page.wait.eles_loaded('css:table.download-table tr', timeout=15)  # :contentReference[oaicite:1]{index=1}

table = page.ele('css:table.download-table')
rows = table.eles('tag:tr')[1:]

download_infos = []
for row in rows:
    cells = row.eles('tag:td')
    quality = cells[1].text.strip()                     # 畫質，如“全高清畫質 (1080p)”
    a_tag = cells[4].ele('tag:a')                       # 定位 <a> 元素
    url = a_tag.attr('data-url') if a_tag else None     # 自定义属性 data-url
    if url:
        download_infos.append({'quality': quality, 'url': url})

for info in download_infos:
    print(f"{info['quality']}: {info['url']}")
