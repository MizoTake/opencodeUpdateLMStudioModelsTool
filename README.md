# OpenCode モデルリスト更新ツール

LM Studio のローカル API からモデル一覧を動的に取得し、OpenCode の設定ファイル (`~/.config/opencode/opencode.jsonc`) にカスタムプロバイダーとして登録するスクリプトです。

## 背景

OpenCode のモデルリスト (`~/.cache/opencode/models.json`) は起動時に再生成されるため、直接編集しても反映されません。このツールは `opencode.jsonc` の `provider` セクションを使い、OpenCode の正規のカスタムプロバイダー機能でモデルを登録します。

## 機能

- LM Studio の `/v1/models` エンドポイントからモデル一覧を取得
- コンテキスト長・出力長などの設定を自動反映
- `opencode.jsonc` の既存設定を保持し、lmstudio プロバイダーのみ更新
- API ベース URL・認証キーを引数または環境変数で設定可能

## 使い方

1. LM Studio が起動していることを確認してください
2. コマンドラインで実行します：

```bash
python update_opencode_models.py --api-key YOUR_KEY
```

3. OpenCode を再起動すると、LM Studio のモデルが選択可能になります。

## オプション

| オプション | 説明 |
|-----------|------|
| `--force` | 既存の lmstudio モデル定義があっても強制更新する |
| `--api-base URL` | LM Studio API のベース URL を指定する（デフォルト: `http://127.0.0.1:1234/v1`） |
| `--api-key KEY` | LM Studio API の認証キーを指定する（デフォルト: 環境変数 `LMSTUDIO_API_KEY`） |

```bash
# 基本: 認証キーを指定して実行
python update_opencode_models.py --api-key lms-xxxxxxxxxxxxx

# 既にモデルが登録済みでも強制的に最新化
python update_opencode_models.py --force --api-key lms-xxxxxxxxxxxxx

# カスタムポートの LM Studio に接続
python update_opencode_models.py --api-base http://127.0.0.1:5000/v1 --api-key lms-xxxxxxxxxxxxx

# 環境変数で指定
LMSTUDIO_API_BASE=http://127.0.0.1:5000/v1 LMSTUDIO_API_KEY=lms-xxxxxxxxxxxxx python update_opencode_models.py

# 全オプションを組み合わせ
python update_opencode_models.py --force --api-base http://127.0.0.1:5000/v1 --api-key lms-xxxxxxxxxxxxx
```

## 注意点

- このツールは `~/.config/opencode/opencode.jsonc` を更新します。`~/.cache/opencode/models.json` は変更しません。
- 設定更新後は **OpenCode の再起動** が必要です。
- LM Studio の API が起動していない場合、モデルの取得に失敗します（終了コード 1）。

## トラブルシューティング

### LM Studio API へのアクセスエラーが発生した場合

1. LM Studio が起動していることを確認してください
2. LM Studio の Server タブで API サーバーが起動しているか確認してください
3. 認証が有効な場合は `--api-key` を指定してください
4. デフォルトポート (1234) 以外を使用している場合は `--api-base` で指定してください

### モデルが OpenCode に表示されない場合

1. OpenCode を再起動してください
2. `~/.config/opencode/opencode.jsonc` に `lmstudio` プロバイダーが正しく登録されているか確認してください
3. `disabled_providers` に `lmstudio` が含まれていないか確認してください
