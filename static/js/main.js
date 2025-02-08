// static/js/main.js

// カメラ起動・停止のボタンイベント
$('#startButton').click(() => {
    Quagga.init({
      inputStream: {
        name: "Live",
        type: "LiveStream",
        target: document.querySelector('#quagga'),
        constraints: {
          width: { min: 640 },
          height: { min: 250 },
          aspectRatio: { min: 1.5, max: 2 },
          facingMode: "environment" // リアカメラ
        },
      },
      decoder: {
        readers: ["ean_reader"]  // ISBNバーコードはEAN形式
      },
    }, function(err) {
      if (err) {
        console.error(err);
        return;
      }
      Quagga.start();
    });
  
    // バーコードが処理されるたびに実行されるイベント
    Quagga.onDetected(data => {
      const isbn = data.codeResult.code;
      $('#isbn').val(isbn);
      // 一度読み取ったら停止（必要に応じて継続読み取りに変更可）
      Quagga.stop();
      // サーバーにISBNを送信して書籍情報を取得
      $.ajax({
        url: '/scan',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ isbn: isbn }),
        success: function(response) {
          addBookToTable(response);
        },
        error: function(err) {
          alert("書籍情報の取得に失敗しました");
        }
      });
    });
  });
  
  $('#stopButton').click(() => {
    Quagga.stop();
  });
  
  // 書籍情報をテーブルに追加する関数
  function addBookToTable(book) {
    const row = `<tr>
      <td>${book.isbn}</td>
      <td>${book.title}</td>
      <td>${book.authors}</td>
      <td>${book.publisher}</td>
      <td>${book.publishedDate}</td>
    </tr>`;
    $('#books-table tbody').append(row);
  }
  
  // CSVダウンロードボタンのクリックイベント
  $('#download-csv').click(() => {
    window.location.href = '/download';
  });
  