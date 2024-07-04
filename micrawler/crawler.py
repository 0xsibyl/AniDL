from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from urllib.parse import urlparse, parse_qs
import json

from colorama import Fore, Style
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
                data = div2.eles('tag:a') if genre == 'li' else page.ele('#home-rows-wrapper').ele(
                    '.row no-gutter').eles('.col-xs-6 col-sm-4 col-md-2 '
                                           'search-doujin-videos hidden-xs '
                                           'hover-lighter multiple-link-wrapper')
                if not data:
                    print(f'第 {page_number} 页没有数据，可能已经是最后一页了。')
                    break

                for i in data:
                    try:
                        img = i('t:img').attr('src') if genre == 'li' else \
                            i.ele('.card-mobile-panel inner').eles('t:img')[1].link
                        title = i.text if genre == 'li' else i.ele('.card-mobile-title').text
                        link = i.href if genre == 'li' else i.ele('t:a').link
                        page2.get(link)
                        hanime1_div = page2.ele('#content-div').ele('#player-div-wrapper')
                        hanime1_div2 = hanime1_div.eles('.video-details-wrapper video-tags-wrapper')
                        author = page2.ele('#content-div').ele(
                            '.video-details-wrapper desktop-inline-mobile-block').ele('#video-artist-name')
                        print(Fore.RED + f'作者: {author.text}')
                        for tag in hanime1_div2:
                            print(f'番剧标签: {tag.texts()}')

                        parsed_url = urlparse(link)
                        query_params = parse_qs(parsed_url.query)
                        v_value = query_params.get('v', [''])[0]
                        page3.get(f'https://hanime1.me/download?v={v_value}')
                        download_urls = page3.ele('tag:table').eles('tag:a')

                        if not download_urls:
                            raise Exception("没有找到合适的下载链接")

                        video_data = {
                            res: k.link for k in download_urls for res in ["1080p", "720p", "480p"]
                            if res in k.link
                        }

                        if not video_data:
                            raise Exception("没有找到可用的高清分辨率下载链接")

                        best_quality_link = video_data.get("1080p") or video_data.get("720p") or video_data.get("480p")
                        print(f'番剧标签: {best_quality_link}')
                        if best_quality_link:
                            connection = connect_to_db(database_config)
                            cursor = connection.cursor()
                            save_path = f"{crawler_config['download_path']}/{v_value}.mp4"
                            download_video(best_quality_link, save_path, v_value, crawler_config['max_retries'], cursor, connection)
                            cursor.close()
                            connection.close()
                        else:
                            connection = connect_to_db(database_config)
                            cursor = connection.cursor()
                            log_error_to_db(cursor, v_value, link, "没有找到合适的下载链接")
                            connection.commit()
                            cursor.close()
                            connection.close()

                        full_title = f"{title} [v={v_value}]"
                        table.add_row([full_title, link, img])
                        print(Fore.CYAN + Style.BRIGHT + f'番剧名称: {full_title}')
                        print(f'番剧URL: {link}')
                        print(f'图片地址: {img}')
                        print('-' * 50)

                        json_data = json.dumps(
                            {"番剧名称": full_title, "作者": author.text, "番剧URL": link, "图片地址": img,
                             "下载地址": best_quality_link}, ensure_ascii=False, indent=4)
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
