# -*- coding: utf-8 -*-
"""
每日新闻爬虫 - 爬取财经、社会新闻并推送到飞书
"""
import requests
import json
from datetime import datetime
import time
import re

class NewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_finance_news(self):
        """获取财经新闻 - 使用AKshare"""
        news_list = []
        
        try:
            import sys
            sys.path.insert(0, r'd:\应用工具-python代码\deps')
            import akshare as ak
            
            # 获取财经新闻
            news_df = ak.stock_news_em(symbol="300059")  # 东方财富股票新闻
            
            if news_df is not None and len(news_df) > 0:
                for _, row in news_df.head(10).iterrows():
                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'source': row.get('文章来源', '东方财富'),
                        'link': row.get('新闻链接', ''),
                        'category': '财经'
                    })
        except Exception as e:
            print(f"AKshare财经新闻失败: {e}")
        
        # 备用方案：使用新浪财经RSS
        if len(news_list) == 0:
            try:
                url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=20&page=1"
                response = self.session.get(url, timeout=15)
                data = response.json()
                
                if data.get('code') == 0:
                    items = data.get('result', {}).get('data', [])
                    for item in items[:10]:
                        title = item.get('title', '').strip()
                        if title and len(title) > 5:
                            news_list.append({
                                'title': title,
                                'source': '新浪财经',
                                'link': item.get('url', ''),
                                'category': '财经'
                            })
            except Exception as e:
                print(f"新浪财经备用失败: {e}")

        return news_list

    def get_social_news(self):
        """获取社会新闻 - 首选澎湃，然后人民网/新华网，备用新浪/腾讯"""
        news_list = []
        
        # 方法1：使用澎湃新闻API（首选）
        try:
            url = "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if data.get('data', {}).get('hotNews1'):
                items = data['data']['hotNews1']
                for item in items[:10]:
                    title = item.get('name', '').strip()
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'source': '澎湃新闻',
                            'link': f"https://www.thepaper.cn/newsDetail_forward_{item.get('id', '')}",
                            'category': '社会'
                        })
                if news_list:
                    return news_list
        except Exception as e:
            print(f"澎湃新闻失败: {e}")
        
        # 方法2：使用人民网新闻
        try:
            url = "http://www.people.com.cn/rss/politics.xml"
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            titles = re.findall(r'<title><!$$CDATA\[(.*?)$$\]></title>', response.text)
            links = re.findall(r'<link>(.*?)</link>', response.text)
            
            if titles:
                for i, title in enumerate(titles[:10]):
                    if title and len(title) > 5 and '人民网' not in title:
                        news_list.append({
                            'title': title,
                            'source': '人民网',
                            'link': links[i] if i < len(links) else '',
                            'category': '社会'
                        })
                if news_list:
                    return news_list
        except Exception as e:
            print(f"人民网失败: {e}")
        
        # 方法3：使用新华网新闻
        try:
            url = "http://www.news.cn/fortune/rss.xml"
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            titles = re.findall(r'<title><!$$CDATA\[(.*?)$$\]></title>', response.text)
            links = re.findall(r'<link>(.*?)</link>', response.text)
            
            if titles:
                for i, title in enumerate(titles[:10]):
                    if title and len(title) > 5 and '新华网' not in title:
                        news_list.append({
                            'title': title,
                            'source': '新华网',
                            'link': links[i] if i < len(links) else '',
                            'category': '社会'
                        })
                if news_list:
                    return news_list
        except Exception as e:
            print(f"新华网失败: {e}")
        
        # 方法4：使用新浪新闻API（热点聚合备用）
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2510&k=&num=20&page=1"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if data.get('code') == 0:
                items = data.get('result', {}).get('data', [])
                for item in items[:10]:
                    title = item.get('title', '').strip()
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'source': '新浪新闻',
                            'link': item.get('url', ''),
                            'category': '社会'
                        })
                if news_list:
                    return news_list
        except Exception as e:
            print(f"新浪新闻失败: {e}")
        
        # 方法5：使用腾讯新闻API（热点聚合备用）
        try:
            url = "https://r.inews.qq.com/getSubNewsListData?scene=2&sub_id=27&newsid=&news_top_num=0&refer=&ext=&offset=0&limit=20"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if data.get('ret') == 0:
                items = data.get('data', {}).get('newslist', [])
                for item in items[:10]:
                    title = item.get('title', '').strip()
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'source': '腾讯新闻',
                            'link': item.get('url', ''),
                            'category': '社会'
                        })
                if news_list:
                    return news_list
        except Exception as e:
            print(f"腾讯新闻失败: {e}")

        return news_list

    def format_news_content(self, finance_news, social_news):
        """格式化新闻内容"""
        today = datetime.now().strftime('%Y年%m月%d日')
        
        content = f"📰 **每日新闻速递** ({today})\n\n"
        
        # 财经新闻
        content += "💰 **财经新闻**\n"
        if finance_news:
            for i, news in enumerate(finance_news[:8], 1):
                content += f"{i}. {news['title']}\n"
                if news['link']:
                    content += f"   🔗 {news['link']}\n"
        else:
            content += "暂无数据\n"
        
        content += "\n🔥 **热点新闻**\n"
        if social_news:
            for i, news in enumerate(social_news[:8], 1):
                content += f"{i}. {news['title']}\n"
                if news['link']:
                    content += f"   🔗 {news['link']}\n"
        else:
            content += "暂无数据\n"
        
        content += f"\n📊 数据来源：澎湃新闻、人民网、新华网、新浪新闻、腾讯新闻\n"
        content += f"⏰ 推送时间：{datetime.now().strftime('%H:%M')}"
        
        return content

class FeishuBot:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, title, content):
        """发送消息到飞书"""
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    }
                ]
            }
        }
        
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('StatusCode') == 0 or result.get('code') == 0:
                    print("消息发送成功！")
                    return True
                else:
                    print(f"消息发送失败: {result}")
                    return False
            else:
                print(f"HTTP错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"发送异常: {e}")
            return False

def main():
    """主函数"""
    print("开始爬取新闻...")
    
    crawler = NewsCrawler()
    
    finance_news = crawler.get_finance_news()
    social_news = crawler.get_social_news()
    
    print(f"爬取到财经新闻 {len(finance_news)} 条")
    print(f"爬取到社会新闻 {len(social_news)} 条")
    
    print("\n财经新闻:")
    for news in finance_news[:5]:
        print(f"  - {news['title']}")
    
    print("\n社会新闻:")
    for news in social_news[:5]:
        print(f"  - {news['title']}")
    
    content = crawler.format_news_content(finance_news, social_news)
    
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/50533a01-e269-4933-9a20-ccbd720ab273"
    bot = FeishuBot(webhook_url)
    
    title = "每日新闻速递"
    success = bot.send_message(title, content)
    
    if success:
        print("\n新闻推送完成！")
    else:
        print("\n新闻推送失败！")

if __name__ == "__main__":
    main()
