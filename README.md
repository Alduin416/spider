# 百度热搜爬虫与 Web 展示平台

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey.svg)](https://flask.palletsprojects.com/)

## 📖 项目简介

这是一个功能完整的百度热搜爬虫与 Web 展示平台，包含两种运行模式：

1. **爬虫模式**：命令行直接抓取热搜数据，进行关键词分析和统计
2. **Web 模式**：启动本地 Web 服务器，提供美观的日式侘寂风格热搜展示界面

## ✨ 功能特性

### 爬虫功能
- ✅ 抓取百度热搜榜实时数据
- ✅ 高频关键词提取（基于 jieba 分词）
- ✅ 专用名词识别（人名、地名、机构名等）
- ✅ 遵守 robots.txt 协议
- ✅ 详细的热点来源追踪

### Web 展示
- 🎨 精美的日式侘寂风格 UI
- 🔐 验证码保护机制
- 📊 实时热搜数据展示
- 🔥 高频关键词可视化
- 🎵 背景音乐支持
- 📱 响应式设计

## 🚀 快速开始

### 环境要求

- Python 3.7+
- Windows / macOS / Linux

### 安装步骤

1. 克隆本仓库：
```bash
git clone https://github.com/Alduin416/baidu-hot-search.git
cd baidu-hot-search
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 运行方式

#### 方式一：交互模式（默认）
```bash
python main.py
```
启动后会显示菜单，可选择爬虫模式或 Web 模式。

#### 方式二：直接启动爬虫模式
```bash
python main.py --scraper
```
直接在命令行显示热搜数据和关键词分析。

#### 方式三：直接启动 Web 模式
```bash
python main.py --web
```
启动 Web 服务器，访问 http://127.0.0.1:5000

## 📁 项目结构

```
baidu-hot-search/
├── main.py                 # 主程序入口（整合版）
├── requirements.txt        # Python 依赖
├── README.md              # 项目说明文档
├── LICENSE                # 开源许可证
├── .gitignore             # Git 忽略文件
│
├── templates/             # HTML 模板
│   ├── page1.html        # 主页（完整功能）
│   └── page_blank.html   # 空白页模板
│
└── static/                # 静态资源（需自行添加）
    ├── images/           # 背景图片
    │   └── great_wave.jpg
    └── Haggstrom-C418.mp3  # 背景音乐（可选）
```

## 🎯 使用示例

### 爬虫模式输出示例

```
### 百度热点信息收集器 ###

成功收集到 10 条热点信息：

1. 某某事件最新进展
   热度：热
   链接：https://www.baidu.com/s?wd=某某事件

...

### 高频关键词分析 ###

🔥 百度热搜高频词 TOP10:

1. 【事件】出现 3 次
   - 第1名：某某事件最新进展
   - 第5名：另一事件追踪
   ...

### 高频专用名词分析 ###

📌 百度热搜专用名词 TOP20:

1. 👤【张三】(人名) - 出现 2 次
   - 第2名：张三的最新动态
   ...
```

### Web 模式

启动后在浏览器访问 `http://127.0.0.1:5000`，通过验证码后即可浏览热搜。

## 🔧 技术栈

- **后端**：Python 3, Flask
- **爬虫**：Requests
- **分词**：Jieba
- **前端**：HTML5, CSS3, JavaScript
- **UI 风格**：日式侘寂美学

## 📝 API 说明

### 百度热搜 API

本项目使用百度热榜官方 API：
```
https://top.baidu.com/api/board?platform=wise&tab=realtime&rn=50
```

### 项目内部 API

- `GET /api/news` - 获取热搜数据（需验证）
- `GET /api/keywords` - 获取高频关键词（需验证）
- `GET /api/captcha/generate` - 生成验证码
- `POST /api/captcha/verify` - 验证验证码

## ⚠️ 注意事项

1. 本项目仅供学习交流使用
2. 遵守 robots.txt 协议
3. 请勿用于商业用途或频繁请求，避免触发反爬机制
4. 背景图片和音乐需自行准备，放入 `static/` 目录

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 百度热搜数据源
- Flask Web 框架
- Jieba 中文分词库
- 富岳三十六景 - 葛饰北斋

---

**声明**：本项目仅供学习交流使用。
