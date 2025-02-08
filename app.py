# app.py
from flask import Flask, render_template, request, jsonify, send_file
import os
import requests
from dotenv import load_dotenv
import csv
import io

# .env の読み込み
load_dotenv()

app = Flask(__name__)

# 書籍情報のエントリーを格納するグローバル変数（本番では DB 等の利用を検討）
book_entries = []

def fetch_book_info(isbn):
    """
    ISBN を元に Google Books API, 楽天 API, OpenBD API を順次試し、書籍情報を取得する関数
    """
    # ① Google Books API を試す
    google_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    google_response = requests.get(google_url)
    if google_response.ok:
        google_data = google_response.json()
        if 'items' in google_data and len(google_data['items']) > 0:
            volume_info = google_data['items'][0]['volumeInfo']
            title = volume_info.get('title', '')
            authors = ", ".join(volume_info.get('authors', []))
            publisher = volume_info.get('publisher', '')
            published_date = volume_info.get('publishedDate', '')
            return {
                'isbn': isbn,
                'title': title,
                'authors': authors,
                'publisher': publisher,
                'published_date': published_date
            }
    
    # ② 楽天ブックス API を試す
    rakuten_api_key = os.getenv("RAKUTEN_API_KEY")
    if rakuten_api_key:
        rakuten_url = "https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404"
        params = {
            'format': 'json',
            'isbn': isbn,
            'applicationId': rakuten_api_key
        }
        rakuten_response = requests.get(rakuten_url, params=params)
        if rakuten_response.ok:
            rakuten_data = rakuten_response.json()
            if 'Items' in rakuten_data and len(rakuten_data['Items']) > 0:
                item = rakuten_data['Items'][0]['Item']
                return {
                    'isbn': isbn,
                    'title': item.get('title', ''),
                    'authors': item.get('author', ''),
                    'publisher': item.get('publisherName', ''),
                    'published_date': item.get('salesDate', '')
                }
    
    # ③ OpenBD API を試す
    openbd_url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
    openbd_response = requests.get(openbd_url)
    if openbd_response.ok:
        openbd_data = openbd_response.json()
        if openbd_data and openbd_data[0]:
            summary = openbd_data[0].get('summary', {})
            return {
                'isbn': isbn,
                'title': summary.get('title', ''),
                'authors': summary.get('author', ''),
                'publisher': summary.get('publisher', ''),
                'published_date': summary.get('pubdate', '')
            }
    
    # いずれの API でも情報が得られなかった場合
    return None

@app.route("/")
def index():
    return render_template("index.html", book_entries=book_entries)

@app.route("/add_entry", methods=["POST"])
def add_entry():
    """
    POST リクエストで渡された ISBN を元に書籍情報を取得し、エントリーに追加する
    """
    data = request.get_json()
    isbn = data.get("isbn")
    if isbn:
        book_info = fetch_book_info(isbn)
        if book_info:
            book_entries.append(book_info)
            return jsonify({"success": True, "book": book_info})
    return jsonify({"success": False, "error": "書籍情報が取得できませんでした"}), 404

@app.route("/download_csv")
def download_csv():
    """
    登録済みの書籍情報を CSV ファイルとして出力する
    """
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["ISBN", "書名", "著者名", "出版社名", "発行年"])
    for book in book_entries:
        cw.writerow([book['isbn'], book['title'], book['authors'], book['publisher'], book['published_date']])
    output = si.getvalue()
    si.close()
    return send_file(
        io.BytesIO(output.encode('utf-8')),
        mimetype="text/csv",
        as_attachment=True,
        download_name="books.csv"  # Flask 2.x 以降は attachment_filename ではなく download_name
    )

if __name__ == "__main__":
    app.run(debug=True)
