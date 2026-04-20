# 7DTD Status API (Fly.io)

Steam A2S (UDP) クエリで `220.158.24.94:26900` を直接問い合わせ、
JSON を返す小さな HTTP サービス。`server/7DaysStatus.html` から
`fetch()` される。

## アーキテクチャ

```
ブラウザ ──GET /status──▶ Fly.io (api-server)
                             │ UDP A2S_INFO / A2S_PLAYER
                             ▼
                        220.158.24.94:26900 (7DTD)
```

- キャッシュ: 20 秒 (in-memory)。多重ポーリング時も A2S 実行は毎 20 秒に 1 回
- Auto-sleep: リクエストがない間マシン停止 → 無料枠で運用可
- CORS: `ALLOW_ORIGINS` に列挙したオリジンのみ許可

## デプロイ (初回)

```bash
# 1. flyctl インストール
curl -L https://fly.io/install.sh | sh

# 2. ログイン
flyctl auth login

# 3. このディレクトリで app 作成 & デプロイ
cd api-server
flyctl launch --copy-config --no-deploy --name <好きな名前>
flyctl deploy
```

デプロイ完了後に表示される URL (例: `https://<名前>.fly.dev`) を
`server/7DaysStatus.html` の `API_URL` に設定してコミット。

## 更新

```bash
cd api-server
flyctl deploy
```

## 環境変数 (`fly.toml` `[env]` で変更)

| 変数            | 既定値                          | 用途                         |
|-----------------|---------------------------------|------------------------------|
| SERVER_HOST     | 220.158.24.94                   | 対象サーバー IP              |
| SERVER_PORT     | 26900                           | Steam A2S クエリポート       |
| CACHE_SEC       | 20                              | 結果キャッシュ秒数           |
| QUERY_TIMEOUT   | 3                               | A2S タイムアウト秒           |
| ALLOW_ORIGINS   | https://dahande.github.io       | CORS 許可オリジン (カンマ区切り) |

## ローカル実行

```bash
cd api-server
pip install -r requirements.txt
python app.py
curl http://localhost:8080/status
```
