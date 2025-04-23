# ui.py
import streamlit as st
import pandas as pd
import time
from database import save_to_db, get_chat_history, get_db_count, clear_db
from llm import generate_response
from data import create_sample_evaluation_data
from metrics import get_metrics_descriptions

# カスタムCSSを適用
def apply_custom_css():
    """かわいいテーマのカスタムCSSを適用する"""
    st.markdown("""
    <style>
    /* 全体的なカラーテーマ - パステルカラー */
    :root {
        --main-color: #FFB6C1;  /* ライトピンク */
        --accent-color: #B0E0E6;  /* パウダーブルー */
        --background-color: #FFF5EE;  /* 明るいクリーム */
        --text-color: #5F4B8B;  /* 柔らかい紫 */
        --success-color: #98FB98;  /* ペールグリーン */
    }
    
    /* 背景色の設定 */
    .main {
        background-color: var(--background-color);
        border-radius: 20px;
        padding: 20px;
    }
    
    /* ヘッダーのスタイル */
    h1, h2, h3 {
        color: var(--text-color);
        font-family: 'Comic Sans MS', cursive, sans-serif;
        border-bottom: 3px dotted var(--main-color);
        padding-bottom: 10px;
    }
    
    /* ボタンのスタイル */
    .stButton > button {
        background-color: var(--main-color);
        color: white;
        border-radius: 15px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        transition: transform 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        background-color: var(--accent-color);
    }
    
    /* テキストエリアのスタイル */
    .stTextArea textarea {
        border-radius: 15px;
        border: 2px solid var(--main-color);
        padding: 10px;
        font-size: 16px;
    }
    
    /* エクスパンダーのスタイル */
    .streamlit-expanderHeader {
        background-color: var(--accent-color);
        color: var(--text-color);
        border-radius: 10px;
        padding: 10px;
        font-family: 'Comic Sans MS', cursive, sans-serif;
    }
    
    /* メトリックのスタイル */
    .stMetric {
        background-color: rgba(255, 182, 193, 0.2);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* 通知のスタイル */
    .stAlert {
        border-radius: 15px;
        border: 2px dashed var(--accent-color);
    }
    
    /* 成功メッセージのスタイル */
    .element-container div[data-testid="stAlert"][data-baseweb="notification"] {
        background-color: var(--success-color);
        border-radius: 15px;
        border: 2px dashed var(--main-color);
    }
    </style>
    """, unsafe_allow_html=True)

# --- チャットページのUI ---
def display_chat_page(pipe):
    """チャットページのUIを表示する"""
    # カスタムCSSを適用
    apply_custom_css()
    
    # 装飾的なヘッダー
    st.markdown("## 🌸 チャットボット 🌸")
    st.markdown("### ✨ 質問を入力してください ✨")
    
    user_question = st.text_area("質問", key="question_input", height=100, 
                            value=st.session_state.get("current_question", ""), 
                            placeholder="ここに質問を入力してね♪",
                            label_visibility="collapsed")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        submit_button = st.button("🚀 質問を送信 🚀")

    # セッション状態の初期化（安全のため）
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    if "current_answer" not in st.session_state:
        st.session_state.current_answer = ""
    if "response_time" not in st.session_state:
        st.session_state.response_time = 0.0
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = False

    # 質問が送信された場合
    if submit_button and user_question:
        st.session_state.current_question = user_question
        st.session_state.current_answer = "" # 回答をリセット
        st.session_state.feedback_given = False # フィードバック状態もリセット

        with st.spinner("✨ モデルが魔法をかけています... ✨"):
            answer, response_time = generate_response(pipe, user_question)
            st.session_state.current_answer = answer
            st.session_state.response_time = response_time
            # ここでrerunすると回答とフィードバックが一度に表示される
            st.rerun()

    # 回答が表示されるべきか判断 (質問があり、回答が生成済みで、まだフィードバックされていない)
    if st.session_state.current_question and st.session_state.current_answer:
        st.markdown("### 🎀 回答: 🎀")
        
        # かわいい吹き出しスタイルで回答を表示
        st.markdown(f"""
        <div style="background-color: #E6F7FF; padding: 20px; border-radius: 20px; border: 2px solid #B0E0E6; position: relative;">
            <div style="position: absolute; top: -15px; left: 20px; background-color: #FFB6C1; padding: 5px 15px; border-radius: 15px; color: white; font-weight: bold;">
                ✨ Gemmaより ✨
            </div>
            <p style="margin-top: 10px; font-size: 16px; color: #5F4B8B;">{st.session_state.current_answer}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align: right; margin-top: 5px; color: #888; font-size: 14px;">
            🕒 応答時間: {st.session_state.response_time:.2f}秒
        </div>
        """, unsafe_allow_html=True)

        # フィードバックフォームを表示 (まだフィードバックされていない場合)
        if not st.session_state.feedback_given:
            display_feedback_form()
        else:
            # フィードバック送信済みの場合、次の質問を促すか、リセットする
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🌟 次の質問へ 🌟"):
                    # 状態をリセット
                    st.session_state.current_question = ""
                    st.session_state.current_answer = ""
                    st.session_state.response_time = 0.0
                    st.session_state.feedback_given = False
                    st.rerun() # 画面をクリア


def display_feedback_form():
    """フィードバック入力フォームを表示する"""
    st.markdown("### 💭 あなたの感想を教えてください 💭")
    
    with st.form("feedback_form"):
        # かわいいフィードバックオプション
        feedback_options = ["😊 正確", "🤔 部分的に正確", "😢 不正確"]
        # より目立つラジオボタン
        st.markdown("""
        <p style="font-size: 18px; font-weight: bold; color: #5F4B8B;">回答の評価:</p>
        """, unsafe_allow_html=True)
        feedback = st.radio("回答の評価", feedback_options, key="feedback_radio", 
                           label_visibility='collapsed', horizontal=True)
        
        correct_answer = st.text_area("より正確な回答（任意）", key="correct_answer_input", 
                                     height=100, placeholder="もっと良い回答があれば教えてね♪")
        
        feedback_comment = st.text_area("コメント（任意）", key="feedback_comment_input", 
                                       height=100, placeholder="感想やアドバイスをどうぞ✨")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("💌 フィードバックを送信 💌")
        
        if submitted:
            # フィードバックをデータベースに保存
            is_correct = 1.0 if "正確" in feedback else (0.5 if "部分的に正確" in feedback else 0.0)
            # コメントがない場合でも '正確' などの評価はfeedbackに含まれるようにする
            combined_feedback = f"{feedback.strip('😊🤔😢 ')}"
            if feedback_comment:
                combined_feedback += f": {feedback_comment}"

            save_to_db(
                st.session_state.current_question,
                st.session_state.current_answer,
                combined_feedback,
                correct_answer,
                is_correct,
                st.session_state.response_time
            )
            st.session_state.feedback_given = True
            
            # かわいい成功メッセージ
            st.success("🎉 ありがとう！フィードバックが保存されました！ 🎉")
            # フォーム送信後に状態をリセットしない方が、ユーザーは結果を確認しやすいかも
            # 必要ならここでリセットして st.rerun()
            st.rerun() # フィードバックフォームを消すために再実行

# --- 履歴閲覧ページのUI ---
def display_history_page():
    """履歴閲覧ページのUIを表示する"""
    # カスタムCSSを適用
    apply_custom_css()
    
    st.markdown("## 📚 チャット履歴と評価指標 📊")
    history_df = get_chat_history()

    if history_df.empty:
        st.markdown("""
        <div style="text-align: center; padding: 30px; background-color: #FFF5EE; border-radius: 15px; border: 2px dashed #FFB6C1;">
            <p style="font-size: 18px; color: #5F4B8B;">💫 まだチャット履歴がありません 💫</p>
            <p style="font-size: 14px; color: #888;">最初の質問をしてみましょう！</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # かわいいタブデザイン
    tab1, tab2 = st.tabs(["📝 履歴閲覧", "📊 評価指標分析"])

    with tab1:
        display_history_list(history_df)

    with tab2:
        display_metrics_analysis(history_df)

def display_history_list(history_df):
    """履歴リストを表示する"""
    st.markdown("#### 🔍 履歴リスト")
    
    # かわいいフィルターオプション
    filter_options = {
        "✨ すべて表示": None,
        "👍 正確なもののみ": 1.0,
        "👌 部分的に正確なもののみ": 0.5,
        "👎 不正確なもののみ": 0.0
    }
    
    # かわいいラジオボタン
    display_option = st.radio(
        "表示フィルタ",
        options=filter_options.keys(),
        horizontal=True,
        label_visibility="collapsed" # ラベル非表示
    )

    filter_value = filter_options[display_option]
    if filter_value is not None:
        # is_correctがNaNの場合を考慮
        filtered_df = history_df[history_df["is_correct"].notna() & (history_df["is_correct"] == filter_value)]
    else:
        filtered_df = history_df

    if filtered_df.empty:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: #FFF5EE; border-radius: 15px; border: 2px dashed #FFB6C1;">
            <p style="font-size: 16px; color: #5F4B8B;">🔍 選択した条件に一致する履歴はありません 🔍</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ページネーション
    items_per_page = 5
    total_items = len(filtered_df)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # かわいいページネーション
    st.markdown("<p style='text-align: center; color: #5F4B8B;'>📄 ページ選択</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        current_page = st.number_input('ページ', min_value=1, max_value=total_pages, value=1, step=1, label_visibility="collapsed")

    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_df = filtered_df.iloc[start_idx:end_idx]


    for i, row in paginated_df.iterrows():
        # かわいいエクスパンダー
        with st.expander(f"🗓️ {row['timestamp']} - 💬 {row['question'][:50] if row['question'] else 'N/A'}..."):
            # かわいいQ&A表示
            st.markdown(f"""
            <div style="background-color: #FFF0F5; padding: 15px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #FFB6C1;">
                <p style="font-weight: bold; color: #5F4B8B;">💬 質問:</p>
                <p style="color: #333;">{row['question']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: #E6F7FF; padding: 15px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #B0E0E6;">
                <p style="font-weight: bold; color: #5F4B8B;">🤖 回答:</p>
                <p style="color: #333;">{row['answer']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: #F0FFF0; padding: 15px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #98FB98;">
                <p style="font-weight: bold; color: #5F4B8B;">💭 フィードバック:</p>
                <p style="color: #333;">{row['feedback']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if row['correct_answer']:
                st.markdown(f"""
                <div style="background-color: #FFFACD; padding: 15px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #FFD700;">
                    <p style="font-weight: bold; color: #5F4B8B;">✅ 正確な回答:</p>
                    <p style="color: #333;">{row['correct_answer']}</p>
                </div>
                """, unsafe_allow_html=True)

            # 評価指標の表示
            st.markdown("---")
            cols = st.columns(3)
            # かわいいメトリック表示
            cols[0].markdown(f"""
            <div style="background-color: rgba(255,182,193,0.2); padding: 10px; border-radius: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #888;">正確性スコア</p>
                <p style="margin: 5px 0; font-size: 24px; font-weight: bold; color: #5F4B8B;">{row['is_correct']:.1f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            cols[1].markdown(f"""
            <div style="background-color: rgba(176,224,230,0.2); padding: 10px; border-radius: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #888;">応答時間(秒)</p>
                <p style="margin: 5px 0; font-size: 24px; font-weight: bold; color: #5F4B8B;">{row['response_time']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            cols[2].markdown(f"""
            <div style="background-color: rgba(152,251,152,0.2); padding: 10px; border-radius: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #888;">単語数</p>
                <p style="margin: 5px 0; font-size: 24px; font-weight: bold; color: #5F4B8B;">{row['word_count']}</p>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(3)
            
            # 修正箇所: 条件分岐をf-stringの外に出す
            bleu_display = f"{row['bleu_score']:.4f}" if pd.notna(row['bleu_score']) else "-"
            similarity_display = f"{row['similarity_score']:.4f}" if pd.notna(row['similarity_score']) else "-"
            relevance_display = f"{row['relevance_score']:.4f}" if pd.notna(row['relevance_score']) else "-"
            
            # NaNの場合はハイフン表示（修正済み）
            cols[0].markdown(f"""
            <div style="background-color: rgba(255,250,205,0.2); padding: 10px; border-radius: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #888;">BLEU</p>
                <p style="margin: 5px 0; font-size: 24px; font-weight: bold; color: #5F4B8B;">{bleu_display}</p>
            </div>
            """, unsafe_allow_html=True)
            
            cols[1].markdown(f"""
            <div style="background-color: rgba(230,230,250,0.2); padding: 10px; border-radius: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #888;">類似度</p>
                <p style="margin: 5px 0; font-size: 24px; font-weight: bold; color: #5F4B8B;">{similarity_display}</p>
            </div>
            """, unsafe_allow_html=True)
            
            cols[2].markdown(f"""
            <div style="background-color: rgba(255,228,225,0.2); padding: 10px; border-radius: 10px; text-align: center;">
                <p style="margin: 0; font-size: 14px; color: #888;">関連性</p>
                <p style="margin: 5px 0; font-size: 24px; font-weight: bold; color: #5F4B8B;">{relevance_display}</p>
            </div>
            """, unsafe_allow_html=True)

    # かわいいページ情報
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px; color: #888; font-size: 14px;">
        🌸 {total_items} 件中 {start_idx+1} - {min(end_idx, total_items)} 件を表示中 🌸
    </div>
    """, unsafe_allow_html=True)


def display_metrics_analysis(history_df):
    """評価指標の分析結果を表示する"""
    st.markdown("#### 📊 評価指標の分析")

    # is_correct が NaN のレコードを除外して分析
    analysis_df = history_df.dropna(subset=['is_correct'])
    if analysis_df.empty:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: #FFF5EE; border-radius: 15px; border: 2px dashed #FFB6C1;">
            <p style="font-size: 16px; color: #5F4B8B;">📊 分析可能な評価データがありません 📊</p>
        </div>
        """, unsafe_allow_html=True)
        return

    accuracy_labels = {1.0: '😊 正確', 0.5: '🤔 部分的に正確', 0.0: '😢 不正確'}
    analysis_df['正確性'] = analysis_df['is_correct'].map(accuracy_labels)

    # 正確性の分布
    st.markdown("##### 🍩 正確性の分布")
    accuracy_counts = analysis_df['正確性'].value_counts()
    if not accuracy_counts.empty:
        st.bar_chart(accuracy_counts)
    else:
        st.info("正確性データがありません。")

    # 応答時間と他の指標の関係
    st.markdown("##### 📈 応答時間とその他の指標の関係")
    metric_options = ["bleu_score", "similarity_score", "relevance_score", "word_count"]
    # 利用可能な指標のみ選択肢に含める
    valid_metric_options = [m for m in metric_options if m in analysis_df.columns and analysis_df[m].notna().any()]

    if valid_metric_options:
        # かわいいセレクトボックス
        st.markdown("<p style='color: #5F4B8B; font-weight: bold;'>🔍 比較する評価指標を選択</p>", unsafe_allow_html=True)
        metric_option = st.selectbox(
            "比較する評価指標を選択",
            valid_metric_options,
            key="metric_select",
            label_visibility="collapsed"
        )

        chart_data = analysis_df[['response_time', metric_option, '正確性']].dropna() # NaNを除外
        if not chart_data.empty:
             st.scatter_chart(
                chart_data,
                x='response_time',
                y=metric_option,
                color='正確性',
            )
        else:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background-color: #FFF5EE; border-radius: 15px; border: 2px dashed #FFB6C1;">
                <p style="font-size: 14px; color: #5F4B8B;">📊 選択された指標 ({metric_option}) と応答時間の有効なデータがありません 📊</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background-color: #FFF5EE; border-radius: 15px; border: 2px dashed #FFB6C1;">
            <p style="font-size: 14px; color: #5F4B8B;">📊 応答時間と比較できる指標データがありません 📊</p>
        </div>
        """, unsafe_allow_html=True)


    # 全体の評価指標の統計
    st.markdown("##### 📋 評価指標の統計")
    stats_cols = ['response_time', 'bleu_score', 'similarity_score', 'word_count', 'relevance_score']
    valid_stats_cols = [c for c in stats_cols if c in analysis_df.columns and analysis_df[c].notna().any()]
    if valid_stats_cols:
        metrics_stats = analysis_df[valid_stats_cols].describe()
        st.dataframe(metrics_stats, use_container_width=True)
    else:
        st.info("統計情報を計算できる評価指標データがありません。")

    # 正確性レベル別の平均スコア
    st.markdown("##### 📌 正確性レベル別の平均スコア")
    if valid_stats_cols and '正確性' in analysis_df.columns:
        try:
            accuracy_groups = analysis_df.groupby('正確性')[valid_stats_cols].mean()
            st.dataframe(accuracy_groups, use_container_width=True)
        except Exception as e:
            st.warning(f"正確性別スコアの集計中にエラーが発生しました: {e}")
    else:
         st.info("正確性レベル別の平均スコアを計算できるデータがありません。")


    # カスタム評価指標：効率性スコア
    st.markdown("##### ⚡ 効率性スコア (正確性 / (応答時間 + 0.1))")
    if 'response_time' in analysis_df.columns and analysis_df['response_time'].notna().any():
        # ゼロ除算を避けるために0.1を追加
        analysis_df['efficiency_score'] = analysis_df['is_correct'] / (analysis_df['response_time'].fillna(0) + 0.1)
        # IDカラムが存在するか確認
        if 'id' in analysis_df.columns:
            # 上位10件を表示
            top_efficiency = analysis_df.sort_values('efficiency_score', ascending=False).head(10)
            # id をインデックスにする前に存在確認
            if not top_efficiency.empty:
                st.bar_chart(top_efficiency.set_index('id')['efficiency_score'])
            else:
                st.info("効率性スコアデータがありません。")
        else:
            # IDがない場合は単純にスコアを表示
             st.bar_chart(analysis_df.sort_values('efficiency_score', ascending=False).head(10)['efficiency_score'])

    else:
        st.info("効率性スコアを計算するための応答時間データがありません。")


# --- サンプルデータ管理ページのUI ---
def display_data_page():
    """サンプルデータ管理ページのUIを表示する"""
    # カスタムCSSを適用
    apply_custom_css()
    
    st.markdown("## 🧸 サンプル評価データの管理 🧸")
    count = get_db_count()
    st.markdown(f"""
    <div style="text-align: center; padding: 15px; background-color: #FFF5EE; border-radius: 15px; margin-bottom: 20px;">
        <p style="font-size: 18px; color: #5F4B8B;">現在のデータベースには <span style="font-weight: bold; color: #FFB6C1;">{count}</span> 件のレコードがあります 📝</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ サンプルデータを追加 ✨", key="create_samples"):
            with st.spinner("🧚‍♀️ サンプルデータを生成中..."):
                create_sample_evaluation_data()
                st.rerun() # 件数表示を更新

    with col2:
        # 確認ステップ付きのクリアボタン
        if st.button("🧹 データベースをクリア 🧹", key="clear_db_button"):
            with st.spinner("🧚‍♂️ データベースをクリア中..."):
                if clear_db(): # clear_db内で確認と実行を行う
                    st.rerun() # クリア後に件数表示を更新

    # 評価指標に関する解説
    st.markdown("## 📖 評価指標の説明 📖")
    metrics_info = get_metrics_descriptions()
    
    # かわいい説明カード形式で表示
    for metric, description in metrics_info.items():
        with st.expander(f"🌟 {metric} 🌟"):
            st.markdown(f"""
            <div style="background-color: #FAFAFA; padding: 15px; border-radius: 15px; border-left: 5px solid #FFB6C1;">
                <p style="color: #5F4B8B;">{description}</p>
            </div>
            """, unsafe_allow_html=True)