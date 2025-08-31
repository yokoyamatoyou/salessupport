# 🚀 Google Cloud移行マニュアル（Cloud初心者向け）

## 📋 概要

このマニュアルは、営業特化SaaSをGoogle Cloud Platform（GCP）に移行するための完全ガイドです。Cloud初心者でも安全に移行できるよう、段階的に説明します。

## 🎯 移行の流れ

1. **GCPプロジェクトの準備** ← 最初に完了
2. **必要なAPIの有効化** ← 最初に完了
3. **Dockerイメージの準備**
4. **Cloud Runへのデプロイ**
5. **環境変数とシークレットの設定**
6. **動作確認とトラブルシューティング**

---

## 🏗️ 1. GCPプロジェクトの準備（最初に完了）

### 1.1 プロジェクトの作成

```bash
# 新しいプロジェクトを作成（推奨）
gcloud projects create sales-saas-[YOUR-UNIQUE-ID] --name="営業特化SaaS"

# プロジェクトを選択
gcloud config set project sales-saas-[YOUR-UNIQUE-ID]

# プロジェクトIDを確認
gcloud config get-value project
```

### 1.2 請求の有効化

**⚠️ 重要**: 必ず最初に請求を有効化してください！

```bash
# 請求アカウントの確認
gcloud billing accounts list

# プロジェクトに請求アカウントをリンク
gcloud billing projects link sales-saas-[YOUR-UNIQUE-ID] --billing-account=[BILLING-ACCOUNT-ID]
```

---

## 🔌 2. 必要なAPIの有効化（最初に完了）

### 2.1 必須APIの一括有効化

```bash
# 必要なAPIを一括で有効化
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com
```

### 2.2 API有効化の確認

```bash
# 有効化されたAPIの確認
gcloud services list --enabled --filter="name:run.googleapis.com OR name:cloudbuild.googleapis.com OR name:artifactregistry.googleapis.com"
```

---

## 🐳 3. Dockerイメージの準備

### 3.1 Dockerfileの確認

現在の`Dockerfile`が正しく設定されているか確認：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
ENTRYPOINT ["streamlit", "run", "app/ui.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

### 3.2 ローカルでのDockerビルドテスト

```bash
# ローカルでDockerイメージをビルド
docker build -t sales-saas .

# ローカルで動作確認
docker run -p 8080:8080 sales-saas
```

---

## 🚀 4. Cloud Runへのデプロイ

### 4.1 Artifact Registryの準備

```bash
# リポジトリの作成
gcloud artifacts repositories create sales-saas-repo \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="営業特化SaaS用Dockerリポジトリ"

# リポジトリの確認
gcloud artifacts repositories list
```

### 4.2 Dockerイメージのビルドとプッシュ

```bash
# イメージのタグ付け
docker tag sales-saas asia-northeast1-docker.pkg.dev/sales-saas-[YOUR-UNIQUE-ID]/sales-saas-repo/sales-saas:latest

# イメージのプッシュ
docker push asia-northeast1-docker.pkg.dev/sales-saas-[YOUR-UNIQUE-ID]/sales-saas-repo/sales-saas:latest
```

### 4.3 Cloud Runへのデプロイ

```bash
# Cloud Runサービスをデプロイ
gcloud run deploy sales-saas \
  --image=asia-northeast1-docker.pkg.dev/sales-saas-[YOUR-UNIQUE-ID]/sales-saas-repo/sales-saas:latest \
  --platform=managed \
  --region=asia-northeast1 \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=1 \
  --max-instances=10 \
  --min-instances=0
```

---

## 🔐 5. 環境変数とシークレットの設定

### 5.1 Secret Managerの設定

```bash
# OpenAI APIキーをシークレットとして保存
echo -n "sk-your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# シークレットの確認
gcloud secrets list
```

### 5.2 Cloud Runサービスにシークレットを追加

GCSにセッションを保存するため、以下の環境変数を設定します：

- `STORAGE_PROVIDER=gcs`
- `GCS_BUCKET_NAME`（必須）
- `GCS_PREFIX`（任意、デフォルトは `sessions`）

```bash
# 環境変数としてシークレットを追加
gcloud run services update sales-saas \
  --region=asia-northeast1 \
  --set-env-vars="OPENAI_API_KEY=projects/sales-saas-[YOUR-UNIQUE-ID]/secrets/openai-api-key/versions/latest" \
  --set-env-vars="APP_ENV=production" \
  --set-env-vars="STORAGE_PROVIDER=gcs" \
  --set-env-vars="GCS_BUCKET_NAME=your-bucket-name" \
  --set-env-vars="GCS_PREFIX=sessions" \
  --set-env-vars="DATA_DIR=/tmp"
```

ローカル環境から GCS や Firestore へアクセスする場合は `GOOGLE_APPLICATION_CREDENTIALS` にサービスアカウント JSON のパスを設定してください。Cloud Run 上ではデフォルトのサービスアカウントが利用されるため、この変数を設定する必要はありません。

---

## 🔍 6. 動作確認とトラブルシューティング

### 6.1 デプロイ状況の確認

```bash
# サービスの状況確認
gcloud run services describe sales-saas --region=asia-northeast1

# ログの確認
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=sales-saas" --limit=50
```

### 6.2 よくあるエラーと対処法

#### エラー1: "Permission denied" または "Insufficient permissions"

```bash
# 必要な権限を付与
gcloud projects add-iam-policy-binding sales-saas-[YOUR-UNIQUE-ID] \
  --member="serviceAccount:YOUR-EMAIL@gmail.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding sales-saas-[YOUR-UNIQUE-ID] \
  --member="serviceAccount:YOUR-EMAIL@gmail.com" \
  --role="roles/iam.serviceAccountUser"
```

#### エラー2: "API not enabled"

```bash
# 特定のAPIを有効化
gcloud services enable [API-NAME].googleapis.com
```

#### エラー3: "Billing not enabled"

```bash
# 請求の有効化確認
gcloud billing projects describe sales-saas-[YOUR-UNIQUE-ID]
```

---

## 📝 7. 移行後の設定

### 7.1 カスタムドメインの設定（オプション）

```bash
# カスタムドメインのマッピング
gcloud run domain-mappings create \
  --service=sales-saas \
  --domain=your-domain.com \
  --region=asia-northeast1
```

### 7.2 監視とログの設定

```bash
# Cloud Loggingの有効化
gcloud services enable logging.googleapis.com

# アラートポリシーの作成（オプション）
gcloud alpha monitoring policies create --policy-from-file=alert-policy.yaml
```

---

## 🛠️ 8. 移行スクリプト

### 8.1 一括移行スクリプト

```bash
#!/bin/bash
# migrate-to-gcp.sh

set -e

PROJECT_ID="sales-saas-[YOUR-UNIQUE-ID]"
REGION="asia-northeast1"
SERVICE_NAME="sales-saas"

echo "🚀 GCP移行を開始します..."

# プロジェクトの設定
gcloud config set project $PROJECT_ID

# 必要なAPIの有効化
echo "📡 必要なAPIを有効化中..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com

# Artifact Registryの準備
echo "🐳 Dockerリポジトリを準備中..."
gcloud artifacts repositories create sales-saas-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="営業特化SaaS用Dockerリポジトリ"

# Dockerイメージのビルドとプッシュ
echo "🔨 Dockerイメージをビルド中..."
docker build -t sales-saas .
docker tag sales-saas $REGION-docker.pkg.dev/$PROJECT_ID/sales-saas-repo/sales-saas:latest
docker push $REGION-docker.pkg.dev/$PROJECT_ID/sales-saas-repo/sales-saas:latest

# Cloud Runへのデプロイ
echo "🚀 Cloud Runにデプロイ中..."
gcloud run deploy $SERVICE_NAME \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/sales-saas-repo/sales-saas:latest \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=1 \
  --max-instances=10 \
  --min-instances=0

echo "✅ 移行が完了しました！"
echo "🌐 サービスURL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')"
```

### 8.2 スクリプトの実行

```bash
# スクリプトに実行権限を付与
chmod +x migrate-to-gcp.sh

# スクリプトを実行
./migrate-to-gcp.sh
```

---

## 🔒 9. セキュリティのベストプラクティス

### 9.1 IAMの最小権限の原則

```bash
# 必要最小限の権限のみを付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:YOUR-EMAIL@gmail.com" \
  --role="roles/run.developer"
```

### 9.2 シークレットの定期ローテーション

```bash
# シークレットの新しいバージョンを作成
echo -n "new-api-key" | gcloud secrets versions add openai-api-key --data-file=-

# 古いバージョンを無効化
gcloud secrets versions disable 1 --secret="openai-api-key"
```

---

## 📊 10. コスト最適化

### 10.1 インスタンス数の調整

```bash
# 本番環境での設定
gcloud run services update sales-saas \
  --region=asia-northeast1 \
  --min-instances=1 \
  --max-instances=5

# 開発環境での設定
gcloud run services update sales-saas \
  --region=asia-northeast1 \
  --min-instances=0 \
  --max-instances=2
```

### 10.2 リソース使用量の監視

```bash
# コストレポートの確認
gcloud billing budgets list

# リソース使用量の確認
gcloud compute instances list
```

---

## 🚨 11. 緊急時の対処法

### 11.1 サービスが起動しない場合

```bash
# サービスの詳細確認
gcloud run services describe sales-saas --region=asia-northeast1

# ログの詳細確認
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=sales-saas" --limit=100

# サービスの再デプロイ
gcloud run services replace service.yaml
```

### 11.2 ロールバック

```bash
# 前のバージョンに戻す
gcloud run revisions list --service=sales-saas --region=asia-northeast1
gcloud run services update-traffic sales-saas --to-revisions=REVISION-NAME=100 --region=asia-northeast1
```

---

## 📚 12. 参考資料

### 12.1 公式ドキュメント

- [Cloud Run 公式ドキュメント](https://cloud.google.com/run/docs)
- [Artifact Registry 公式ドキュメント](https://cloud.google.com/artifact-registry/docs)
- [Secret Manager 公式ドキュメント](https://cloud.google.com/secret-manager/docs)

### 12.2 トラブルシューティング

- [Cloud Run トラブルシューティング](https://cloud.google.com/run/docs/troubleshooting)
- [IAM トラブルシューティング](https://cloud.google.com/iam/docs/troubleshooting)

---

## 🎯 次のステップ

移行が完了したら、以下の作業を検討してください：

1. **CI/CDパイプラインの構築**
2. **監視とアラートの設定**
3. **バックアップ戦略の策定**
4. **セキュリティ監査の実施**

---

## 📞 サポート

問題が発生した場合は、以下の順序で対処してください：

1. このマニュアルの該当セクションを確認
2. Google Cloud 公式ドキュメントを確認
3. Stack Overflow で検索
4. Google Cloud サポートに問い合わせ

**🚀 安全で確実なGCP移行を目指しましょう！**
