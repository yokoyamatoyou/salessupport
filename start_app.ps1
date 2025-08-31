# Sales SaaS アプリ起動 (PowerShell版)
# UTF-8エンコーディング設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sales SaaS アプリ起動" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 仮想環境の存在確認
if (!(Test-Path "venv")) {
    Write-Host "❌ 仮想環境が見つかりません" -ForegroundColor Red
    Write-Host "   まず setup_venv.bat を実行してください" -ForegroundColor Yellow
    Read-Host "Enterキーを押して終了"
    exit 1
}

# 仮想環境有効化
Write-Host "🔧 仮想環境を有効化しています..." -ForegroundColor Green
& "venv\Scripts\activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 仮想環境の有効化に失敗しました" -ForegroundColor Red
    Read-Host "Enterキーを押して終了"
    exit 1
}

# APIキー確認
$apiKey = $env:OPENAI_API_KEY
if (!$apiKey) {
    Write-Host "⚠️  OPENAI_API_KEYが設定されていません" -ForegroundColor Yellow
    Write-Host "   .envファイルまたは環境変数を設定してください" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "続行しますか？ (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        Write-Host "起動をキャンセルしました" -ForegroundColor Yellow
        Read-Host "Enterキーを押して終了"
        exit 1
    }
} else {
    Write-Host "✅ OpenAI APIキーが設定されています" -ForegroundColor Green
}

# Streamlit起動
Write-Host "🚀 Streamlitアプリを起動しています..." -ForegroundColor Green
Write-Host ""
Write-Host "ブラウザで以下のURLにアクセスしてください:" -ForegroundColor Cyan
Write-Host "  http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "終了するには Ctrl+C を押してください" -ForegroundColor Yellow
Write-Host ""

# Streamlit起動
streamlit run app/ui.py --server.headless true --server.port 8501

Write-Host ""
Read-Host "Enterキーを押して終了"
