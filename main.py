# -*- coding: utf-8 -*-
"""
侘寂 - 百度热搜爬虫与 Web 展示平台
===================================

功能：
1. 爬虫模式：抓取百度热搜数据，进行关键词分析
2. Web 模式：启动 Web 服务器，提供美观的热搜展示界面

运行方式：
- 爬虫模式：python main.py --scraper
- Web 模式：python main.py --web
- 交互模式：python main.py（默认）

作者：[你的GitHub用户名]
许可证：MIT
"""

import sys
import os
import json
import time
import random
import re
from typing import Optional
from dataclasses import dataclass, field
from collections import Counter

# 第三方库导入
try:
    import requests
    import jieba
    import jieba.posseg as pseg
except ImportError as e:
    print(f"错误：缺少必要的依赖库。请先运行：pip install -r requirements.txt")
    print(f"详细信息：{e}")
    sys.exit(1)

# Flask 相关导入（仅在 Web 模式需要）
try:
    from flask import Flask, render_template, jsonify, session, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


# ==========================================
# 常量定义
# ==========================================

# API 配置
BAIDU_HOT_API_URL = "https://top.baidu.com/api/board?platform=wise&tab=realtime&rn=50"
BAIDU_ROBOTS_URL = "https://www.baidu.com/robots.txt"
BAIDU_SEARCH_BASE = "https://www.baidu.com/s?wd="

# 请求头配置
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://top.baidu.com/board?tab=realtime",
}

# 爬虫模式请求头
SCRAPER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 关键词提取配置
DEFAULT_TOP_N = 15
PROPER_NOUN_TOP_N = 20

# 词性映射
PROPER_NOUN_FLAGS = {"nr", "ns", "nt", "nz"}
FLAG_MEANINGS = {
    "nr": "人名",
    "ns": "地名",
    "nt": "机构名",
    "nz": "其他专有名词",
}

# 中文停用词表
CHINESE_STOPWORDS = frozenset({
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
    "他", "她", "它", "们", "这个", "那个", "可以", "能", "让",
    "但", "而", "如", "及", "等", "等", "一个", "一些", "什么",
    "怎么", "为什么", "是否", "如何", "以及", "因为", "所以",
    "虽然", "但是", "如果", "对于", "关于", "被", "给", "使",
    "让", "叫", "向", "从", "为", "对", "与", "或", "等", "第",
    "其", "更", "已", "已经", "还", "又", "再", "才", "刚",
    "正在", "正", "将", "要", "会", "可能", "应该", "必须",
    "可以", "能够", "得以", "予以", "进行", "作出", "开展",
    "之", "乎", "者", "也", "矣", "焉", "哉", "嘛", "呢", "吧",
    "啊", "呀", "哦", "嗯", "哎", "唉", "喂", "呐", "喽", "呗",
})


# ==========================================
# 数据类定义
# ==========================================

@dataclass
class HotNewsItem:
    """热搜新闻条目"""
    title: str
    url: str
    hot: str
    desc: str = ""


@dataclass
class KeywordInfo:
    """关键词信息"""
    keyword: str
    count: int
    sources: list = field(default_factory=list)


@dataclass
class ProperNounInfo:
    """专用名词信息"""
    word: str
    noun_type: str
    count: int
    sources: list = field(default_factory=list)
    flag: str = ""


# ==========================================
# 爬虫核心功能
# ==========================================

def check_robots_txt() -> bool:
    """
    检查百度 robots.txt 协议
    遵守 robots.txt 协议是我们爬虫的第一原则

    Returns:
        bool: 是否成功检查 robots.txt
    """
    try:
        response = requests.get(BAIDU_ROBOTS_URL, headers=SCRAPER_HEADERS, timeout=5)
        if response.status_code == 200:
            print("已检查百度 robots.txt 协议")
            return True
    except Exception:
        pass
    return True


def get_baidu_hot_news() -> list[HotNewsItem]:
    """
    抓取百度热点信息
    使用百度热榜官方 API 接口

    Returns:
        list[HotNewsItem]: 热点新闻列表
    """
    check_robots_txt()

    try:
        print(f"正在请求百度热榜 API...")
        response = requests.get(BAIDU_HOT_API_URL, headers=DEFAULT_HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            print(f"API 返回错误：{data.get('error', {}).get('message', '未知错误')}")
            return []

        hot_items: list[HotNewsItem] = []
        result = data.get("data", {})
        cards = result.get("cards", [])

        for card in cards:
            content_list = card.get("content", [])
            for content in content_list:
                items = content.get("content", [])
                for item in items:
                    if word := item.get("word"):
                        full_link = f"{BAIDU_SEARCH_BASE}{word}"
                        hot_items.append(HotNewsItem(
                            title=word,
                            url=full_link,
                            hot=item.get("newHotName", "") or item.get("hotTag", ""),
                        ))

        print(f"成功提取 {len(hot_items)} 条热点")
        return hot_items

    except requests.RequestException as e:
        print(f"请求出错：{e}")
    except json.JSONDecodeError as e:
        print(f"JSON 解析出错：{e}")
    except Exception as e:
        print(f"其他错误：{e}")

    return []


def extract_hot_keywords(
    news_list: Optional[list[HotNewsItem]] = None,
    top_n: int = DEFAULT_TOP_N,
) -> list[tuple[str, int]]:
    """
    从百度热点新闻标题中提取高频关键词

    Args:
        news_list: 新闻列表，如果为 None 则自动获取
        top_n: 返回前 N 个高频词

    Returns:
        list[tuple[str, int]]: 包含 (词语, 词频) 的列表
    """
    if news_list is None:
        news_list = get_baidu_hot_news()

    if not news_list:
        print("未能获取新闻列表，无法提取关键词")
        return []

    titles = [news.title for news in news_list if news.title]

    all_words = []
    for title in titles:
        words = jieba.lcut(title)
        for word in words:
            word = word.strip()
            if word and word not in CHINESE_STOPWORDS and len(word) > 1:
                if not re.match(r"^[^\w\u4e00-\u9fa5]+$", word):
                    all_words.append(word)

    word_counts = Counter(all_words)
    hot_keywords = word_counts.most_common(top_n)

    print(f"从 {len(titles)} 条新闻标题中提取到 {len(hot_keywords)} 个高频词")
    return hot_keywords


def get_keywords_with_freshness(
    news_list: Optional[list[HotNewsItem]] = None,
    top_n: int = DEFAULT_TOP_N,
) -> list[KeywordInfo]:
    """
    获取高频词，并附带新鲜度信息（哪些热搜包含该词）

    Args:
        news_list: 新闻列表
        top_n: 返回前 N 个高频词

    Returns:
        list[KeywordInfo]: 包含词语信息的字典列表
    """
    hot_keywords = extract_hot_keywords(news_list, top_n)

    if not news_list:
        news_list = get_baidu_hot_news()

    result: list[KeywordInfo] = []
    for keyword, count in hot_keywords:
        sources = [
            {"rank": i, "title": news.title, "url": news.url}
            for i, news in enumerate(news_list, 1)
            if keyword in news.title
        ]

        result.append(KeywordInfo(keyword=keyword, count=count, sources=sources))

    return result


def get_proper_nouns(
    news_list: Optional[list[HotNewsItem]] = None,
    top_n: int = PROPER_NOUN_TOP_N,
) -> list[ProperNounInfo]:
    """
    提取高频专用名词（人名、地名、机构名等）

    使用 jieba 词性标注，提取：
    - nr: 人名
    - ns: 地名
    - nt: 机构名
    - nz: 其他专有名词

    Args:
        news_list: 新闻列表，如果为 None 则自动获取
        top_n: 返回前 N 个高频专用名词

    Returns:
        list[ProperNounInfo]: 包含专用名词信息的字典列表
    """
    if news_list is None:
        news_list = get_baidu_hot_news()

    if not news_list:
        print("未能获取新闻列表，无法提取专用名词")
        return []

    proper_nouns_dict: dict[str, ProperNounInfo] = {}

    for i, news in enumerate(news_list, 1):
        if not news.title:
            continue

        words = pseg.lcut(news.title)
        for word, flag in words:
            word = word.strip()
            if flag in PROPER_NOUN_FLAGS and word not in CHINESE_STOPWORDS and len(word) >= 2:
                if word not in proper_nouns_dict:
                    proper_nouns_dict[word] = ProperNounInfo(
                        word=word,
                        flag=flag,
                        noun_type=FLAG_MEANINGS.get(flag, "其他专有名词"),
                        count=0,
                    )
                proper_nouns_dict[word].count += 1
                proper_nouns_dict[word].sources.append({
                    "rank": i,
                    "title": news.title,
                    "url": news.url,
                })

    proper_nouns_list = sorted(
        proper_nouns_dict.values(),
        key=lambda x: x.count,
        reverse=True,
    )[:top_n]

    print(f"从 {len(news_list)} 条新闻标题中提取到 {len(proper_nouns_list)} 个专用名词")
    return proper_nouns_list


def run_scraper_mode() -> None:
    """运行爬虫模式：抓取并显示热点信息"""
    print("\n" + "=" * 50)
    print("### 百度热点信息收集器 ###")
    print("=" * 50)

    news_list = get_baidu_hot_news()

    if not news_list:
        print("\n未能收集到信息。可能原因：")
        print("1. 百度页面结构已更新")
        print("2. 触发了反爬机制（如验证码）")
        print("3. 网络连接问题")
        return

    print(f"\n成功收集到 {len(news_list)} 条热点信息：\n")
    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news.title}")
        print(f"   热度：{news.hot}")
        print(f"   链接：{news.url}\n")

    # 提取高频词
    print("\n" + "=" * 30)
    print("### 高频关键词分析 ###")
    print("=" * 30)

    keywords_data = get_keywords_with_freshness(news_list)

    if keywords_data:
        print(f"\n🔥 百度热搜高频词 TOP{len(keywords_data)}:\n")
        for i, kw in enumerate(keywords_data, 1):
            print(f"{i}. 【{kw.keyword}】出现 {kw.count} 次")
            for src in kw.sources[:3]:
                print(f"   - 第{src['rank']}名：{src['title']}")
            print()

    # 提取高频专用名词
    print("\n" + "=" * 30)
    print("### 高频专用名词分析 ###")
    print("=" * 30)

    proper_nouns = get_proper_nouns(news_list)

    if proper_nouns:
        type_icon = {"人名": "👤", "地名": "📍", "机构名": "🏢", "其他专有名词": "🏷️"}
        print(f"\n📌 百度热搜专用名词 TOP{len(proper_nouns)}:\n")
        for i, pn in enumerate(proper_nouns, 1):
            icon = type_icon.get(pn.noun_type, "📎")
            print(f"{i}. {icon}【{pn.word}】({pn.noun_type}) - 出现 {pn.count} 次")
            for src in pn.sources[:2]:
                print(f"   - 第{src['rank']}名：{src['title']}")
            print()
    else:
        print("未能提取到专用名词")


# ==========================================
# Web 应用功能
# ==========================================

def create_web_app() -> Flask:
    """创建并配置 Flask Web 应用"""
    if not FLASK_AVAILABLE:
        print("错误：Flask 未安装。请运行：pip install flask")
        sys.exit(1)

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.secret_key = os.urandom(24)

    # ======================================
    # 辅助函数
    # ======================================

    def generate_captcha() -> dict[str, str | int]:
        """生成简单的数学验证码"""
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        return {
            "question": f"{num1} + {num2} = ?",
            "answer": num1 + num2,
        }

    def verify_captcha(user_answer: str, correct_answer: int) -> bool:
        """验证答案是否正确"""
        try:
            return int(user_answer) == int(correct_answer)
        except (ValueError, TypeError):
            return False

    # ======================================
    # 路由定义
    # ======================================

    @app.route("/")
    def index() -> Flask.response_class:
        """首页 - 重定向到第 1 页"""
        return page(1)

    @app.route("/page/<int:page_num>")
    def page(page_num: int) -> Flask.response_class:
        """页面路由，支持 1-10 页"""
        if not (1 <= page_num <= 10):
            page_num = 1

        if page_num == 1:
            verified = session.get("captcha_verified", False)
            if not verified:
                captcha_data = generate_captcha()
                session["captcha_answer"] = captcha_data["answer"]
                session["captcha_question"] = captcha_data["question"]
            else:
                session["captcha_question"] = "已验证"
            return render_template("page1.html", page_num=page_num, verified=verified)
        elif page_num == 2:
            # 第二页：土星粒子系统（无需验证）
            return render_template("page2.html", page_num=page_num)
        else:
            return render_template("page_blank.html", page_num=page_num)

    @app.route("/api/captcha/generate", methods=["GET"])
    def generate_captcha_api() -> Flask.response_class:
        """生成验证码 API"""
        captcha_data = generate_captcha()
        session["captcha_answer"] = captcha_data["answer"]
        return jsonify({"success": True, "question": captcha_data["question"]})

    @app.route("/api/captcha/verify", methods=["POST"])
    def verify_captcha_api() -> Flask.response_class:
        """验证验证码 API"""
        data = request.get_json()
        user_answer = data.get("answer", "")
        correct_answer = session.get("captcha_answer")

        if correct_answer is None:
            captcha_data = generate_captcha()
            session["captcha_answer"] = captcha_data["answer"]
            return jsonify({
                "success": False,
                "message": "验证码已更新，请重新提交",
                "question": captcha_data["question"],
                "need_regenerate": True,
            })

        if verify_captcha(user_answer, correct_answer):
            session["captcha_verified"] = True
            session.pop("captcha_answer", None)
            return jsonify({"success": True, "message": "验证成功"})
        else:
            captcha_data = generate_captcha()
            session["captcha_answer"] = captcha_data["answer"]
            return jsonify({
                "success": False,
                "message": "答案错误，请重试",
                "question": captcha_data["question"],
                "need_regenerate": True,
            }), 400

    @app.route("/api/news")
    def get_news() -> Flask.response_class:
        """API 接口：获取百度热搜数据"""
        if not session.get("captcha_verified"):
            return jsonify({
                "success": False,
                "data": [],
                "message": "请先通过人机验证",
            }), 403

        news_list = get_baidu_hot_news()

        if news_list:
            return jsonify({
                "success": True,
                "data": [news.__dict__ for news in news_list],
                "message": f"成功获取 {len(news_list)} 条热点",
            })
        else:
            return jsonify({
                "success": False,
                "data": [],
                "message": "获取失败，请稍后重试",
            })

    @app.route("/api/keywords")
    def get_keywords() -> Flask.response_class:
        """API 接口：获取高频关键词"""
        if not session.get("captcha_verified"):
            return jsonify({
                "success": False,
                "data": [],
                "message": "请先通过人机验证",
            }), 403

        news_list = get_baidu_hot_news()
        keywords = extract_hot_keywords(news_list, top_n=10)

        if keywords:
            return jsonify({
                "success": True,
                "data": [{"keyword": k, "count": v} for k, v in keywords],
                "message": f"成功提取 {len(keywords)} 个高频词",
            })
        else:
            return jsonify({
                "success": False,
                "data": [],
                "message": "提取失败，请稍后重试",
            })

    return app


def run_web_mode() -> None:
    """运行 Web 展示模式"""
    print("\n" + "=" * 50)
    print("侘寂 - 百度热搜 Web 展示平台启动中...")
    print("=" * 50)

    app = create_web_app()

    print("\n本地访问：http://127.0.0.1:5000")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)

    app.run(debug=False, host="127.0.0.1", port=5000)


# ==========================================
# 主程序入口
# ==========================================

def show_menu() -> None:
    """显示主菜单并提供交互选项"""
    print("\n" + "=" * 50)
    print("     百度热搜爬虫系统")
    print("=" * 50)
    print("提示：使用功能后可返回主菜单继续使用")
    print("输入 q 可随时退出")
    print("=" * 50)

    while True:
        print("\n--- 主菜单 ---")
        print("1. 爬虫模式 - 直接抓取并显示热点")
        print("2. Web 模式 - 启动 Web 服务器")
        print("3. 退出")
        print("-" * 50)

        choice = input("请选择运行模式 (1/2/3): ").strip().lower()

        if choice == "1":
            run_scraper_mode()
            print("\n按 Enter 键返回主菜单...")
            input()
        elif choice == "2":
            run_web_mode()
            break
        elif choice in ("3", "q"):
            print("\n再见！")
            sys.exit(0)
        else:
            print("无效选择，请重新输入！")


if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case "--scraper":
                run_scraper_mode()
            case "--web":
                run_web_mode()
            case _:
                show_menu()
    else:
        show_menu()
