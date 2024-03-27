import boto3
import json
import os
from botocore.config import Config

def kendra_search(index_id, query_text):
    kendra = boto3.client('kendra')

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
    results = response['ResultItems'][:100] if response['ResultItems'] else []

    for i in range(len(results)):
        results[i] = results[i].get("DocumentExcerpt", {}).get("Text", "").replace('\\n', ' ')

    print("Received results:" + json.dumps(results, ensure_ascii=False))
    return results

def lambda_handler(event, context):
    kendra = boto3.client('kendra')
    my_config = Config(region_name='us-east-1')
    bedrock_runtime = boto3.client('bedrock-runtime', config=my_config)

    index_id = os.environ.get('KENDRA_INDEX_ID')
    information = kendra_search(index_id, event['question'])

    information_prompts = ""
    for i in information:
        information_prompts = information_prompts + "情報:「" + i + "」\n"

    prompt = f"""
H: 
あなたはXアカウント「平目」さんのツイートを分析して説明するチャットbotです。
以下の情報を参考に、質問について答えてください。

情報:「{information_prompts}」

質問:「{event['question']}」

    与えられたデータの中に質問に対する答えがない場合、
    もしくはわからない場合、不確かな情報は決して答えないでください。
    わからない場合は正直に「わかりませんでした」と答えてください。
    また、一度Assistantの応答が終わった場合、その後新たな質問などは出力せずに終了してください。

A: """
    print("プロンプト : ", prompt)

    modelId = 'anthropic.claude-3-haiku-20240307-v1:0'
    accept = 'application/json'
    contentType = 'application/json'

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

    response = bedrock_runtime.invoke_model(
        modelId=modelId,
        accept=accept,
        contentType=contentType,
        body=body
    )

    response_body = json.loads(response.get('body').read())
    return response_body