import json
import math
from collections import Counter
import altair as alt
import streamlit as st
from typing import Any, Dict, List
from urllib.parse import urlparse
from services.storage_service import get_storage_provider
from core.models import SalesType
try:
    from streamlit_sortables import sort_items
    SORTABLES_AVAILABLE = True
except ImportError:
    SORTABLES_AVAILABLE = False
    def sort_items(items, key=None):
        """Fallback function when streamlit-sortables is not available"""
        return items
from translations import t


def show_history_page() -> None:
    st.header(t("history_header"))
    st.write(t("history_desc"))


    provider = get_storage_provider()
    all_sessions: List[Dict[str, Any]] = provider.list_sessions()

    # チーム別集計
    team_counts = Counter(s.get("team_id", "unknown") for s in all_sessions)
    if team_counts:
        st.subheader("チーム別セッション数")
        agg_data = [{"team_id": k, "count": v} for k, v in team_counts.items()]
        st.table(agg_data)
        chart = alt.Chart(agg_data).mark_bar().encode(x="team_id:N", y="count:Q")
        st.altair_chart(chart, use_container_width=True)

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        json_data = provider.export_sessions("json", all_sessions)
        st.download_button(
            t("history_export_json"),
            data=json_data,
            file_name="sessions.json",
            mime="application/json",
            key="history_dl_json",
        )
    with col_exp2:
        csv_data = provider.export_sessions("csv", all_sessions)
        st.download_button(
            t("history_export_csv"),
            data=csv_data,
            file_name="sessions.csv",
            mime="text/csv",
            key="history_dl_csv",
        )

    # フィルタUI
    with st.expander("フィルタ", expanded=True):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        with col1:
            type_filter = st.selectbox(
                "種類",
                options=["すべて", "pre_advice", "post_review", "icebreaker"],
                index=0,
                help="表示するセッションの種類を選択",
                key="history_type_filter",
            )
        with col2:
            user_ids = sorted({s.get("user_id", "unknown") for s in all_sessions})
            user_filter = st.selectbox(
                "ユーザー",
                options=["すべて"] + user_ids,
                index=0,
                key="history_user_filter",
            )
        with col3:
            team_ids = sorted({s.get("team_id", "unknown") for s in all_sessions})
            team_filter = st.selectbox(
                "チーム",
                options=["すべて"] + team_ids,
                index=0,
                key="history_team_filter",
            )
        with col4:
            query = st.text_input("キーワード検索", placeholder="業界名・目的など", key="history_query")

        s1, s2, s3 = st.columns([1, 1, 1])
        with s1:
            sort_mode = st.selectbox(
                "並び替え",
                options=["最新順 (ピン優先)", "古い順 (ピン優先)", "タイプ順 (ピン優先)", "ピンのみ"],
                index=0,
                key="history_sort_mode",
            )
        with s2:
            default_size = st.session_state.get("history_page_size", 10)
            page_size = st.selectbox("表示件数", options=[5, 10, 20, 50], index=[5, 10, 20, 50].index(default_size), key="history_page_size")
        with s3:
            # 既存タグ/ドメインを収集してサジェスト
            all_tags: set[str] = set()
            all_domains: set[str] = set()
            for s in all_sessions:
                for t in (s.get("tags", []) or []):
                    if isinstance(t, str) and t.strip():
                        all_tags.add(t.strip())
                data_blob = s.get("data", {}) or {}
                if data_blob.get("type") == "pre_advice":
                    ev = ((data_blob.get("output", {}) or {}).get("advice", {}) or {}).get("evidence_urls", [])
                else:
                    ev = (data_blob.get("output", {}) or {}).get("evidence_urls", [])
                for u in ev or []:
                    try:
                        host = urlparse(u).netloc
                        if host:
                            all_domains.add(host)
                    except Exception:
                        pass
            tag_filter_multi = st.multiselect(
                "タグで絞り込み",
                options=sorted(all_tags),
                default=[],
                key="history_tag_filter_multi",
            )
            domain_filter_multi = st.multiselect(
                "出典ドメインで絞り込み",
                options=sorted(all_domains),
                default=[],
                key="history_domain_filter_multi",
            )

    sessions: List[Dict[str, Any]] = all_sessions


    # フィルタ適用
    def match(session: Dict[str, Any]) -> bool:
        if type_filter != "すべて" and session["data"].get("type") != type_filter:
            return False
        if user_filter != "すべて" and session.get("user_id", "unknown") != user_filter:
            return False
        if team_filter != "すべて" and session.get("team_id", "unknown") != team_filter:
            return False
        if query:
            blob = json.dumps(session["data"], ensure_ascii=False)
            return query in blob
        # タグフィルタ（AND）
        if st.session_state.get("history_tag_filter_multi"):
            tags = session.get("tags", []) or []
            for t in st.session_state["history_tag_filter_multi"]:
                if t not in tags:
                    return False
        # 出典ドメインフィルタ（OR）
        if st.session_state.get("history_domain_filter_multi"):
            data_blob = session.get("data", {}) or {}
            if data_blob.get("type") == "pre_advice":
                ev = ((data_blob.get("output", {}) or {}).get("advice", {}) or {}).get("evidence_urls", [])
            else:
                ev = (data_blob.get("output", {}) or {}).get("evidence_urls", [])
            session_hosts = set()
            for u in ev or []:
                try:
                    h = urlparse(u).netloc
                    if h:
                        session_hosts.add(h)
                except Exception:
                    pass
            if not session_hosts.intersection(set(st.session_state.get("history_domain_filter_multi", []))):
                return False
        
        return True

    filtered = [s for s in sessions if match(s)]

    # 集計ダッシュボード
    total_count = len(filtered)
    success_count = len([s for s in filtered if s.get("success", True)])
    success_rate = (success_count / total_count * 100) if total_count else 0.0
    d1, d2 = st.columns(2)
    with d1:
        st.metric("件数", total_count)
    with d2:
        st.metric("成功率", f"{success_rate:.1f}%")

    # 並び替え
    def sort_key_latest(x):
        return (0 if x.get("pinned", False) else 1, x.get("created_at", ""))

    def sort_key_oldest(x):
        return (0 if x.get("pinned", False) else 1, x.get("created_at", ""))

    def sort_key_type(x):
        return (0 if x.get("pinned", False) else 1, x.get("data", {}).get("type", ""), x.get("created_at", ""))

    if sort_mode == "最新順 (ピン優先)":
        sorted_list = sorted(filtered, key=sort_key_latest, reverse=True)
    elif sort_mode == "古い順 (ピン優先)":
        sorted_list = sorted(filtered, key=sort_key_oldest, reverse=False)
    elif sort_mode == "タイプ順 (ピン優先)":
        sorted_list = sorted(filtered, key=sort_key_type, reverse=False)
    elif sort_mode == "ピンのみ":
        sorted_list = sorted([s for s in filtered if s.get("pinned", False)], key=sort_key_latest, reverse=True)
    else:
        sorted_list = filtered

    # ページネーション
    total = len(sorted_list)
    page_size_val = st.session_state.get("history_page_size", 10)
    total_pages = max(1, math.ceil(total / page_size_val))
    current_page = st.session_state.get("history_page", 1)
    if current_page > total_pages:
        current_page = total_pages
        st.session_state["history_page"] = current_page

    def pager(location_key: str):
        left, mid, right = st.columns([1, 2, 1])
        with left:
            if st.button("⬅️ 前へ", key=f"hist_prev_{location_key}"):
                if st.session_state.get("history_page", 1) > 1:
                    st.session_state["history_page"] -= 1
                    st.experimental_rerun()
        with mid:
            st.markdown(f"ページ {current_page}/{total_pages}  |  全{total}件")
        with right:
            if st.button("次へ ➡️", key=f"hist_next_{location_key}"):
                if st.session_state.get("history_page", 1) < total_pages:
                    st.session_state["history_page"] += 1
                    st.experimental_rerun()

    if total == 0:
        st.info("保存されたセッションが見つかりません。事前アドバイスや商談後分析の実行後に保存してください。")
        return

    # ページ範囲を先に計算
    start = (current_page - 1) * page_size_val
    end = start + page_size_val
    page_items = sorted_list[start:end]

    # 選択状態の初期化（複数選択用）
    if "history_selected_ids" not in st.session_state:
        st.session_state["history_selected_ids"] = []

    selected_ids: list[str] = list(st.session_state.get("history_selected_ids", []))

    # バッチ操作バー（上部）
    top_c1, top_c2, top_c3, top_c4, top_c5, top_c6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 2])
    with top_c1:
        st.metric("選択中", f"{len(selected_ids)} 件")
    with top_c2:
        if st.button("このページを全選択", key="sel_all_top"):
            for it in sorted_list[start:end]:
                sid = it.get("session_id")
                st.session_state[f"sel_{sid}"] = True
                if sid not in selected_ids:
                    selected_ids.append(sid)
            st.session_state["history_selected_ids"] = selected_ids
            st.experimental_rerun()
    with top_c3:
        if st.button("選択解除", key="clear_sel_top"):
            for it in sorted_list[start:end]:
                sid = it.get("session_id")
                st.session_state[f"sel_{sid}"] = False
            st.session_state["history_selected_ids"] = [sid for sid in selected_ids if sid not in [it.get("session_id") for it in sorted_list[start:end]]]
            st.experimental_rerun()
    with top_c4:
        if st.button("📌 選択をピン留め", key="pin_sel_top") and selected_ids:
            provider = get_storage_provider()
            for sid in selected_ids:
                provider.set_pinned(sid, True)
            st.success("ピン留めを更新しました")
            st.experimental_rerun()
    with top_c5:
        if st.button("📌 選択のピン解除", key="unpin_sel_top") and selected_ids:
            provider = get_storage_provider()
            for sid in selected_ids:
                provider.set_pinned(sid, False)
            st.success("ピン解除を更新しました")
            st.experimental_rerun()
    with top_c6:
        if st.button("🗑️ 選択を削除", key="del_sel_top") and selected_ids:
            st.session_state["batch_confirm_delete"] = True

    pager("top")

    # start/end/page_items は上で計算済み

    # 一覧表示
    for sess in page_items:
        meta = sess
        data = sess.get("data", {})
        sess_id = meta.get("session_id", "-")
        created_at = meta.get("created_at", "-")
        sess_type = data.get("type", "-")
        pinned_flag = bool(meta.get("pinned", False))
        title_prefix = "📌 " if pinned_flag else ""

        sel_col, rest_col = st.columns([0.1, 0.9])
        with sel_col:
            current_checked = st.session_state.get(f"sel_{sess_id}", sess_id in selected_ids)
            checked = st.checkbox("", value=current_checked, key=f"sel_{sess_id}")
            if checked and sess_id not in selected_ids:
                selected_ids.append(sess_id)
            if not checked and sess_id in selected_ids:
                selected_ids.remove(sess_id)
            st.session_state["history_selected_ids"] = selected_ids
        with rest_col:
            with st.expander(f"{title_prefix}[{sess_type}] {created_at}  (Session ID: {sess_id})", expanded=False):
                st.caption("入力/出力の概要を表示します")
                if pinned_flag:
                    st.info("このセッションはピン留めされています")

            # 入力概要
            st.markdown("#### 入力")
            st.code(json.dumps(data.get("input", {}), ensure_ascii=False, indent=2), language="json")

            # 出力概要
            st.markdown("#### 出力")
            st.code(json.dumps(data.get("output", {}), ensure_ascii=False, indent=2), language="json")

            # 根拠リンクのハイライト表示
            try:
                ev_urls: List[str] = []
                if sess_type == "pre_advice":
                    ev_urls = list((data.get("output", {}).get("advice", {}) or {}).get("evidence_urls", []) or [])
                elif sess_type == "post_review":
                    ev_urls = list((data.get("output", {}) or {}).get("evidence_urls", []) or [])
            except Exception:
                ev_urls = []
            if ev_urls:
                st.markdown("#### 🔗 根拠リンク")
                for u in ev_urls:
                    try:
                        host = urlparse(u).netloc
                    except Exception:
                        host = ""
                    host_disp = f"（{host}）" if host else ""
                    st.markdown(f"- [{u}]({u}) {host_disp}")

            # タグ編集（色分け表示 + 既存タグ選択 + 新規追加 + 並び替え）
            st.markdown("#### タグ")
            current_tags = meta.get("tags", []) or []
            _render_tag_badges(current_tags)
            # 並び替えUI
            st.caption("ドラッグ＆ドロップでタグの順序を変更できます")
            items = [
                {
                    "header": t,
                    "body": "",
                    "style": {
                        "background": _color_for_tag(t),
                        "color": "#fff",
                        "padding": "6px 10px",
                        "borderRadius": "12px",
                        "margin": "4px",
                        "display": "inline-block"
                    }
                }
                for t in current_tags
            ]
            # モバイルは縦方向の方が操作しやすい
            direction = "vertical" if st.session_state.get("mobile_ui") else "horizontal"
            reordered = sort_items(items, direction=direction, key=f"sort_tags_{sess_id}")
            reordered_tags = [it["header"] for it in reordered] if reordered else current_tags
            tag_cols = st.columns([2, 1])
            # 最新の全タグ候補を取得
            provider_tags = get_storage_provider()
            sessions_tags: List[Dict[str, Any]] = provider_tags.list_sessions()
            all_tags_now: set[str] = set()
            for s2 in sessions_tags:
                for t2 in (s2.get("tags", []) or []):
                    if isinstance(t2, str) and t2.strip():
                        all_tags_now.add(t2.strip())
            with tag_cols[0]:
                selected_existing = st.multiselect(
                    "既存タグから選択",
                    options=sorted(all_tags_now),
                    default=current_tags,
                    key=f"tag_select_{sess_id}"
                )
            with tag_cols[1]:
                new_tags_str = st.text_input(
                    "新しいタグ（カンマ区切り）",
                    placeholder="例: 顧客A, 優先",
                    key=f"tag_new_{sess_id}"
                )
            if st.button("💾 タグを更新", key=f"save_tags_{sess_id}"):
                provider_save = get_storage_provider()
                new_tags = [t.strip() for t in (new_tags_str or "").split(",") if t.strip()]
                merged = list(dict.fromkeys([*reordered_tags, *selected_existing, *new_tags]))
                ok = provider_save.update_tags(sess_id, merged)
                if ok:
                    st.success("タグを更新しました")
                    st.experimental_rerun()
                else:
                    st.error("タグの更新に失敗しました")

            # アクション
            st.markdown("---")
            a_col1, a_col2, a_col3, a_col4 = st.columns([1,1,1,2])
            with a_col1:
                if st.button("🔁 この内容で再生成", key=f"regen_{sess_id}"):
                    # ページ選択を更新
                    import streamlit as st_local
                    if sess_type == "pre_advice":
                        st_local.session_state.page_select = "事前アドバイス生成"
                        # 入力の再セット
                        _hydrate_pre_advice(data.get("input", {}))
                        st_local.rerun()
                    elif sess_type == "post_review":
                        st_local.session_state.page_select = "商談後ふりかえり解析"
                        _hydrate_post_review(data.get("input", {}))
                        st_local.rerun()
                    elif sess_type == "icebreaker":
                        st_local.session_state.page_select = "アイスブレイク生成"
                        # アイスブレイク入力の再セット
                        _hydrate_icebreaker(data.get("input", {}))
                        st_local.rerun()
            with a_col2:
                if st.button("⚡ 即時再生成", key=f"regen_now_{sess_id}"):
                    import streamlit as st_local
                    if sess_type == "pre_advice":
                        _hydrate_pre_advice(data.get("input", {}))
                        st_local.session_state["pre_advice_autorun"] = True
                        st_local.session_state["autorun_session_id"] = sess_id
                        st_local.session_state.page_select = "事前アドバイス生成"
                        st_local.rerun()
                    elif sess_type == "post_review":
                        _hydrate_post_review(data.get("input", {}))
                        st_local.session_state["post_review_autorun"] = True
                        st_local.session_state["autorun_session_id"] = sess_id
                        st_local.session_state.page_select = "商談後ふりかえり解析"
                        st_local.rerun()
                    elif sess_type == "icebreaker":
                        _hydrate_icebreaker(data.get("input", {}))
                        st_local.session_state["icebreaker_autorun"] = True
                        st_local.session_state["autorun_session_id"] = sess_id
                        st_local.session_state.page_select = "アイスブレイク生成"
                        st_local.rerun()
            with a_col3:
                # ピン留めトグル
                pinned = bool(meta.get("pinned", False))
                pin_label = "📌 ピン解除" if pinned else "📌 ピン留め"
                if st.button(pin_label, key=f"pin_{sess_id}"):
                    provider = get_storage_provider()
                    provider.set_pinned(sess_id, not pinned)
                    st.experimental_rerun()
            with a_col4:
                st.download_button(
                    "⬇️ JSONをダウンロード",
                    data=json.dumps(data, ensure_ascii=False, indent=2),
                    file_name=f"{sess_type}_{sess_id}.json",
                    mime="application/json",
                    key=f"dl_{sess_id}"
                )

            # 削除（確認ダイアログ）
            del_col1, del_col2 = st.columns([1,3])
            with del_col1:
                if st.session_state.get("confirm_delete") == sess_id:
                    st.warning("本当に削除しますか？ この操作は元に戻せません。")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("はい、削除する", key=f"confirm_yes_{sess_id}"):
                            provider = get_storage_provider()
                            ok = provider.delete_session(sess_id)
                            st.session_state["confirm_delete"] = None
                            if ok:
                                st.success("削除しました")
                                st.experimental_rerun()
                            else:
                                st.error("削除に失敗しました")
                    with c2:
                        if st.button("キャンセル", key=f"confirm_no_{sess_id}"):
                            st.session_state["confirm_delete"] = None
                else:
                    if st.button("🗑️ 削除", key=f"del_{sess_id}"):
                        st.session_state["confirm_delete"] = sess_id
    # 下部バッチ操作バー
    bot_c1, bot_c2, bot_c3, bot_c4, bot_c5, bot_c6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 2])
    with bot_c1:
        st.metric("選択中", f"{len(selected_ids)} 件")
    with bot_c2:
        if st.button("このページを全選択", key="sel_all_bottom"):
            for it in page_items:
                sid = it.get("session_id")
                st.session_state[f"sel_{sid}"] = True
                if sid not in selected_ids:
                    selected_ids.append(sid)
            st.session_state["history_selected_ids"] = selected_ids
            st.experimental_rerun()
    with bot_c3:
        if st.button("選択解除", key="clear_sel_bottom"):
            for it in page_items:
                sid = it.get("session_id")
                st.session_state[f"sel_{sid}"] = False
            st.session_state["history_selected_ids"] = [sid for sid in selected_ids if sid not in [it.get("session_id") for it in page_items]]
            st.experimental_rerun()
    with bot_c4:
        if st.button("📌 選択をピン留め", key="pin_sel_bottom") and selected_ids:
            provider = get_storage_provider()
            for sid in selected_ids:
                provider.set_pinned(sid, True)
            st.success("ピン留めを更新しました")
            st.experimental_rerun()
    with bot_c5:
        if st.button("📌 選択のピン解除", key="unpin_sel_bottom") and selected_ids:
            provider = get_storage_provider()
            for sid in selected_ids:
                provider.set_pinned(sid, False)
            st.success("ピン解除を更新しました")
            st.experimental_rerun()
    with bot_c6:
        if st.button("🗑️ 選択を削除", key="del_sel_bottom") and selected_ids:
            st.session_state["batch_confirm_delete"] = True

    # 削除確認（バッチ）
    if st.session_state.get("batch_confirm_delete"):
        st.warning(f"選択された {len(selected_ids)} 件を削除します。よろしいですか？ この操作は元に戻せません。")
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("はい、削除する", key="batch_del_yes"):
                provider = get_storage_provider()
                ok_count = 0
                for sid in list(selected_ids):
                    if provider.delete_session(sid):
                        ok_count += 1
                st.session_state["history_selected_ids"] = []
                st.session_state["batch_confirm_delete"] = False
                st.success(f"{ok_count} 件を削除しました")
                st.experimental_rerun()
        with bc2:
            if st.button("キャンセル", key="batch_del_no"):
                st.session_state["batch_confirm_delete"] = False

    pager("bottom")
def _hydrate_pre_advice(input_data: Dict[str, Any]) -> None:
    """PreAdviceフォームへ入力を再設定"""
    try:
        st.session_state["sales_type_select"] = SalesType(input_data.get("sales_type")) if input_data.get("sales_type") else None
    except Exception:
        st.session_state["sales_type_select"] = None
    st.session_state["industry_input"] = input_data.get("industry", "")
    st.session_state["product_input"] = input_data.get("product", "")
    # 説明系
    if input_data.get("description_url"):
        st.session_state["description_type"] = "URL"
        st.session_state["description_url"] = input_data.get("description_url", "")
        st.session_state["description_text"] = ""
    else:
        st.session_state["description_type"] = "テキスト"
        st.session_state["description_text"] = input_data.get("description", "")
        st.session_state["description_url"] = ""
    # 競合系
    if input_data.get("competitor_url"):
        st.session_state["competitor_type"] = "URL"
        st.session_state["competitor_url"] = input_data.get("competitor_url", "")
        st.session_state["competitor_text"] = ""
    else:
        st.session_state["competitor_type"] = "テキスト"
        st.session_state["competitor_text"] = input_data.get("competitor", "")
        st.session_state["competitor_url"] = ""
    # ステージ
    st.session_state["stage_select"] = input_data.get("stage", "初期接触")
    st.session_state["purpose_input"] = input_data.get("purpose", "")
    st.session_state["constraints_input"] = "\n".join(input_data.get("constraints", []))


def _hydrate_post_review(input_data: Dict[str, Any]) -> None:
    """PostReviewフォームへ入力を再設定"""
    # セッションキーはページ内で使うキーに合わせて必要に応じて追加
    try:
        st.session_state["post_sales_type"] = SalesType(input_data.get("sales_type")) if input_data.get("sales_type") else None
    except Exception:
        st.session_state["post_sales_type"] = None
    st.session_state["post_industry"] = input_data.get("industry", "")
    st.session_state["post_product"] = input_data.get("product", "")
    st.session_state["post_meeting_content"] = input_data.get("meeting_content", "")
    st.session_state["post_meeting_result"] = input_data.get("meeting_result", "")
    st.session_state["post_customer_reaction"] = input_data.get("customer_reaction", "")
    st.session_state["post_challenges"] = input_data.get("challenges", "")
    st.session_state["post_next_meeting"] = input_data.get("next_meeting", "")


def _hydrate_icebreaker(input_data: Dict[str, Any]) -> None:
    """Icebreakerフォームへ入力を再設定"""
    try:
        st.session_state["icebreaker_sales_type"] = SalesType(input_data.get("sales_type")) if input_data.get("sales_type") else None
    except Exception:
        st.session_state["icebreaker_sales_type"] = None
    st.session_state["icebreaker_industry"] = input_data.get("industry", "")
    st.session_state["icebreaker_company_hint"] = input_data.get("company_hint", "")
    st.session_state["icebreaker_search_enabled"] = input_data.get("search_enabled", True)


def _color_for_tag(tag: str) -> str:
    palette = [
        "#4F46E5", "#059669", "#DB2777", "#D97706", "#2563EB",
        "#16A34A", "#7C3AED", "#EA580C", "#0EA5E9", "#DC2626",
    ]
    h = sum(ord(c) for c in tag)
    return palette[h % len(palette)]


def _render_tag_badges(tags: List[str]) -> None:
    if not tags:
        st.caption("タグは未設定です")
        return
    html = " ".join([
        f"<span style='display:inline-block;padding:2px 8px;border-radius:12px;background:{_color_for_tag(t)};color:#fff;margin-right:6px;margin-bottom:4px;font-size:12px;'>{t}</span>"
        for t in tags if isinstance(t, str) and t
    ])
    st.markdown(html, unsafe_allow_html=True)

