# replace_heads_of_audio_paths_in_m3u

本リポジトリは、iTunesなどから出力したM3Uプレイリストファイルに対して、記載された音楽ファイルのパスを、移行先のNASなどのPC上の実在するパスに置換するPythonスクリプトを提供します。

---

## 🚀 実行方法

### 1. Pythonのインストール

音楽ファイルの移行先のPC上に、Pythonをインストールします。  
本リポジトリのスクリプトが動作確認されている未満のバージョンだと、不具合が生じる可能性があります。  
※作者が動作確認をした環境は、[.python-version](./.python-version)ファイルを参照。

（参考）  
[WindowsにシンプルなPython開発環境を構築する。 | U-MAN Lab.](https://u-man-lab.com/simple-python-dev-environment-on-windows/?utm_source=github&utm_medium=social&utm_campaign=replace_heads_of_audio_paths_in_m3u)


### 2. スクリプトファイルと設定ファイルの格納

音楽ファイルの移行先のPC上で、適切な作業フォルダに、本リポジトリのスクリプトファイルと設定ファイル、および`requirements.txt`ファイルをダウンロードして格納します。
* スクリプトファイル: [replace_heads_of_audio_paths_in_m3u.py](./replace_heads_of_audio_paths_in_m3u.py)
* 設定ファイル: [replace_heads_of_audio_paths_in_m3u.yaml](./replace_heads_of_audio_paths_in_m3u.yaml)
* `requirements.txt`ファイル: [requirements.txt](./requirements.txt)

### 3. 必要パッケージのインストール

本リポジトリのスクリプトの実行に必要なPythonパッケージをインストールします。  
本リポジトリのスクリプトが動作確認されている未満のバージョンだと、不具合が生じる可能性があります。

```bash
pip install -r ./requirements.txt
```

### 4. 設定ファイルを編集

設定ファイル`replace_heads_of_audio_paths_in_m3u.yaml`を開き、ファイル内のコメントに従って、各フィールドの値を編集してください。

### 5. スクリプトの実行

設定ファイルのパスを引数に指定して、スクリプトを実行します。

```bash
python ./replace_heads_of_audio_paths_in_m3u.py ./replace_heads_of_audio_paths_in_m3u.yaml
```

---

## ✅ 正常な動作結果の例

- 指定された入力フォルダ配下のM3Uファイル（拡張子`.m3u`または`.m3u8`）が再帰的に探索されます。
- 指定された出力フォルダに、変換後のM3Uファイルが元のフォルダ構造を維持したまま作成されます。
- 各M3Uファイル内の音楽ファイルのパスは、移行先のPC上に実在するファイルパスに置換されます。
- 正常に動作した場合の出力例は以下です。
  ```bash
  ---
  処理中 [1/178] <- "/original/path/m3u_folder/アニメ.m3u"
  処理完了 [1/178] -> "/new/path/converted_m3u_folder/アニメ.m3u"
  ---
  処理中 [2/178] <- "/original/path/m3u_folder/JUDY AND MARY.m3u"
  処理完了 [2/178] -> "/new/path/converted_m3u_folder/JUDY AND MARY.m3u"
  ...
  ```

---

## ⚠️ 主なエラー・例外

発生しうるエラーの一部を以下に示します。詳しくはスクリプトのdocstringを参照してください。

### 設定ミスによるエラー

設定ファイルに不備がある場合。不備の詳細は、その上部に記載されているトレースバックの内容を参照してください。

```bash
ValueError: 設定ファイルの読み取りに失敗しました。
```

### FileNotFoundError

M3Uファイル内の楽曲ファイルパスが置換後に実在しない場合。

```bash
---
処理中 [2/178] <- "/original/path/m3u_folder/JUDY AND MARY.m3u"
FileNotFoundError: M3Uファイル内の楽曲ファイルパス"/Users/USERNAME/Music/iTunes/iTunes Media/Music/JUDY AND MARY/The Great Escape -COMPLETE BEST-/1-04 mottö.m4a"の現在の場所を確認できません。
処理失敗(変換) [2/178] FileNotFoundError: 1つ以上の楽曲ファイルの特定ができなかったため、M3Uファイルの置換に失敗しました。: "/original/path/m3u_folder/JUDY AND MARY.m3u"
...
```

---

## 📄 ライセンス

このリポジトリはMITライセンスの下で提供されています。詳細は[LICENSE](./LICENSE)ファイルを参照してください。

---

## 👤 作者

U-MAN Lab. ([https://u-man-lab.com/](https://u-man-lab.com?utm_source=github&utm_medium=social&utm_campaign=replace_heads_of_audio_paths_in_m3u))
