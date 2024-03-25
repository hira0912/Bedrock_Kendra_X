import json
import os
import re
from datetime import datetime

# 元のデータファイルのパス
input_file = 'data/tweets.json'

# 実行ファイルの絶対パス
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 元のデータファイルの絶対パス
input_file_path = os.path.join(script_dir, input_file)

# 出力ディレクトリ
output_dir = os.path.join(script_dir, 'data/data_split')

# 出力ディレクトリが存在しない場合は作成する
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 元のデータを読み込む
with open(input_file_path, 'r', encoding='utf-8') as f:
    tweets = json.load(f)

# リンクを検出する正規表現
link_pattern = re.compile(r'https?://\S+')

# 各ツイートを処理する
for tweet_data in tweets:
    tweet = tweet_data['tweet']
    entities = tweet['entities']
    user_mentions = entities['user_mentions']

    # user_mentionsが空でない場合は処理を除外
    if user_mentions:
        continue

    full_text = tweet['full_text']
    created_at = tweet['created_at']

    # full_textにリンクがある場合は処理を除外
    if link_pattern.search(full_text):
        continue

    try:
        # full_textをShift_JISに変換
        full_text_sjis = full_text.encode('shift_jis')
    except UnicodeEncodeError:
        # 変換できない文字が含まれる場合は処理を除外
        continue

    # 日付をYYYYMMDDhhmmss形式に変換
    date_str = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y').strftime('%Y%m%d%H%M%S')

    # 出力データを作成
    output_data = {
        'full_text': full_text_sjis.decode('shift_jis'),
        'date': date_str
    }

    # 出力ファイル名を作成
    output_filename = f'tweet_{date_str}.json'
    output_path = os.path.join(output_dir, output_filename)

    # 出力ファイルを書き込む
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

print('処理が完了しました。')