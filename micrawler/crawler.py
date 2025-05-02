import logging
import json
import os
import sys  # 添加sys模块导入
from urllib.parse import urlparse, parse_qs
from DrissionPage import Chromium
from prettytable import PrettyTable
from colorama import init, Fore, Style
from micrawler.config_loader import load_config
from micrawler.database_utils import DatabaseManager
from micrawler.vide_data import Video
from micrawler.video_downloader import download_video
from micrawler.write_json_to_file import write_json_to_file

# 初始化colorama
init(autoreset=True)

# 将这些函数定义在类外部，作为模块级函数
def li_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es, write_to_file, use_json_db=False, json_db=None, json_db_path=None):
    """爬取里番的入口函数"""
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, 'li', write_to_file, use_json_db, json_db, json_db_path)


def motion_crawling(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type, write_to_file, use_json_db=False, json_db=None, json_db_path=None):
    """爬取动画的入口函数"""
    crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, crawler_type, write_to_file, use_json_db, json_db, json_db_path)


def crawl_page(base_url, start_page, database_config, crawler_config, write_to_es, es, genre, write_to_file, use_json_db=False, json_db=None, json_db_path=None):
    """爬取页面的统一入口函数"""
    crawler = AnimeCrawler(
        base_url, start_page, database_config, crawler_config, 
        write_to_es, es, genre, write_to_file, use_json_db, json_db, json_db_path
    )
    crawler.start_crawling()


class AnimeCrawler:
    # 在Crawler类的__init__方法中添加以下代码
    def __init__(self, base_url, start_page, db_config, crawler_config, write_to_es, es, genre, write_to_file, use_json_db=False, json_db=None, json_db_path=None):
        self.base_url = base_url
        self.start_page = start_page
        self.database_config = db_config
        self.crawler_config = crawler_config
        self.write_to_es = write_to_es
        self.es = es
        self.genre = genre
        self.write_to_file = write_to_file
        self.use_json_db = use_json_db
        self.json_db = json_db if json_db is not None else {}
        self.json_db_path = json_db_path
        self.browser = Chromium()
        self.page = self.browser.latest_tab
        self.table = PrettyTable()
        self.table.field_names = ["状态", "ID", "番剧名称", "作者", "下载地址"]
        self.table.align = "l"  # 左对齐
        self.table.max_width = 50  # 设置最大宽度
        self.db_manager = None if use_json_db else DatabaseManager()
        self.config = load_config('micrawler/config.yaml')
        self.success_count = 0
        self.fail_count = 0
        
    def start_crawling(self):
        """开始爬取过程"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}开始爬取 - 类型: {self.genre}, 起始页: {self.start_page}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # 在开始爬取前获取下载目录
        self.download_dir = self._get_download_directory()
        
        page_number = self.start_page
        while True:
            url = f'{self.base_url}&page={page_number}'
            print(f'{Fore.YELLOW}正在访问: {url}{Style.RESET_ALL}')
            
            self.page.get(url)
            if not self._process_page(page_number):
                break
                
            page_number += 1
        
        self.page.close()
        
        # 打印爬取结果统计
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}爬取完成 - 总计: {self.success_count + self.fail_count}, 成功: {self.success_count}, 失败: {self.fail_count}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # 打印表格
        print(self.table)
    
    def _process_page(self, page_number):
        """处理单个页面的内容"""
        div1 = self.page.ele('#home-rows-wrapper')
        if not div1:
            print(f'{Fore.RED}找不到 #home-rows-wrapper，可能已经是最后一页了。{Style.RESET_ALL}')
            return False
            
        div2 = div1.ele('.home-rows-videos-wrapper' if self.genre == 'li' else '.row no-gutter')
        if not div2:
            print(f'{Fore.RED}找不到 .home-rows-videos-wrapper' if self.genre == 'li' else '.row.no-gutter，可能已经是最后一页了。{Style.RESET_ALL}')
            return False
            
        data = self._get_anime_elements(div1, div2)
        if not data:
            print(f'{Fore.RED}第 {page_number} 页没有数据，可能已经是最后一页了。{Style.RESET_ALL}')
            return False
            
        print(f"{Fore.CYAN}第 {page_number} 页找到 {len(data)-1} 个视频{Style.RESET_ALL}")
        
        for item in data[1:]:
            try:
                self._process_anime_item(item)
            except Exception as e:
                print(f"{Fore.RED}获取数据时出错: {e}{Style.RESET_ALL}")
                logging.error(f"第 {page_number} 页出错: {e}")
                self.fail_count += 1
                
        return True
    
    def _get_anime_elements(self, div1, div2):
        """获取动画元素列表"""
        if self.genre == 'li':
            return div2.eles('tag:a')
        else:
            return div1.ele('.row no-gutter').eles('.col-xs-6 col-sm-4 col-md-2 search-doujin-videos hidden-xs hover-lighter multiple-link-wrapper')
    
    def _process_anime_item(self, item):
        """处理单个动画项目"""
        # 获取基本信息
        img, title, link = self._get_basic_info(item)
        
        # 打开详情页
        page2 = self.browser.new_tab(link)
        try:
            # 获取详细信息
            author, final_result = self._get_detailed_info(page2)
            
            # 获取视频ID
            parsed_url = urlparse(link)
            query_params = parse_qs(parsed_url.query)
            idx = query_params.get('v', [''])[0]
            
            # 获取下载链接
            best_quality_link = self._get_download_link(idx)
            
            # 处理视频数据
            download_path = f"{self.crawler_config['download_path']}/{title}.mp4"
            video_data = Video(
                id=idx, 
                title=title, 
                video_url=link, 
                thumbnail_url=img,
                description=author.text, 
                tags=final_result, 
                status=1,
                save_path=download_path, 
                download_path=best_quality_link
            )
            
            # 发送数据
            self._send_data(video_data, idx, title, link, img, author.text, best_quality_link)
            
        finally:
            page2.close()
    
    def _get_basic_info(self, item):
        """获取基本信息（图片、标题、链接）"""
        if self.genre == 'li':
            img = item('t:img').attr('src')
            title = item.text
            link = item.link
        else:
            img = item.ele('.card-mobile-panel inner').eles('t:img')[1].link
            title = item.ele('.card-mobile-title').text
            link = item.ele('t:a').link
            
        print("爬取番剧详情信息:")
        print(f"  Image Source: {img}")
        print(f"  Title: {title}")
        print(f"  Link: {link}")
        print()
        
        return img, title, link
    
    def _get_detailed_info(self, page):
        """获取详细信息（作者、标签）"""
        hanime1_div = page.ele('#content-div').ele('#player-div-wrapper')
        hanime1_div2 = hanime1_div.eles('.video-details-wrapper video-tags-wrapper')
        
        author = page.ele('#content-div').ele(
            '.video-details-wrapper desktop-inline-mobile-block').ele('#video-artist-name')
        
        result_strings = []
        try:
            for tag in hanime1_div2:
                tags = tag.texts()
                filtered_tags = [tag for tag in tags if tag not in ('add', 'remove')]
                result_string = ', '.join(filtered_tags)
                result_strings.append(result_string)
        except Exception as e:
            print(e)
            
        final_result = '\n'.join(result_strings)
        return author, final_result
    
    def _get_download_link(self, idx):
        """获取下载链接"""
        page3 = self.browser.new_tab(f'https://hanime1.me/download?v={idx}')
        try:
            page3.wait.eles_loaded('css:table.download-table tr', timeout=15)
            table = page3.ele('css:table.download-table')
            rows = table.eles('tag:tr')[1:]
            
            # 遍历所有下载链接
            download_infos = []
            for row in rows:
                cells = row.eles('tag:td')
                quality = cells[1].text.strip()  # 畫質，如"全高清畫質 (1080p)"
                a_tag = cells[4].ele('tag:a')  # 定位 <a> 元素
                url = a_tag.attr('data-url') if a_tag else None  # 自定义属性 data-url
                if url:
                    download_infos.append({'quality': quality, 'url': url})
                    
            # 打印所有可用的下载链接
            print(f"{Fore.CYAN}可用的下载链接:{Style.RESET_ALL}")
            for info in download_infos:
                print(f"{Fore.WHITE}{info['quality']}: {Fore.YELLOW}{info['url']}{Style.RESET_ALL}")
                
            if not download_infos:
                raise Exception("没有找到可用的高清分辨率下载链接")
                
            # 选择最高优先级的画质
            quality_priority = ['1080p', '720p', '480p']
            best_quality_link = next(
                (info['url'] for q in quality_priority for info in download_infos if q in info['quality']),
                download_infos[0]['url'] if download_infos else None
            )
            
            # 获取最高清晰度的名称
            best_quality_name = next(
                (info['quality'] for q in quality_priority for info in download_infos if q in info['quality']),
                download_infos[0]['quality'] if download_infos else "未知清晰度"
            )
            
            if not best_quality_link:
                raise Exception("没有找到合适的下载链接")
            
            # 打印选择的最高清晰度链接
            print(f"\n{Fore.GREEN}已选择最高清晰度: {best_quality_name}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}下载链接: {best_quality_link}{Style.RESET_ALL}")
                
            return best_quality_link
        finally:
            page3.close()
    
    def _send_data(self, video_data, idx, title, link, img, author_text, best_quality_link):
        """发送数据到数据库、ES和文件"""
        # 处理视频数据
        download_success = self._process_video_data(video_data)
        
        # 添加到表格，根据下载状态设置颜色
        status = f"{Fore.GREEN}成功{Style.RESET_ALL}" if download_success else f"{Fore.RED}失败{Style.RESET_ALL}"
        
        # 截断过长的标题和作者
        title_display = (title[:47] + '...') if len(title) > 50 else title
        author_display = (author_text[:47] + '...') if len(author_text) > 50 else author_text
        
        self.table.add_row([
            status, 
            idx, 
            title_display, 
            author_display, 
            best_quality_link[:50] + '...' if len(best_quality_link) > 50 else best_quality_link
        ])
        
        # 更新计数
        if download_success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        # 创建JSON数据
        json_data = json.dumps(
            {"番剧名称": title, "ID": idx, "作者": author_text, "番剧URL": link, "图片地址": img,
             "下载地址": best_quality_link, "下载状态": "成功" if download_success else "失败"}, 
            ensure_ascii=False, indent=4)
        
        # 写入文件
        if self.write_to_file:
            write_json_to_file(json_data, self.crawler_config['json_file_path'])
            
        # 写入ES
        if self.write_to_es and self.es:
            es_data = {'title': title, 'id': idx, 'url': link, 'image_url': img, 'status': download_success}
            self.es.index(index='anime_data', body=es_data)
            print(f'{Fore.BLUE}数据已写入 Elasticsearch{Style.RESET_ALL}')
    
    def _process_video_data(self, video_data):
        """处理视频数据（检查、插入、下载）"""
        max_retries = self.config['crawler']['max_retries']
        download_success = False
        
        # 使用已经选择的下载目录
        video_data.save_path = os.path.join(self.download_dir, os.path.basename(video_data.save_path))
        
        try:
            if self.use_json_db:
                # 使用JSON数据库
                video_id_str = str(video_data.id)
                if video_id_str in self.json_db and self.json_db[video_id_str].get('status') == 1:
                    print(f"{Fore.YELLOW}视频 {video_data.id} 已经在JSON数据库中标记为已下载，跳过下载。{Style.RESET_ALL}")
                    download_success = True
                else:
                    # 下载视频
                    print(f"{Fore.CYAN}开始下载视频 {video_data.id} - {video_data.title}{Style.RESET_ALL}")
                    download_success = download_video(video_data.download_path, video_data.save_path, video_data.id, max_retries, self.use_json_db)
                    
                    # 更新JSON数据库
                    self.json_db[video_id_str] = {
                        'id': video_data.id,
                        'title': video_data.title,
                        'video_url': video_data.video_url,
                        'thumbnail_url': video_data.thumbnail_url,
                        'description': video_data.description,
                        'tags': video_data.tags,
                        'status': 1 if download_success else 0,
                        'save_path': video_data.save_path,
                        'download_path': video_data.download_path
                    }
                    
                    # 保存JSON数据库
                    self._save_json_db()
            else:
                # 使用MySQL数据库
                if self.db_manager.check_video(video_data.id, video_data.status):
                    print(f"{Fore.YELLOW}视频 {video_data.id} 已经下载，不进行重复下载。{Style.RESET_ALL}")
                    download_success = True
                elif self.db_manager.check_video_id(video_data.id):
                    print(f"{Fore.CYAN}开始下载视频 {video_data.id} - {video_data.title}{Style.RESET_ALL}")
                    download_success = download_video(video_data.download_path, video_data.save_path, video_data.id, max_retries)
                else:
                    self.db_manager.insert_video(
                        video_data.id, video_data.title, video_data.video_url, video_data.thumbnail_url,
                        video_data.description, video_data.tags, 0
                    )
                    print(f"{Fore.CYAN}开始下载视频 {video_data.id} - {video_data.title}{Style.RESET_ALL}")
                    download_success = download_video(video_data.download_path, video_data.save_path, video_data.id, max_retries)
        except Exception as e:
            logging.error(f"处理视频 {video_data.id} 时出错: {e}")
            print(f"{Fore.RED}处理视频 {video_data.id} 时出错: {e}{Style.RESET_ALL}")
            download_success = False
            
        return download_success
    
    def _save_json_db(self):
        """保存JSON数据库"""
        if not self.use_json_db or not self.json_db_path:
            return
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.json_db_path), exist_ok=True)
            
            with open(self.json_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.json_db, f, ensure_ascii=False, indent=4)
            logging.info(f"JSON数据库已保存，共 {len(self.json_db)} 条记录")
        except Exception as e:
            logging.error(f"保存JSON数据库时出错: {e}")

    def _get_download_directory(self):
        """获取下载目录，根据配置决定默认使用哪个路径"""
        config_path = self.crawler_config['download_path']
        exe_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)), 'downloads')
        
        # 根据配置决定默认使用哪个路径
        use_config_path = self.crawler_config.get('use_config_path', False)
        
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}下载位置:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1. 程序运行目录: {exe_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}2. 配置文件中的路径: {config_path}{Style.RESET_ALL}")
        
        # 根据配置设置默认选项
        default_choice = '2' if use_config_path else '1'
        choice = input(f"{Fore.GREEN}请输入选择 (1/2，默认为{default_choice}): {Style.RESET_ALL}").strip()
        
        if not choice:
            choice = default_choice
        
        if choice == '2':
            # 确保配置文件中的下载目录存在
            os.makedirs(config_path, exist_ok=True)
            print(f"{Fore.GREEN}已选择保存到配置文件路径: {config_path}{Style.RESET_ALL}")
            return config_path
        else:
            # 确保下载目录存在
            os.makedirs(exe_path, exist_ok=True)
            print(f"{Fore.GREEN}已选择保存到程序运行目录: {exe_path}{Style.RESET_ALL}")
            return exe_path


# 外部接口函数
def crawler_data_send(video_data):
    """处理视频数据的函数（为了保持兼容性）"""
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


def _get_application_path(self):
    """获取应用程序路径，兼容打包后的EXE文件"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的EXE文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
