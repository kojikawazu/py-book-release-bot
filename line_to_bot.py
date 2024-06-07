"""
技術書の新刊情報を取得し、
LINEメッセージとして送信する

1. SE Shopのウェブサイトから技術書の情報を取得
2. 最新の技術書をフィルタリング
3. フィルタリングされた書籍情報をLINEメッセージとしてフォーマット
4. フォーマットされたメッセージをLINEに送信
5. AWS Lambdaでの実行をサポート
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

# 環境変数を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID              = os.getenv('LINE_USER_ID')
LINE_BOT_PUSH_URL         = os.getenv('LINE_BOT_PUSH_URL')
DEDAULT_KEYWORD           = os.getenv('DEDAULT_KEYWORD')
SESHOP_URL                = os.getenv('SESHOP_URL')

# ---------------------------------------------------------------------------------

def fetch_books_from_page(url):
    """
    指定されたURLから技術書の情報を取得する

    Args:
        url (str): 技術書の情報を取得するためのURL
    
    Returns:
        list: 書籍情報のリスト。各書籍は辞書形式で 'title', 'release_date', 'description' を含む。
    """
    
    print(f"Requesting URL: {url}")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    #print(f"Response content for keyword '{keyword}':")
    #print(soup.prettify())
    
    books = []
    for item in soup.find_all('div', class_='col-md-4 col-sm-6'):
        title_tag = item.find('div', class_='txt').find('a')
        title = title_tag.text.strip() if title_tag else 'N/A'
        
        release_date_tag = item.find('span', class_='date')
        release_date = release_date_tag.text.strip() if release_date_tag else 'N/A'
        
        description_tags = item.find('div', class_='txt').find_all('p')
        description = description_tags[1].text.strip() if len(description_tags) > 1 else 'N/A'
        
        books.append({
            'title': title,
            'release_date': release_date,
            'description': description
        })
    
    if not books:
        print(f"No books found.")
    
    return books

def fetch_all_books():
    """
    すべてのカテゴリとページから技術書の情報を取得する

    Returns:
        list: すべての取得した書籍情報のリスト
    """
    all_books = []
    
    for category in [7, 8]:
        for page in range(1, 5):
            url = f'{SESHOP_URL}/{category}?p={page}'
            books = fetch_books_from_page(url)
            all_books.extend(books)
    
    return all_books

def filter_books_by_3_months_and_upcoming(books):
    """
    過去3ヶ月以内の書籍および今後発売予定の書籍をフィルタリングする

    Args:
        books (list): すべての取得した書籍情報のリスト
    
    Returns:
        list: フィルタリングされた書籍情報のリスト
    """
    
    today = datetime.today().date()
    three_months_ago = today - timedelta(days=90)
    filtered_books = []
    for book in books:
        try:
            release_date_str = book['release_date'].replace('発売', '').strip()
            release_date = datetime.strptime(release_date_str, '%Y.%m.%d').date()
            # 3ヶ月以内の書籍または発売予定の書籍をフィルタリング
            if release_date > today or three_months_ago <= release_date <= today:
                filtered_books.append(book)
        except ValueError:
            continue
    return filtered_books

def sort_books_by_date(books):
    """
    書籍情報を発売日順に並べ替える

    Args:
        books (list): フィルタリングされた書籍情報のリスト
    
    Returns:
        list: 発売日順に並べ替えられた書籍情報のリスト
    """
    return sorted(books, key=lambda x: datetime.strptime(x['release_date'].replace('発売', '').strip(), '%Y.%m.%d').date(), reverse=True)

def format_message(books):
    """
    書籍情報をフォーマットしてメッセージを作成する

    Args:
        books (list): フィルタリングされた書籍情報のリスト
    
    Returns:
        str: フォーマットされたメッセージ
    """
    if not books:
        return "新刊書籍は見つかりませんでした。"
    
    message = "近日発売予定の技術書籍:\n\n"
    for book in books:
        message += f"タイトル: {book['title']}\n発売日: {book['release_date']}\n説明: {book['description']}\n\n"
    
    return message

def send_line_message(message):
    """
    フォーマットされたメッセージをLINEに送信する

    Args:
        message (str): 送信したいメッセージ
    
    Returns:
        None
    """
    
    line_api_url = LINE_BOT_PUSH_URL
    line_user_id = LINE_USER_ID
    line_channel_access_token = LINE_CHANNEL_ACCESS_TOKEN

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {line_channel_access_token}'
    }
    
    # メッセージを5000文字以内に分割
    messages = [message[i:i+5000] for i in range(0, len(message), 5000)]
    
    for msg in messages:
        payload = {
            'to': line_user_id,
            'messages': [{
                'type': 'text',
                'text': msg
            }]
        }
        
        response = requests.post(line_api_url, headers=headers, json=payload)
        print(response.status_code, response.text)

# ---------------------------------------------------------------------------------

def main():
    """
    書籍情報を取得し、フィルタリングし、メッセージを作成してLINEに送信する
    """
    
    all_books      = fetch_all_books()
    filtered_books = filter_books_by_3_months_and_upcoming(all_books)
    sorted_books   = sort_books_by_date(filtered_books)

    if sorted_books:
        message = format_message(sorted_books)
        send_line_message(message)
    else:
        send_line_message("新刊書籍は見つかりませんでした。")

def lambda_handler(event, context):
    """
    AWS Lambdaのエントリポイント

    Args:
        event (dict): Lambda 関数に渡されるイベントデータ
        context (object): ランタイム情報を提供するコンテキストオブジェクト
    
    Returns:
        dict: ステータスコードとメッセージを含むレスポンス
    """
    
    main()
    return {
        'statusCode': 200,
        'body': json.dumps('News sent successfully!')
    }

if __name__ == "__main__":
    main()
