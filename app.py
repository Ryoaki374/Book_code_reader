from flask import Flask, render_template, request, jsonify, make_response
import requests
import csv
import io

app = Flask(__name__)

# デモ用にグローバル変数で書籍情報を保持（実際はセッションやDBを利用するのが望ましい）
books = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lookup', methods=['POST'])
def lookup():
    # クライアントから送られた JSON の中からバーコードを取得
    data = request.get_json()
    barcode = data.get('barcode', '')
    
    # Google Books API を利用して、ISBN から書籍情報を取得
    api_url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{barcode}'
    response = requests.get(api_url)
    
    if response.status_code == 200:
        result = response.json()
        if 'items' in result:
            # 1件目の結果を利用
            volume_info = result['items'][0]['volumeInfo']
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
        else:
            return jsonify({'status': 'error', 'message': '該当する書籍が見つかりませんでした。'})
    else:
        return jsonify({'status': 'error', 'message': '外部APIへのリクエストに失敗しました。'})

@app.route('/download_csv')
def download_csv():
    # in-memory で CSV ファイルを生成
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