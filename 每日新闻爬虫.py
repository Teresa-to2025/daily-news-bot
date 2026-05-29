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
        """获取财经新闻 - 使用AKShare获取财经新闻"""
        news_list = []
        
        # 方法1：使用AKShare获取财经新闻（尝试多个股票以获取更多新闻）
        try:
            import sys
            sys.path.insert(0, r'd:\应用工具-python代码\deps')
            import akshare as ak
            
            # 尝试多个热门股票获取财经新闻
            symbols = ["300059", "600519", "000001", "601318", "600036", "601166", "000858", "600276"]
            
            for symbol in symbols:
                if len(news_list) >= 20:
                    break
                    
                try:
                    news_df = ak.stock_news_em(symbol=symbol)
                    
                    if news_df is not None and len(news_df) > 0:
                        for _, row in news_df.iterrows():
                            if len(news_list) >= 20:
                                break
                                
                            title = row.get('新闻标题', '').strip()
                            pub_time = row.get('发布时间', '')
                            
                            # 严格过滤前一天的新闻
                            if not self._is_yesterday_news(pub_time):
                                continue
                            
                            if title and len(title) > 5:
                                # 检查是否重复
                                if not any(n['title'] == title for n in news_list):
                                    news_list.append({
                                        'title': title,
                                        'source': row.get('文章来源', '东方财富'),
                                        'link': row.get('新闻链接', ''),
                                        'category': '财经'
                                    })
                except:
                    continue
        except Exception as e:
            print(f"AKshare财经新闻失败: {e}")
        
        # 备用方案：使用新浪财经API
        if len(news_list) == 0:
            try:
                url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=1"
                response = self.session.get(url, timeout=15)
                data = response.json()
                
                if data.get('code') == 0:
                    items = data.get('result', {}).get('data', [])
                    for item in items:
                        title = item.get('title', '').strip()
                        ctime = item.get('ctime', '')
                        
                        # 添加日期过滤
                        if not self._is_yesterday_news(ctime, is_timestamp=True):
                            continue
                        
                        if title and len(title) > 5:
                            news_list.append({
                                'title': title,
                                'source': '新浪财经',
                                'link': item.get('url', ''),
                                'category': '财经',
                                'intro': item.get('intro', '')
                            })
                        
                        if len(news_list) >= 20:
                            break
            except Exception as e:
                print(f"新浪财经财经新闻失败: {e}")

        return news_list

    def _is_yesterday_news(self, pub_time, is_timestamp=False):
        """判断新闻是否为前一天的"""
        if not pub_time:
            return False
        
        try:
            if is_timestamp:
                # 时间戳格式（秒级）
                news_date = datetime.fromtimestamp(int(pub_time)).strftime('%Y-%m-%d')
            else:
                # 字符串格式，如 "2024-01-15 10:30:00" 或 "2024-01-15"
                pub_time_str = str(pub_time).strip()
                # 提取日期部分（取前10个字符，格式为 YYYY-MM-DD）
                if len(pub_time_str) >= 10:
                    news_date = pub_time_str[:10]
                else:
                    return False
            
            # 严格匹配前一天日期
            return news_date == self.yesterday_str
        except Exception as e:
            print(f"日期解析失败: {e}, pub_time={pub_time}")
            return False

    def get_social_news(self):
        """获取社会新闻 - 首选澎湃，备用新浪"""
        news_list = []
        
        # 方法1：使用澎湃新闻API获取社会新闻
        try:
            url = "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            hot_news = data.get('data', {}).get('hotNews', [])
            if hot_news:
                for item in hot_news:
                    if isinstance(item, dict):
                        title = item.get('name', '').strip()
                        pub_time_long = item.get('pubTimeLong', '')
                        cont_id = item.get('contId', '')
                        
                        # 过滤前一天的新闻（pubTimeLong是毫秒级时间戳）
                        if pub_time_long:
                            try:
                                news_date = datetime.fromtimestamp(int(pub_time_long) / 1000).strftime('%Y-%m-%d')
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
                                'link': f"https://www.thepaper.cn/newsDetail_forward_{cont_id}" if cont_id else '',
                                'category': '社会'
                            })
                    
                    if len(news_list) >= 20:
                        break
                        
                if news_list:
                    return news_list
        except Exception as e:
            print(f"澎湃新闻失败: {e}")
        
        # 方法2：使用澎湃新闻社会新闻频道
        try:
            url = "https://cache.thepaper.cn/contentapi/wwwChannel/getByChannelId?channelId=25950&pageSize=20&page=1"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            contents = data.get('data', {}).get('contentList', [])
            if contents:
                for item in contents:
                    title = item.get('title', '').strip()
                    pub_time_long = item.get('pubTimeLong', '')
                    cont_id = item.get('contId', '')
                    
                    # 过滤前一天的新闻
                    if pub_time_long:
                        try:
                            news_date = datetime.fromtimestamp(int(pub_time_long) / 1000).strftime('%Y-%m-%d')
                            if news_date != self.yesterday_str:
                                continue
                        except:
                            pass
                    
                    if title and len(title) > 5:
                        exclude_keywords = ['股市', '股票', '基金', '理财', '银行', '保险', '经济', '金融', 'A股', '沪指', '深证', '创业板', '科创板', '北交所', '涨停', '跌停', '股价', '市值', '分红', '财报']
                        if any(keyword in title for keyword in exclude_keywords):
                            continue
                            
                        news_list.append({
                            'title': title,
                            'source': '澎湃新闻',
                            'link': f"https://www.thepaper.cn/newsDetail_forward_{cont_id}" if cont_id else '',
                            'category': '社会'
                        })
                    
                    if len(news_list) >= 20:
                        break
                        
                if news_list:
                    return news_list
        except Exception as e:
            print(f"澎湃新闻社会频道失败: {e}")
        
        # 方法3：使用新浪国内新闻API（备用）
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&page=1"
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            status_code = data.get('result', {}).get('status', {}).get('code')
            if status_code == 0:
                items = data.get('result', {}).get('data', [])
                for item in items:
                    title = item.get('title', '').strip()
                    ctime = item.get('ctime', '')
                    
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
                            'source': '新浪国内',
                            'link': item.get('url', ''),
                            'category': '社会'
                        })
                    
                    if len(news_list) >= 20:
                        break
                        
                if news_list:
                    return news_list
        except Exception as e:
            print(f"新浪国内新闻失败: {e}")

        return news_list

    def format_news_content(self, finance_news, social_news):
        """格式化新闻内容"""
        content = f" **每日新闻速递** ({self.yesterday_display})\n\n"
        
        # 财经新闻
        content += "💰 **财经新闻**\n"
        if finance_news:
            for i, news in enumerate(finance_news[:20], 1):
                content += f"{i}. {news['title']}\n"
                if news['link']:
                    content += f"   🔗 {news['link']}\n"
        else:
            content += "暂无数据\n"
        
        content += "\n📰 **社会新闻**\n"
        if social_news:
            for i, news in enumerate(social_news[:20], 1):
                content += f"{i}. {news['title']}\n"
                if news['link']:
                    content += f"   🔗 {news['link']}\n"
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
        try:
            print(f"  - {news['title']}")
        except UnicodeEncodeError:
            print(f"  - {news['title'].encode('gbk', 'ignore').decode('gbk')}")
    
    print("\n社会新闻:")
    for news in social_news[:5]:
        try:
            print(f"  - {news['title']}")
        except UnicodeEncodeError:
            print(f"  - {news['title'].encode('gbk', 'ignore').decode('gbk')}")
    
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
