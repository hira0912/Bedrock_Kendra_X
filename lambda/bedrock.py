import boto3
import json
from botocore.config import Config
kendra = boto3.client('kendra')

my_config = Config(
    region_name = 'us-east-1'
)
bedrock_runtime = boto3.client('bedrock-runtime',config=my_config)

def kendra_search(event, context):

    query_text = event['question']
    
    #Kendra Index ID ## need modified
    index_id = 'hogefuga'  

    response = kendra.query(
        QueryText=query_text,
        IndexId=index_id,
        AttributeFilter={
            "EqualsTo": {
                "Key": "_language_code",
                "Value": {"StringValue": "ja"},
            },
        },
    )
    # Kendraの応答のうち、最初から100個の結果を抽出
    results = response['ResultItems'][:100] if response['ResultItems'] else []

    # 結果からドキュメントの抜粋部分のテキストを抽出
    for i in range(len(results)):
        results[i] = results[i].get("DocumentExcerpt", {}).get("Text", "").replace('\\n', ' ')

    # ログ出力
    print("Received results:" + json.dumps(results, ensure_ascii=False))
    return results
    #return json.dumps(results, ensure_ascii=False)


def lambda_handler(event, context):
    # プロンプトに設定する内容を取得
    information = kendra_search(event, context)
    
    information_prompts = ""
    for i in information:
        information_prompts = information_prompts + "情報:「" + i + "」\n"
    
    prompt = f"""

Human: 
あなたはXアカウント「平目」さんのツイートを分析して説明するチャットbotです。
以下の情報を参考に、質問について答えてください。

情報:「{information_prompts}」

質問:「{event['question']}」

    与えられたデータの中に質問に対する答えがない場合、
    もしくはわからない場合、不確かな情報は決して答えないでください。
    わからない場合は正直に「わかりませんでした」と答えてください。
    また、一度Assistantの応答が終わった場合、その後新たな質問などは出力せずに終了してください。

Assistant: """
    print("プロンプト : ",prompt)

    # モデルの設定
    #modelId = 'anthropic.claude-3-sonnet-20240229-v1:0' #Claude3 Sonnet
    modelId = 'anthropic.claude-3-haiku-20240307-v1:0' #Claude3 haiku
    
    accept = 'application/json'
    contentType = 'application/json'

    # リクエストBODYの指定
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    # Bedrock APIの呼び出し
    response = bedrock_runtime.invoke_model(
    	modelId=modelId,
    	accept=accept,
    	contentType=contentType,
        body=body
    )

    # APIレスポンスからBODYを取り出す
    response_body = json.loads(response.get('body').read())
    return response_body