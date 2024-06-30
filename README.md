# AniDL


![AniDL Version](https://img.shields.io/badge/AniDL-v1.0-blue)
![Dev Version](https://img.shields.io/badge/Dev%20Version-dev-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![GitHub stars](https://img.shields.io/github/stars/0xsibyl/AniDL?style=social)


[项目地址](https://github.com/0xsibyl/AniDL)

## 项目简介

AniDL是一个开源项目，开发者的初衷是经常去琉璃神社进行资源的获取,但是觉得很麻烦,为什么不能自动化下载这些里番视频,才开发了此项目。

## 功能特点

- **自动化抓取**：支持从多个网站自动化抓取里番动漫资源。
- **多种信息收集**：可以获取动漫的详细信息，包括标题、简介、标签、封面图片等。
- **数据存储**：支持将抓取的数据保存在数据库、ES中。
- **多线程支持**：通过多线程技术加速爬取过程，提高效率。
- **用户自定义**：用户可以根据需要自定义爬取的内容和保存格式。

## 安装步骤

### 环境要求

- Python 3.7及以上版本
- pip 包管理器

### 安装步骤

1. 克隆仓库到本地：

    ```bash
    git clone https://github.com/yourusername/yourrepo.git
    cd micrawler
    ```

2. 安装依赖：

    ```bash
    pip install DrissionPage
    pip install -r requirements.txt
    ```

## 使用方法

1. 运行主程序：

    ```bash
    python main.py
    ```

2. 配置文件：

    在 `config.json` 中，你可以设置需要爬取的网站列表、存储路径等参数（v2.0在开发）。

    ```json
    {
        "websites": [
            "https://example.com",
            "https://anotherexample.com"
        ],
        "output_format": "csv",
        "output_path": "./data"
    }
    ```

3. 运行示例：

    ```bash
    python main.py --config config.json
    ```

4. 查看结果：

    爬取的数据将保存在 `data` 文件夹中，可以使用任何文本编辑器或数据分析工具查看。

## 文件结构

```plaintext
AniDL/
│
├── README.md                 # 项目介绍文档      
├── main.py                   # 程序入口
├── /micrawler                # 源代码
│   └── /log                  # 日志
│   └── config.yaml           # 配置文件
│   └── config_loader.py      # 读取配置文件
│   └── crawler.py            # 爬虫主模块
│   └── database_utils.py     # 数据库模块
│   └── signal_handler.py	  # 中断模块
│   └── video_downloader.py   # 中断模块
└──             
```

## 贡献指南

欢迎对项目进行贡献！你可以通过以下方式参与：

1. **提交 Issue**：如果你发现了问题，欢迎通过 Issue 反馈。
2. **Fork 项目**：Fork 本项目，并在本地进行修改。
3. **提交 PR**：在完成修改后，提交 Pull Request 以供审核。

## 许可证

该项目遵循 [MIT 许可证](LICENSE)。
