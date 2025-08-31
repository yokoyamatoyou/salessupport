from typing import List, Dict, Any, Optional
import os
import random
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class WebSearchProvider:
    """Web検索プロバイダーのインターフェース"""
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.search_provider = os.getenv("SEARCH_PROVIDER", "none")
        self.offline_mode = False
    
    def _get_search_config(self):
        """設定から検索設定を取得"""
        if self.settings_manager:
            try:
                settings = self.settings_manager.load_settings()
                # 型をサニタイズ（Mock対策）
                provider = getattr(settings, 'search_provider', self.search_provider)
                limit = getattr(settings, 'search_results_limit', 5)
                doms = getattr(settings, 'search_trusted_domains', None)
                if not isinstance(doms, list):
                    doms = []
                wnd = getattr(settings, 'search_time_window_days', 60)
                if not isinstance(wnd, int):
                    try:
                        wnd = int(wnd)  # type: ignore[arg-type]
                    except Exception:
                        wnd = 60
                lang = getattr(settings, 'search_language', 'ja')
                if not isinstance(lang, str):
                    lang = 'ja'
                return {
                    "provider": provider,
                    "limit": limit,
                    "trusted_domains": doms,
                    "time_window_days": wnd,
                    "language": lang,
                }
            except Exception:
                pass
        
        return {
            "provider": self.search_provider,
            "limit": 5,
            "trusted_domains": ["www.bloomberg.co.jp", "www.nikkei.com"],
            "time_window_days": 60,
            "language": "ja",
        }
    
    def search(self, query: str, num: int = 3) -> List[Dict[str, Any]]:
        """検索を実行

        戻り値の各要素: {
            title, url, snippet, source, published_at(ISO8601|None), score, reasons(list[str])
        }
        """
        config = self._get_search_config()
        provider = (config.get("provider") or "none").lower()

        if provider == "none":
            results = self._search_none(query, num)
        elif provider == "stub":
            results = self._search_stub(query, num)
        elif provider == "cse":
            results = self._search_cse_with_fallback(query, num)
        elif provider == "newsapi":
            results = self._search_newsapi_with_fallback(query, num)
        elif provider == "hybrid":
            results = self._search_hybrid(query, num, config.get("limit", num))
        else:
            results = self._search_unknown(query, num)

        if not results:
            return [{
                "title": "検索結果なし",
                "snippet": "ヒットしませんでした。別のキーワードで再検索してください。",
                "url": "",
                "source": "system",
            }]

        if self.offline_mode:
            logger.warning("オフラインモード: Web検索に失敗したためスタブデータを使用します。")

        return results

    def _search_none(self, query: str, num: int) -> List[Dict[str, Any]]:
        return []

    def _search_stub(self, query: str, num: int) -> List[Dict[str, Any]]:
        return self._rank_results(self._get_stub_results(query, num), query, num)

    def _search_cse_with_fallback(self, query: str, num: int) -> List[Dict[str, Any]]:
        res = self._rank_results(self._search_cse(query, num), query, num)
        if res:
            return res
        alt = self._rank_results(self._search_newsapi(query, num), query, num)
        return alt if alt else self._rank_results(self._get_stub_results(query, num), query, num)

    def _search_newsapi_with_fallback(self, query: str, num: int) -> List[Dict[str, Any]]:
        res = self._rank_results(self._search_newsapi(query, num), query, num)
        if res:
            return res
        alt = self._rank_results(self._search_cse(query, num), query, num)
        return alt if alt else self._rank_results(self._get_stub_results(query, num), query, num)

    def _search_hybrid(self, query: str, num: int, limit: int) -> List[Dict[str, Any]]:
        merged = self._merge_dedupe(
            self._search_cse(query, num),
            self._search_newsapi(query, num),
            limit=max(num, limit),
        )
        res = self._rank_results(merged, query, num)
        return res if res else self._rank_results(self._get_stub_results(query, num), query, num)

    def _search_unknown(self, query: str, num: int) -> List[Dict[str, Any]]:
        return self._rank_results(self._get_stub_results(query, num), query, num)
    
    def _get_stub_results(self, query: str, num: int) -> List[Dict[str, Any]]:
        """スタブ検索結果を返す"""
        # 業界別の一般的なニューステンプレート
        industry_news = {
            "IT": [
                "AI技術の進歩により、業務効率化が加速",
                "クラウド移行が業界全体で進展",
                "サイバーセキュリティの重要性が増加"
            ],
            "製造業": [
                "DX推進による生産性向上が注目",
                "サプライチェーンの最適化が課題",
                "環境配慮型製造への転換が進行"
            ],
            "金融業": [
                "フィンテックによる金融サービス革新",
                "ESG投資の拡大が続く",
                "デジタル通貨への関心が高まる"
            ],
            "医療": [
                "テレメディシンの普及が加速",
                "AI診断支援システムの実用化",
                "個別化医療への期待が高まる"
            ],
            "小売": [
                "EC化の進展で店舗戦略が変化",
                "顧客体験向上への投資が活発",
                "サステナビリティへの配慮が重要に"
            ]
        }
        
        # クエリから業界を推測
        detected_industry = "IT"  # デフォルト
        for industry in industry_news.keys():
            if industry in query:
                detected_industry = industry
                break
        
        # 業界別のニュースを取得
        industry_specific_news = industry_news.get(detected_industry, industry_news["IT"])
        
        # ランダムにニュースを選択
        selected_news = random.sample(industry_specific_news, min(num, len(industry_specific_news)))
        
        results: List[Dict[str, Any]] = []
        for i, news in enumerate(selected_news):
            results.append({
                "title": f"{detected_industry}業界の最新動向{i+1}",
                "url": f"https://example.com/news{i+1}",
                "snippet": news,
                "source": "stub",
                "published_at": None,
            })
        
        return results

    # ============ 実プロバイダ ============
    def _search_cse(self, query: str, num: int) -> List[Dict[str, Any]]:
        api_key = os.getenv("CSE_API_KEY")
        cx = os.getenv("CSE_CX")
        if not api_key or not cx:
            return []
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": min(10, max(1, num)),
            "hl": "ja",
            "safe": "active",
        }
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            self.offline_mode = True
            logger.warning("CSE search failed: %s", e)
            return self._load_cached_results(query, num)
        items = data.get("items", []) or []
        results: List[Dict[str, Any]] = []
        for it in items[:num]:
            results.append({
                "title": it.get("title"),
                "url": it.get("link"),
                "snippet": it.get("snippet"),
                "source": "cse",
                "published_at": None,
            })
        return results

    def _search_newsapi(self, query: str, num: int) -> List[Dict[str, Any]]:
        api_key = os.getenv("NEWSAPI_KEY")
        if not api_key:
            return []
        url = "https://newsapi.org/v2/everything"
        cfg = self._get_search_config()
        params = {
            "q": query,
            "pageSize": min(20, max(1, num * 2)),
            "language": cfg.get("language", "ja"),
            "sortBy": "publishedAt",
            "apiKey": api_key,
        }
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            self.offline_mode = True
            logger.warning("NewsAPI search failed: %s", e)
            return self._load_cached_results(query, num)
        arts = data.get("articles", []) or []
        results: List[Dict[str, Any]] = []
        for a in arts[: max(1, num * 2)]:
            results.append({
                "title": a.get("title"),
                "url": a.get("url"),
                "snippet": a.get("description") or a.get("content"),
                "source": "newsapi",
                "published_at": a.get("publishedAt"),
            })
        return results[:num]

    def _load_cached_results(self, query: str, num: int) -> List[Dict[str, Any]]:
        cache_path = Path(__file__).resolve().parent.parent / "data" / "search_cache.json"
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            for key, items in cache.items():
                if key.lower() in query.lower():
                    return items[:num]
        except Exception:
            pass
        return self._get_stub_results(query, num)

    # ============ マージ・スコアリング ============
    def _merge_dedupe(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        seen = set()
        merged: List[Dict[str, Any]] = []
        for item in [*a, *b]:
            key = self._normalize_url(item.get("url"))
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                break
        return merged

    def _normalize_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        try:
            p = urlparse(url)
            return f"{p.netloc}{p.path}".lower()
        except Exception:
            return url

    def _rank_results(self, items: List[Dict[str, Any]], query: str, num: int) -> List[Dict[str, Any]]:
        """高度化された検索結果のランキング"""
        if not items:
            return []
        now = datetime.now(timezone.utc)
        cfg = self._get_search_config()
        keywords = [w for w in re.split(r"\s+", query) if len(w) >= 2]
        trusted_domains_map = {d: 1.0 for d in cfg.get("trusted_domains", [])}
        ranked: List[Dict[str, Any]] = []
        
        for it in items:
            score = 0.0
            reasons: List[str] = []
            fresh = 0.0  # 新鮮度スコアを初期化

            # 1. 新鮮度スコア（時効性の重要度を向上）
            ts = it.get("published_at")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    days = max(0, (now - dt).days)
                    window = max(1, int(cfg.get("time_window_days", 60)))

                    # 非線形な新鮮度計算（より新しい記事により高い重み）
                    if days <= 1:
                        fresh = 1.0  # 24時間以内
                    elif days <= 7:
                        fresh = 0.9  # 1週間以内
                    elif days <= 30:
                        fresh = 0.7  # 1ヶ月以内
                    elif days <= 90:
                        fresh = 0.4  # 3ヶ月以内
                    else:
                        fresh = max(0.1, 1.0 - (days / float(window)))

                    score += fresh * 1.2  # 新鮮度の重みを増加
                    reasons.append("freshness")
                except Exception:
                    pass
            
            # 2. ドメイン信頼性スコア（階層化された信頼度）
            host = urlparse(it.get("url", "")).netloc
            if host in trusted_domains_map:
                # 信頼ドメインの種類に応じた重み付け
                if any(high_trust in host for high_trust in ["www.nikkei.com", "www.bloomberg.co.jp", "www.reuters.com"]):
                    score += 1.0  # 最高信頼度
                    reasons.append("high_trusted_domain")
                elif any(medium_trust in host for medium_trust in ["techcrunch.com", "wired.com", "mit.edu"]):
                    score += 0.8  # 中程度信頼度
                    reasons.append("medium_trusted_domain")
                else:
                    score += 0.6  # 基本信頼度
                    reasons.append("trusted_domain")
            
            # 3. クエリ関連性スコア（より洗練されたマッチング）
            text = ((it.get("title") or "") + " " + (it.get("snippet") or "")).lower()
            
            # タイトルとスニペットの重み付け
            title_text = (it.get("title") or "").lower()
            snippet_text = (it.get("snippet") or "").lower()
            
            title_matches = sum(1 for k in keywords if k.lower() in title_text)
            snippet_matches = sum(1 for k in keywords if k.lower() in snippet_text)
            
            # タイトルマッチの方が重要
            relevance_score = (title_matches * 0.7 + snippet_matches * 0.3) / max(1, len(keywords))
            score += min(1.0, relevance_score) * 0.8
            reasons.append("keyword_match")
            
            # 4. コンテンツ品質スコア（新しい指標）
            content_quality = 0.0
            
            # タイトルの長さ（適切な長さを評価）
            title_length = len(it.get("title", ""))
            if 20 <= title_length <= 100:
                content_quality += 0.2
                reasons.append("optimal_title_length")
            
            # スニペットの詳細度
            snippet_length = len(it.get("snippet", ""))
            if snippet_length >= 100:
                content_quality += 0.2
                reasons.append("detailed_snippet")
            
            # 特殊文字やHTMLタグの除去
            clean_text = re.sub(r'<[^>]+>', '', text)
            if clean_text == text:
                content_quality += 0.1
                reasons.append("clean_content")
            
            score += content_quality
            reasons.append("content_quality")
            
            # 5. ソース品質スコア
            source_quality = 0.0
            source = it.get("source", "")
            
            if source == "newsapi":
                source_quality += 0.3
                reasons.append("news_api_source")
            elif source == "cse":
                source_quality += 0.2
                reasons.append("custom_search_source")
            
            score += source_quality
            
            # 6. 多様性ボーナス（同じドメインからの結果を抑制）
            domain_count = sum(1 for r in ranked if urlparse(r.get("url", "")).netloc == host)
            if domain_count == 0:
                score += 0.1
                reasons.append("diversity_bonus")
            
            # スコアの正規化と最終調整
            final_score = min(5.0, score)  # 最大スコアを5.0に制限
            
            it["score"] = round(final_score, 3)
            it["reasons"] = reasons
            it["detailed_scoring"] = {
                "freshness": fresh,
                "reliability": score - fresh - content_quality - source_quality,
                "relevance": relevance_score * 0.8,
                "content_quality": content_quality,
                "source_quality": source_quality
            }
            
            ranked.append(it)
        
        # スコアによる並び替え
        ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # 結果の多様性を確保（上位結果のドメイン重複を制限）
        final_results = []
        seen_domains = set()
        
        # まず、ドメインが重複しない結果を優先的に追加
        for item in ranked:
            if len(final_results) >= num:
                break
            
            host = urlparse(item.get("url", "")).netloc
            if host not in seen_domains:
                final_results.append(item)
                seen_domains.add(host)
        
        # 要求された数に満たない場合は、残りの結果を追加
        if len(final_results) < num:
            for item in ranked:
                if len(final_results) >= num:
                    break
                
                # まだ追加されていない結果のみ
                if item not in final_results:
                    final_results.append(item)
        
        return final_results[:num]

