# 営業特化SaaS

GCP上で動く**マルチテナント**の営業特化SaaS（Streamlit UI + 将来的にAPI層）。

## プロジェクト構造

```
sales-saas-main/
├── app/                          # Streamlitアプリケーション
│   ├── components/               # UIコンポーネント
│   │   ├── sales_style_diagnosis.py    # 営業スタイル診断
│   │   ├── practical_icebreaker.py     # 実践的アイスブレイク生成
│   │   ├── smart_defaults.py           # スマートデフォルト設定
│   │   └── copy_button.py              # コピーボタン
│   ├── pages/                   # ページコンポーネント
│   │   ├── pre_advice.py        # 事前アドバイス生成
│   │   ├── post_review.py       # 商談後ふりかえり
│   │   ├── icebreaker.py        # アイスブレイク生成
│   │   ├── history.py           # 履歴管理
│   │   └── settings.py          # 設定
│   ├── static/                  # 静的ファイル
│   │   └── responsive.css       # モバイル対応CSS
│   └── ui.py                    # メインUI
├── core/                        # コアモデル・ビジネスロジック
│   ├── models.py                # Pydanticモデル
│   ├── schema.py                # JSONスキーマ定義
│   └── validation.py            # バリデーション
├── services/                    # サービス層
│   ├── pre_advisor.py           # 事前アドバイスサービス
│   ├── post_analyzer.py         # 商談後分析サービス
│   ├── icebreaker.py            # アイスブレイクサービス
│   ├── prompt_manager.py        # プロンプト管理
│   ├── schema_manager.py        # スキーマ管理
│   ├── security_utils.py        # セキュリティユーティリティ
│   └── di_container.py          # 依存性注入コンテナ
├── providers/                   # 外部サービスプロバイダー
│   ├── llm_openai.py            # OpenAIプロバイダー
│   ├── search_provider.py       # 検索プロバイダー
│   └── storage_*.py             # ストレージプロバイダー
├── prompts/                     # プロンプトテンプレート
├── config/                      # 設定ファイル
├── data/                        # データファイル
├── tests/                       # テストファイル
├── docs/                        # ドキュメント
├── cloudrun/                    # Cloud Run設定
└── pyproject.toml               # パッケージ設定
```

## 機能

### MVP機能
- **事前アドバイス生成**：短期/中期・JSON構造
- **商談後ふりかえり解析**：要約/BANT/反論/次アクション/メール草案
- **アイスブレイク・ネタ生成**：ユーザーの"自分のタイプ"+業界ニュースから1行
- 3つの軽い追加入力（業界/目的/制約）
- JSONスキーマで厳格受け取り（UIカードへ表示）

### 履歴・UX
- セッション保存（`data/sessions/{uuid}.json`）とSession ID表示
- 履歴ページ（フィルタ/検索/並び替え/ページネーション）
- 再生成・即時再生成（オートラン）
- 複数選択での一括ピン留め/解除・削除
- タグ（色分けバッジ、マルチセレクト絞込、既存タグサジェスト＋新規追加、ドラッグ並び替え）
- モバイル最適化（パディング/ボタン全幅/フォント、タグ並び替えは狭幅で縦方向）

## 前提条件

- Python 3.11
- Docker（推奨）または venv
- OpenAI API Key

## 起動方法

### Windows環境（BATファイル使用）

#### 初回セットアップ（仮想環境作成・依存関係インストール）
```cmd
setup_venv.bat
```

#### 通常起動（仮想環境使用）
```cmd
start_app.bat
```

#### Docker起動
```cmd
start_docker.bat
```

#### クイックテスト（初回セットアップ + テスト）
```cmd
quick_test.bat
```

### Linux/macOS環境

#### Dockerでの起動（推奨）

```bash
# Dockerイメージのビルド
make docker-build

# 起動ファイルに実行権限を付与
chmod +x start_docker.sh

# 起動
./start_docker.sh
```

### ローカル環境での起動

```bash
# 起動ファイルに実行権限を付与
chmod +x start_local.sh

# 起動
./start_local.sh
```

## 環境変数

`.env`ファイルを作成し、以下の環境変数を設定してください：

```bash
APP_ENV=local
OPENAI_API_KEY=sk-xxxx
DATA_DIR=./data
LOCAL_TENANT_ID=         # optional tenant id for local storage
STORAGE_PROVIDER=local  # local|gcs|firestore
GCS_BUCKET_NAME=        # required when STORAGE_PROVIDER=gcs
GCS_PREFIX=sessions     # optional prefix path
GCS_TENANT_ID=          # required when STORAGE_PROVIDER=gcs
FIRESTORE_TENANT_ID=    # required when STORAGE_PROVIDER=firestore
GOOGLE_APPLICATION_CREDENTIALS=path/to/cred.json  # optional on Cloud Run
SEARCH_PROVIDER=none   # none|cse|newsapi|hybrid
CSE_API_KEY=            # required when SEARCH_PROVIDER=cse or hybrid
CSE_CX=                 # required when SEARCH_PROVIDER=cse or hybrid
NEWSAPI_KEY=            # required when SEARCH_PROVIDER=newsapi or hybrid
```

`STORAGE_PROVIDER` を `gcs` に設定する場合は `GCS_BUCKET_NAME` と `GCS_TENANT_ID`（必須）、必要に応じて `GCS_PREFIX` を、`firestore` に設定する場合は `FIRESTORE_TENANT_ID` を設定してください。ローカルストレージでテナント分離を行う場合は `LOCAL_TENANT_ID` を指定します。Cloud Run では自動的にサービスアカウントが利用されるため `GOOGLE_APPLICATION_CREDENTIALS` は不要ですが、ローカルから GCS や Firestore にアクセスする際は `GOOGLE_APPLICATION_CREDENTIALS` にサービスアカウント JSON のパスを設定します。

`SEARCH_PROVIDER` を `cse` または `hybrid` に設定する場合は `CSE_API_KEY` と `CSE_CX` を、`newsapi` または `hybrid` に設定する場合は `NEWSAPI_KEY` をそれぞれ設定してください。

### Web検索の使用例

```python
from services.search_enhancer import SearchEnhancerService

service = SearchEnhancerService()
result = service.enhanced_search("最新のAI動向", industry="IT")
for item in result["search_results"]:
    print(item["title"], item["url"])
```

環境変数 `SEARCH_PROVIDER` によって使用する検索プロバイダーを切り替えられます。`hybrid` を選択すると CSE と NewsAPI の結果を統合して返します。

## GCPへの移行

`migrate-to-gcp.sh` を使うとアプリを Google Cloud にデプロイできます。非対話モードでの実行例:

```bash
./migrate-to-gcp.sh -p my-proj -r asia-northeast1
```

`OPENAI_API_KEY` は環境変数から取得され、未設定の場合のみ実行時にプロンプトが表示されます。

## Cloud Run デプロイ

`cloudrun/` ディレクトリに Cloud Run 用の `Dockerfile` と `cloudrun.yaml` を配置しています。

1. イメージをビルドし Artifact Registry へプッシュ:

```bash
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$PROJECT_ID/sales-saas-repo/sales-saas
```

2. Firestore と Secret Manager 用の環境変数を設定してデプロイ (Cloud Run では `GOOGLE_APPLICATION_CREDENTIALS` を設定する必要はありません):

```bash
export FIRESTORE_TENANT_ID=tenant-123
export OPENAI_API_SECRET_NAME=openai-api-key
make deploy-cloudrun
```

3. Cloud Run 実行サービスアカウントに必要な権限を付与:

- `roles/datastore.user` (Firestore アクセス)
- `roles/secretmanager.secretAccessor` (Secret Manager アクセス)

`cloudrun/cloudrun.yaml` にはポート `8080` と上記の環境変数が定義されています。

## LLMプロバイダのJSONスキーマ対応

`OpenAIProvider.call_llm` に `json_schema` を渡すと、OpenAI API は
`response_format={"type": "json_schema", "json_schema": schema, "strict": True}`
を利用して呼び出されます。スキーマに合わない応答は `ValueError`
として扱われ、呼び出し元で検知できます。

## テスト

```bash
# テスト実行（全体）
pytest -q

# 主要テスト
pytest tests/test_validation.py -q
pytest tests/test_services.py -q
pytest tests/test_icebreaker.py -q
pytest tests/test_storage_local.py -q

# パフォーマンステスト
pytest tests/performance/test_post_analyzer.py -q
```

## Makefile コマンド

開発を簡単にするための Makefile ターゲットを用意しています。

```bash
make run         # ローカル環境で起動
make docker-run  # Dockerで起動
make test        # テスト実行
make lint        # 構文チェック
make deploy-cloudrun  # Cloud Run にデプロイ
```

## 翻訳キーの命名規則

- 重複を避けるため、翻訳キーは `page_element_name` 形式で命名する
  - 例: `pre_advice_industry_label`, `post_review_product_label`

## プロジェクト構造

```
repo/
  app/                    # Streamlit UI（MVPはUI直呼び）
    pages/
      1_PreAdvice.py
      2_PostReview.py
    components/           # UI部品
    ui.py                 # ルート（サイドバーなど）
  core/                   # ドメイン（Pydanticモデル、バリデーション）
    models.py
    schema.py
    validation.py
  services/               # ユースケース（LLM/アイスブレイク/要約など）
    pre_advisor.py
    post_analyzer.py
    icebreaker.py
  providers/              # インフラ依存（LLM・検索・保存）
    llm_openai.py
    search_provider.py
    storage_local.py
  prompts/                # Jinja2/YAMLなどで管理
    pre_advice.yaml
    post_review.yaml
    icebreaker.yaml
  data/                   # ローカル保存（JSON/添付）
  tests/
    test_validation.py
    test_services.py
    test_icebreaker.py
  Dockerfile
  docker-compose.yml
  requirements.txt
  env.example
  start_local.sh          # venvでの起動ファイル
  start_docker.sh         # Dockerでの起動ファイル
  README.md
```

## 営業タイプ（9種）

- 🏹 ハンター：短文・行動促進・前向き
- 🔒 クローザー：価値訴求→締めの一言
- 🤝 リレーション：共感・近況・柔らかめ
- 🧭 コンサル：課題仮説・問いかけ
- ⚡ チャレンジャー：仮説提示・視点転換
- 📖 ストーリーテラー：具体例・物語
- 📊 アナリスト：事実・データ起点
- 🧩 問題解決：障害除去・次の一歩
- 🌾 ファーマー：長期関係・紹介喚起

## 開発状況

- [x] フェーズ0：環境準備
- [x] フェーズ1：ドメインモデル & バリデーション
- [x] フェーズ2：LLMアダプタ（OpenAI）
- [x] フェーズ3：アイスブレイク・ネタ生成
- [x] フェーズ4：事前アドバイス生成（UI + サービス）
- [x] フェーズ5：商談後ふりかえり解析
- [x] フェーズ6：ローカル永続化・履歴・テンプレ
- [x] フェーズ7：起動・配布（MVP完了チェック）
- [ ] フェーズ8：GCP移行（シングルテナント→マルチテナント）
- [ ] フェーズ9：Webリサーチ実装
- [ ] フェーズ10：品質・セキュリティ
## プロジェクトドキュメント

- 進捗ログ: [docs/PROGRESS.md](docs/PROGRESS.md)
- 重要な決定: [docs/DECISIONS.md](docs/DECISIONS.md)

## ライセンス

MIT License

