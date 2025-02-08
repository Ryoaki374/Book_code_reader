# app.py
from flask import Flask, render_template, request, jsonify, Response
import requests
import csv
import os
from io import StringIO
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# .env から楽天 API キーを取得
RAKUTEN_API_KEY = os.getenv("RAKUTEN_API_KEY")
# 記録した書籍情報を保持するリスト（CSV出力用）
book_records = []

def fetch_book_data(isbn):
    book_info = {
        'isbn': isbn,
        'title': '',
        'authors': '',
        'publisher': '',
        'publishedDate': ''
    }
    
    # --- Google Books API ---
    google_url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
    google_resp = requests.get(google_url)
    if google_resp.status_code == 200:
        google_data = google_resp.json()
        if google_data.get('totalItems', 0) > 0:
            volume_info = google_data['items'][0]['volumeInfo']
            book_info['title'] = volume_info.get('title', '')
            book_info['authors'] = ', '.join(volume_info.get('authors', []))
            book_info['publisher'] = volume_info.get('publisher', '')
            book_info['publishedDate'] = volume_info.get('publishedDate', '')
    
    # --- 楽天ブックス API ---
    rakuten_url = "https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404"
    params = {
        'isbn': isbn,
        'applicationId': RAKUTEN_API_KEY,
    }
    rakuten_resp = requests.get(rakuten_url, params=params)
    if rakuten_resp.status_code == 200:
        rakuten_data = rakuten_resp.json()
        if rakuten_data.get('count', 0) > 0:
            rakuten_item = rakuten_data['Items'][0]['Item']
            if not book_info['title']:
                book_info['title'] = rakuten_item.get('title', '')
            if not book_info['authors']:
                book_info['authors'] = rakuten_item.get('author', '')
            if not book_info['publisher']:
                book_info['publisher'] = rakuten_item.get('publisherName', '')
            if not book_info['publishedDate']:
                book_info['publishedDate'] = rakuten_item.get('salesDate', '')
    
    # --- OpenBD API ---
    openbd_url = f'https://api.openbd.jp/v1/get?isbn={isbn}'
    openbd_resp = requests.get(openbd_url)
    if openbd_resp.status_code == 200:
        openbd_data = openbd_resp.json()
        if openbd_data and openbd_data[0]:
            summary = openbd_data[0].get('summary', {})
            if not book_info['title']:
                book_info['title'] = summary.get('title', '')
            if not book_info['authors']:
                book_info['authors'] = summary.get('author', '')
            if not book_info['publisher']:
                book_info['publisher'] = summary.get('publisher', '')
            if not book_info['publishedDate']:
                book_info['publishedDate'] = summary.get('pubdate', '')
    return book_info

# ルート（メイン画面）を表示
@app.route('/')
def index():
    return render_template('index.html')

# ISBNを元に書籍情報を取得（ユーザ確認前）
@app.route('/fetch_book_info', methods=['POST'])
def fetch_book_info():
    data = request.get_json()
    isbn = data.get('isbn')
    book_info = fetch_book_data(isbn)
    return jsonify(book_info)

# ユーザ確認後、書籍情報を記録に追加
@app.route('/commit_book_info', methods=['POST'])
def commit_book_info():
    book_info = request.get_json()
    book_records.append(book_info)
    return jsonify({'status': 'success'})

# CSVダウンロード用エンドポイント
@app.route('/download_csv')
def download_csv():
    si = StringIO()
    fieldnames = ['isbn', 'title', 'authors', 'publisher', 'publishedDate']
    writer = csv.DictWriter(si, fieldnames=fieldnames)
    writer.writeheader()
    for record in book_records:
        writer.writerow(record)
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=books.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)
