import logging
from urllib.parse import urlparse, parse_qs
import json
from DrissionPage import Chromium, ChromiumOptions
from prettytable import PrettyTable
from config_loader import load_config
from database_utils import DatabaseManager
from vide_data import Video
from video_downloader import download_video
from write_json_to_file import write_json_to_file


# 加载配置文件


def crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, genre, write_to_file):
    # 配置 ChromiumPage
    browser = Chromium()
    page = browser.latest_tab

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

                for i in data[1:]:
                    try:
                        img = i('t:img').attr('src') if genre == 'li' else \
                            i.ele('.card-mobile-panel inner').eles('t:img')[1].link
                        title = i.text if genre == 'li' else i.ele('.card-mobile-title').text
                        link = i.link if genre == 'li' else i.ele('t:a').link
                        page2 = browser.new_tab(link)
                        hanime1_div = page2.ele('#content-div').ele('#player-div-wrapper')
                        hanime1_div2 = hanime1_div.eles('.video-details-wrapper video-tags-wrapper')
                        author = page2.ele('#content-div').ele(
                            '.video-details-wrapper desktop-inline-mobile-block').ele('#video-artist-name')
                        # tags = []
                        result_strings = []
                        print("爬取--的番剧--详情--信息:")
                        print(f"  Image Source: {img}")
                        print(f"  Title: {title}")
                        print(f"  Link: {link}")
                        print()
                        for tag in hanime1_div2:
                            tags = tag.texts()
                            filtered_tags = [tag for tag in tags if tag not in ('add', 'remove')]
                            result_string = ', '.join(filtered_tags)
                            result_strings.append(result_string)

                        final_result = '\n'.join(result_strings)
                        parsed_url = urlparse(link)
                        query_params = parse_qs(parsed_url.query)
                        idx = query_params.get('v', [''])[0]
                        page3 = browser.new_tab(f'https://hanime1.me/download?v={idx}')
                        download_urls = page3.ele('tag:table').eles('tag:a')
                        video_data = {
                            res: next((k.link for k in download_urls if res in k.link), download_urls[0].link)
                            for res in ["1080p", "720p", "480p"]
                        }
                        # 打印第一个链接
                        first_link = download_urls[0].link if download_urls else None
                        print("第一个链接:", first_link)

                        if not video_data:
                            raise Exception("没有找到可用的高清分辨率下载链接")

                        best_quality_link = video_data.get("1080p") or video_data.get("720p") or video_data.get("480p")

                        if not download_urls:
                            raise Exception("没有找到合适的下载链接")
                        download_path = crawler_config['download_path'] + '/' + title + '.mp4'
                        video_data = Video(id=idx, title=title, video_url=link, thumbnail_url=img,
                                           description=author.text, tags=final_result, status=1,
                                           save_path=download_path, download_path=best_quality_link)
                        crawler_data_send(video_data)
                        fulul_title = f"{title} [v={idx}]"
                        table.add_row([fulul_title, link, img])

                        json_data = json.dumps(
                            {"番剧名称": fulul_title, "作者": author.text, "番剧URL": link, "图片地址": img,
                             "下载地址": best_quality_link}, ensure_ascii=False, indent=4)

                        if write_to_file:
                            write_json_to_file(json_data, crawler_config['json_file_path'])  ##开启JSON文件
                        if write_to_es:
                            es_data = {'title': fulul_title, 'url': link, 'image_url': img}
                            es.index(index='anime_data', body=es_data)
                            print(f'数据已写入 Elasticsearch: {es_data}')

                    except Exception as e:
                        print(f"获取数据时出错: {e}")
                        logging.error(f"第 {page_number} 页出错: {e}")
                    page2.close()
                    page3.close()

            else:
                print('找不到 .home-rows-videos-wrapper' if genre == 'li' else '.row.no-gutter，可能已经是最后一页了。')
                break
        else:
            print('找不到 #home-rows-wrapper，可能已经是最后一页了。')
            break

        page_number += 1
    page.close()
    print(table)


def li_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es, write_to_file):
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, 'li', write_to_file)


def motion_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type,
                    write_to_file):
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type, write_to_file)


def crawler_data_send(video_data):
    db_manager = DatabaseManager()
    config = load_config('micrawler/config.yaml')
    max_retries = config['crawler']['max_retries']

    try:
        if db_manager.check_video(video_data.id, video_data.status):
            logging.info(f"视频 {video_data.id} 已经下载，不进行重复下载。")
        elif db_manager.check_video_id(video_data.id):
            download_video(video_data.download_path, video_data.save_path, video_data.id, max_retries)
        else:
            db_manager.insert_video(video_data.id, video_data.title, video_data.video_url, video_data.thumbnail_url,
                                    video_data.description, video_data.tags, 0)
            download_video(video_data.download_path, video_data.save_path, video_data.id, max_retries)
    except Exception as e:
        logging.error(f"处理视频 {video_data.id} 时出错: {e}")
