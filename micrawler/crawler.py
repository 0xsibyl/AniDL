from DrissionPage import ChromiumPage
from DrissionPage._configs.chromium_options import ChromiumOptions
from urllib.parse import urlparse, parse_qs
import json

from colorama import Fore, Style
from prettytable import PrettyTable
from database_utils import DatabaseManager
from vide_data import Video
from video_downloader import download_video
from write_json_to_file import write_json_to_file


def crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, genre, write_to_file):
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
                        # tags = []
                        result_strings = []

                        for tag in hanime1_div2:
                            tags = tag.texts()
                            filtered_tags = [tag for tag in tags if tag not in ('add', 'remove')]
                            result_string = ', '.join(filtered_tags)
                            result_strings.append(result_string)

                        final_result = '\n'.join(result_strings)
                        print(final_result)
                        # print(f'番剧标签: {tag.texts()}')
                        # 这里获取vide——id
                        parsed_url = urlparse(link)
                        query_params = parse_qs(parsed_url.query)
                        idx = query_params.get('v', [''])[0]
                        page3.get(f'https://hanime1.me/download?v={idx}')
                        download_urls = page3.ele('tag:table').eles('tag:a')
                        video_data = {
                            res: k.link for k in download_urls for res in ["1080p", "720p", "480p"]
                            if res in k.link
                        }

                        if not video_data:
                            raise Exception("没有找到可用的高清分辨率下载链接")

                        best_quality_link = video_data.get("1080p") or video_data.get("720p") or video_data.get("480p")

                        if not download_urls:
                            raise Exception("没有找到合适的下载链接")

                        # if best_quality_link:
                        #     connection = connect_to_db(database_config)
                        #     cursor = connection.cursor()
                        #     save_path = f"{crawler_config['download_path']}/{title}.mp4"
                        #     download_video(best_quality_link, save_path, idx, crawler_config['max_retries'],
                        #                    cursor,
                        #                    connection)  ##这个要写上标签名字
                        #     cursor.close()
                        #     connection.close()
                        # else:
                        #     connection = connect_to_db(database_config)
                        #     cursor = connection.cursor()
                        #     update_video_status(cursor, idx, 2)
                        #     connection.commit()
                        #     cursor.close()
                        #     connection.close()
                        video_data = Video(id=idx, title=title, video_url=link, thumbnail_url=img,
                                           description=author.text, tags=final_result, status=1)
                        crawler_data_send(video_data)
                        fulul_title = f"{title} [v={idx}]"
                        table.add_row([fulul_title, link, img])
                        # print(Fore.CYAN + Style.BRIGHT + f'番剧名称: {fulul_title}')
                        # print(f'番剧标签: {best_quality_link}')
                        # print(f'番剧URL: {link}')
                        # print(f'图片地址: {img}')
                        # print('-' * 50)
                        # 我在在这里进行判断是否没有进行下载
                        # if check_vide_id(cursor, idx, 1):
                        #     print(f"番剧 {fulul_title} 已经存在数据库中，跳过下载")
                        #     continue

                        json_data = json.dumps(
                            {"番剧名称": fulul_title, "作者": author.text, "番剧URL": link, "图片地址": img,
                             "下载地址": best_quality_link}, ensure_ascii=False, indent=4)

                        if write_to_file:
                            write_json_to_file(json_data)  ##开启JSON文件
                        if write_to_es:
                            es_data = {'title': fulul_title, 'url': link, 'image_url': img}
                            es.index(index='anime_data', body=es_data)
                            print(f'数据已写入 Elasticsearch: {es_data}')

                    except Exception as e:
                        print(f"获取数据时出错: {e}")

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


def li_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es, write_to_file):
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, 'li', write_to_file)


def motion_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type,
                    write_to_file):
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type, write_to_file)


def crawler_data_send(video_data):
    db_manager = DatabaseManager()
    if db_manager.check_video(video_data.id, video_data.status):
        print("此视频已经记录不在进行爬取")
    else:
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print(video_data.title)
        print("---------------------------")
        print(video_data.video_url)
        print("---------------------------")
        print(video_data.thumbnail_url)
        print("---------------------------")
        print(video_data.tags)
        print("---------------------------")
        print(video_data.description)
        print("****************************")
        # db_manager.insert_video(video_data.id, video_data.title, video_data.video_url, video_data.thumbnail_url,
        #                         video_data.description, video_data.tags, video_data.status)
