import os
from flask import Flask, render_template, request, jsonify, make_response
import requests
import csv
import io

# 開発中は python-dotenv を使って .env ファイルの内容を読み込む
# 本番環境では、ホスティングサービスの環境変数設定を利用してください。
from dotenv import load_dotenv
load_dotenv()  # カレントディレクトリの .env ファイルを読み込む

app = Flask(__name__)

# 環境変数から楽天ブックスAPIのアプリケーションIDを取得
RAKUTEN_APPLICATION_ID = os.environ.get('RAKUTEN_APPLICATION_ID')
if not RAKUTEN_APPLICATION_ID:
    raise ValueError("環境変数 RAKUTEN_APPLICATION_ID が設定されていません。")

# 書籍情報を保持するリスト（デモ用）
books = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lookup', methods=['POST'])
def lookup():
    data = request.get_json()
    barcode = data.get('barcode', '').strip()
    
    if not barcode:
        return jsonify({'status': 'error', 'message': 'バーコードが送信されていません。'})
    
    # --- 1. Google Books API で検索 ---
    google_url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{barcode}'
    response_google = requests.get(google_url)
    if response_google.status_code == 200:
        result_google = response_google.json()
        if 'items' in result_google:
            volume_info = result_google['items'][0]['volumeInfo']
            title = volume_info.get('title', '不明')
            authors = ', '.join(volume_info.get('authors', ['不明']))
            publisher = volume_info.get('publisher', '不明')
            publishedDate = volume_info.get('publishedDate', '不明')
            
            book_entry = {
                'barcode': barcode,
                'title': title,
                'authors': authors,
                'publisher': publisher,
                'publishedDate': publishedDate
            }
            books.append(book_entry)
            return jsonify({'status': 'success', 'book': book_entry})
    
    # --- 2. 楽天ブックスAPI で検索 ---
    rakuten_url = (
        f'https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404'
        f'?format=json&isbn={barcode}&applicationId={RAKUTEN_APPLICATION_ID}'
    )
    response_rakuten = requests.get(rakuten_url)
    if response_rakuten.status_code == 200:
        result_rakuten = response_rakuten.json()
        if 'Items' in result_rakuten and len(result_rakuten['Items']) > 0:
            item = result_rakuten['Items'][0]['Item']
            title = item.get('title', '不明')
            author = item.get('author', '不明')
            publisher = item.get('publisherName', '不明')
            publishedDate = item.get('salesDate', '不明')
            
            book_entry = {
                'barcode': barcode,
                'title': title,
                'authors': author,
                'publisher': publisher,
                'publishedDate': publishedDate
            }
            books.append(book_entry)
            return jsonify({'status': 'success', 'book': book_entry})
    
    # --- 3. OpenBD API で検索 ---
    openbd_url = f'https://api.openbd.jp/v1/get?isbn={barcode}'
    response_openbd = requests.get(openbd_url)
    if response_openbd.status_code == 200:
        result_openbd = response_openbd.json()
        if result_openbd and result_openbd[0]:
            summary = result_openbd[0].get('summary', {})
            title = summary.get('title', '不明')
            author = summary.get('author', '不明')
            publisher = summary.get('publisher', '不明')
            publishedDate = summary.get('pubdate', '不明')
            
            book_entry = {
                'barcode': barcode,
                'title': title,
                'authors': author,
                'publisher': publisher,
                'publishedDate': publishedDate
            }
            books.append(book_entry)
            return jsonify({'status': 'success', 'book': book_entry})
    
    return jsonify({'status': 'error', 'message': '該当する書籍が見つかりませんでした。'})

@app.route('/download_csv')
def download_csv():
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['バーコード', '書名', '著者名', '出版社', '発行年'])
    for book in books:
        writer.writerow([book['barcode'], book['title'], book['authors'], book['publisher'], book['publishedDate']])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=books.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)
