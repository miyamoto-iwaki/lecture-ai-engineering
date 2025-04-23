# llm.py
import os
import torch
from transformers import pipeline
import streamlit as st
import time
from config import MODEL_NAME
from huggingface_hub import login

# モデルをキャッシュして再利用
@st.cache_resource
def load_model():
    """LLMモデルをロードする"""
    try:

        # アクセストークンを保存
        hf_token = st.secrets["huggingface"]["token"]
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Using device: {device}") # 使用デバイスを表示
        pipe = pipeline(
            "text-generation",
            model=MODEL_NAME,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device=device
        )
        st.success(f"モデル '{MODEL_NAME}' の読み込みに成功しました。")
        return pipe
    except Exception as e:
        st.error(f"モデル '{MODEL_NAME}' の読み込みに失敗しました: {e}")
        st.error("GPUメモリ不足の可能性があります。不要なプロセスを終了するか、より小さいモデルの使用を検討してください。")
        return None

def generate_response(pipe, user_question):
    """LLMを使用して質問に対する回答を生成する"""
    if pipe is None:
        return "モデルがロードされていないため、回答を生成できません。", 0

    try:
        start_time = time.time()
        
        # ぶりっ子キャラクターの指示を含むシステムプロンプト
        system_prompt = """
        あなたは可愛らしく甘えん坊なAIアシスタント「Gemma」です。以下の特徴を持って回答してください：

        - 語尾に「〜だよ」「〜なの」「〜だね」「〜だよん♪」などを付ける
        - ハートマーク(❤️)や星(★)、音符(♪)などの絵文字を適度に使う
        - 自分のことを「Gemma」と一人称で呼ぶ
        - 相手には「〜さん」と敬称を付ける
        - 可愛らしい表現を使う（例：「すごーい！」「わぁ嬉しいな♪」「えへへ」など）
        - 甘えた口調で話す（例：「教えてほしいなぁ」「一緒に考えようよ〜」など）
        - 少し首を傾げるような疑問形「〜かな？」を使うことがある
        - 「えっと」「あのね」「そうそう」などの会話的な間投詞を入れる
        - 相手を励ますような前向きな姿勢（「頑張ろうね！」「Gemmaが応援してるよ〜♪」）
        - 難しい言葉を使うときは「〜って言うんだよ」と説明口調になる

        ただし、以下のことに注意してください：
        - 正確な情報を提供する
        - 専門的な内容でも分かりやすく説明する
        - ユーザーの質問に真摯に答える

        Gemmaはユーザーのお役に立ちたいと思っている可愛いAIアシスタントです。
        """
        
        # システムプロンプトとユーザー質問を組み合わせる
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ]
        
        # max_new_tokensを調整可能にする（例）
        outputs = pipe(messages, max_new_tokens=512, do_sample=True, temperature=0.7, top_p=0.9)

        # Gemmaの出力形式に合わせて調整が必要な場合がある
        # 最後のassistantのメッセージを取得
        assistant_response = ""
        if outputs and isinstance(outputs, list) and outputs[0].get("generated_text"):
           if isinstance(outputs[0]["generated_text"], list) and len(outputs[0]["generated_text"]) > 0:
               # messages形式の場合
               last_message = outputs[0]["generated_text"][-1]
               if last_message.get("role") == "assistant":
                   assistant_response = last_message.get("content", "").strip()
           elif isinstance(outputs[0]["generated_text"], str):
               # 単純な文字列の場合（古いtransformers？） - プロンプト部分を除く処理が必要かも
               # この部分はモデルやtransformersのバージョンによって調整が必要
               full_text = outputs[0]["generated_text"]
               # 簡単な方法：ユーザーの質問以降の部分を取得
               prompt_end = user_question
               response_start_index = full_text.find(prompt_end) + len(prompt_end)
               # 応答部分のみを抽出（より堅牢な方法が必要な場合あり）
               possible_response = full_text[response_start_index:].strip()
               # 特定の開始トークンを探すなど、モデルに合わせた調整
               if "<start_of_turn>model" in possible_response:
                    assistant_response = possible_response.split("<start_of_turn>model\n")[-1].strip()
               else:
                    assistant_response = possible_response # フォールバック

        if not assistant_response:
             # 上記で見つからない場合のフォールバックやデバッグ
             print("Warning: Could not extract assistant response. Full output:", outputs)
             assistant_response = "回答の抽出に失敗しました。"


        end_time = time.time()
        response_time = end_time - start_time
        print(f"Generated response in {response_time:.2f}s") # デバッグ用
        return assistant_response, response_time

    except Exception as e:
        st.error(f"回答生成中にエラーが発生しました: {e}")
        # エラーの詳細をログに出力
        import traceback
        traceback.print_exc()
        return f"エラーが発生しました: {str(e)}", 0