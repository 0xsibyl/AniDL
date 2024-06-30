from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from urllib.parse import urlparse, parse_qs
import json

from colorama import Fore
from prettytable import PrettyTable
from database_utils import log_error_to_db, connect_to_db
from video_downloader import download_video


def crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, genre):
    # 配置 ChromiumPage
    co = ChromiumOptions().auto_port()
    page = ChromiumPage(co)
    page.set.load_mode.eager()
    page2 = ChromiumPage(co)
    page2.set.load_mode.eager()
    page3 = ChromiumPage(co)
    page3.set.load_mode.eager()
    table = PrettyTable(["番剧名称", "番剧URL", "图片地址"])

    page_number = start_page
    while True:
        url = f'{base_url}&page={page_number}'
        print(f'正在访问: {url}')

        page.get(url)
        div1 = page.ele('#home-rows-wrapper')
        if div1:
            div2 = div1.ele('.home-rows-videos-wrapper' if genre == 'li' else '.row no-gutter')
            if div2:
                data = div2.eles('tag:a') if genre == 'li' else page.ele('#home-rows-wrapper').ele('.row no-gutter').eles('.col-xs-6 col-sm-4 col-md-2 '
                                                                                 'search-doujin-videos hidden-xs '
                                                                                 'hover-lighter multiple-link-wrapper')
                if not data:
                    print(f'第 {page_number} 页没有数据，可能已经是最后一页了。')
                    break

                for i in data:
                    try:
                        img = i('t:img').attr('src') if genre == 'li' else \
                        i.ele('.card-mobile-panel inner').eles('t:img')[1].link
                        title = i.text if genre == 'li' else i.ele('.card-mobile-title').texts()
                        link = i.href if genre == 'li' else i.ele('t:a').link
                        page2.get(link)
                        hanime1_div = page2.ele('#content-div').ele('#player-div-wrapper')
                        hanime1_div2 = hanime1_div.eles('.video-details-wrapper video-tags-wrapper')
                        author = page2.ele('#content-div').ele(
                            '.video-details-wrapper desktop-inline-mobile-block').ele('#video-artist-name')
                        print(f'作者: {author.text}')

                        for tag in hanime1_div2:
                            print(f'番剧标签: {tag.texts()}')

                        parsed_url = urlparse(link)
                        query_params = parse_qs(parsed_url.query)
                        v_value = query_params.get('v', [''])[0]
                        page3.get('https://hanime1.me/download?v=' + v_value)
                        download_url = page3.ele('tag:table').eles('tag:a')
                        vide_data = {}

                        for k in download_url:
                            if "1080p" in k.link:
                                vide_data['1080P'] = k.link
                                print(f'视频下载信息: {vide_data}')
                                connection = connect_to_db(database_config)
                                cursor = connection.cursor()
                                download_video(k, title, v_value, crawler_config, connection, cursor)
                                break

                        if not vide_data:
                            connection = connect_to_db(database_config)
                            cursor = connection.cursor()
                            log_error_to_db(cursor, v_value, link, "没有找到合适的下载链接")
                            connection.commit()
                            cursor.close()
                            connection.close()

                        full_title = f"{title} [v={v_value}]"
                        table.add_row([full_title, link, img])

                        print(f'番剧名称: {full_title}')
                        print(f'番剧URL: {link}')
                        print(f'图片地址: {img}')
                        print('-' * 50)

                        json_data = json.dumps(
                            {"番剧名称": full_title, "作者": author.text, "番剧URL": link, "图片地址": img,
                             "下载地址": vide_data}, ensure_ascii=False, indent=5)
                        print(json_data)

                        if write_to_es:
                            es_data = {'title': full_title, 'url': link, 'image_url': img}
                            es.index(index='anime_data', body=es_data)
                            print(f'数据已写入 Elasticsearch: {es_data}')

                    except Exception as e:
                        print(f"获取数据时出错: {e}")
                        connection = connect_to_db(database_config)
                        cursor = connection.cursor()
                        log_error_to_db(cursor, v_value, link, str(e))
                        connection.commit()
                        cursor.close()
                        connection.close()
            else:
                print('找不到 .home-rows-videos-wrapper' if genre == 'li' else '.row.no-gutter，可能已经是最后一页了。')
                break
        else:
            print('找不到 #home-rows-wrapper，可能已经是最后一页了。')
            break

        page_number += 1

    print(table)
    page.quit()
    page2.quit()
    page3.quit()


def li_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es):
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, 'li')


def motion_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type):
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type)
