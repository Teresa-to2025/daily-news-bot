# -*- coding: utf-8 -*-
"""
每日新闻爬虫 - 爬取财经、社会新闻并推送到飞书
"""
import requests
import json
from datetime import datetime, timedelta
import time

class NewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # 获取前一天的日期
        self.yesterday = datetime.now() - timedelta(days=1)
        self.yesterday_str = self.yesterday.strftime('%Y-%m-%d')
        self.yesterday_date = self.yesterday.strftime('%Y%m%d')
        self.yesterday_display = self.yesterday.strftime('%Y年%m月%d日')

    def get_finance_news(self):
        """获取财经新闻 - 使用新浪财经API"""
        news_list = []
        
        # 方法1：使用新浪财经API获取财经新闻
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=1"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if data.get('code') == 0:
                items = data.get('result', {}).get('data', [])
                for item in items:
                    title = item.get('title', '').strip()
                    intro = item.get('intro', '')
                    ctime = item.get('ctime', '')
                    
                    # 过滤前一天的新闻
                    if ctime:
                        try:
                            news_date = datetime.fromtimestamp(int(ctime)).strftime('%Y-%m-%d')
                            if news_date != self.yesterday_str:
                                continue
                        except:
                            pass
                    
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'source': '新浪财经',
                            'link': item.get('url', ''),
                            'category': '财经',
                            'intro': intro
                        })
                    
                    if len(news_list) >= 10:
                        break
        except Exception as e:
            print(f"新浪财经财经新闻失败: {e}")
        
        # 备用方案：使用东方财富新闻
        if len(news_list) == 0:
            try:
                import sys
                sys.path.insert(0, r'd:\应用工具-python代码\deps')
                import akshare as ak
                
                news_df = ak.stock_news_em(symbol="300059")
                
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

        return news_list

    def get_social_news(self):
        """获取社会新闻 - 首选澎湃/新浪，备用腾讯"""
        news_list = []
        
        # 方法1：使用澎湃新闻API获取社会新闻
        try:
            url = "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if data.get('data', {}).get('hotNews1'):
                items = data['data']['hotNews1']
                for item in items:
                    title = item.get('name', '').strip()
                    pub_time = item.get('pubTimeLong', '')
                    
                    # 过滤前一天的新闻
                    if pub_time:
                        try:
                            news_date = datetime.fromtimestamp(int(pub_time) / 1000).strftime('%Y-%m-%d')
                            if news_date != self.yesterday_str:
                                continue
                        except:
                            pass
                    
                    # 排除财经、股票相关标题
                    if title and len(title) > 5:
                        exclude_keywords = ['股市', '股票', '基金', '理财', '银行', '保险', '经济', '金融', 'A股', '沪指', '深证', '创业板', '科创板', '北交所', '涨停', '跌停', '股价', '市值', '分红', '财报']
                        if any(keyword in title for keyword in exclude_keywords):
                            continue
                            
                        news_list.append({
                            'title': title,
                            'source': '澎湃新闻',
                            'link': f"https://www.thepaper.cn/newsDetail_forward_{item.get('id', '')}",
                            'category': '社会'
                        })
                    
                    if len(news_list) >= 10:
                        break
                        
                if news_list:
                    return news_list
        except Exception as e:
            print(f"澎湃新闻失败: {e}")
        
        # 方法2：使用新浪社会新闻API
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2510&k=&num=50&page=1"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if data.get('code') == 0:
                items = data.get('result', {}).get('data', [])
                for item in items:
                    title = item.get('title', '').strip()
                    ctime = item.get('ctime', '')
                    
                    # 过滤前一天的新闻
                    if ctime:
                        try:
                            news_date = datetime.fromtimestamp(int(ctime)).strftime('%Y-%m-%d')
                            if news_date != self.yesterday_str:
                                continue
                        except:
                            pass
                    
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'source': '新浪新闻',
                            'link': item.get('url', ''),
                            'category': '社会'
                        })
                    
                    if len(news_list) >= 10:
                        break
                        
                if news_list:
                    return news_list
        except Exception as e:
            print(f"新浪新闻失败: {e}")
        
        # 方法3：使用腾讯新闻API
        try:
            url = "https://r.inews.qq.com/getSubNewsListData?scene=2&sub_id=27&newsid=&news_top_num=0&refer=&ext=&offset=0&limit=50"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            if data.get('ret') == 0:
                items = data.get('data', {}).get('newslist', [])
                for item in items:
                    title = item.get('title', '').strip()
                    timestamp = item.get('timestamp', '')
                    
                    # 过滤前一天的新闻
                    if timestamp:
                        try:
                            news_date = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
                            if news_date != self.yesterday_str:
                                continue
                        except:
                            pass
                    
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'source': '腾讯新闻',
                            'link': item.get('url', ''),
                            'category': '社会'
                        })
                    
                    if len(news_list) >= 10:
                        break
                        
                if news_list:
                    return news_list
        except Exception as e:
            print(f"腾讯新闻失败: {e}")

        return news_list

    def format_news_content(self, finance_news, social_news):
        """格式化新闻内容"""
        content = f" **每日新闻速递** ({self.yesterday_display})\n\n"
        
        # 财经新闻
        content += "💰 **财经新闻**\n"
        if finance_news:
            for i, news in enumerate(finance_news[:8], 1):
                content += f"{i}. {news['title']}\n"
                if news['link']:
                    content += f"   🔗 {news['link']}\n"
        else:
            content += "暂无数据\n"
        
        content += "\n **社会新闻**\n"
        if social_news:
            for i, news in enumerate(social_news[:8], 1):
                content += f"{i}. {news['title']}\n"
                if news['link']:
                    content += f"    {news['link']}\n"
        else:
            content += "暂无数据\n"
        
        content += f"\n 数据来源：澎湃新闻、新浪新闻、腾讯新闻\n"
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
    print(f"目标日期: {crawler.yesterday_display}")
    
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
