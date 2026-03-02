# OpenCode モデルリスト仕様と対策

## 概要

OpenCode のモデルリストは `models.json` という静的ファイルで管理されている。
LM Studio 等のローカルプロバイダーについても、ローカル API からの動的取得は行われず、
ファイルに定義されたモデルのみが利用可能となる。

## 現状の仕様

### models.json の基本情報

| 項目 | 値 |
|------|------|
| パス | `~/.cache/opencode/models.json` |
| サイズ | 約 1.3 MB |
| 登録プロバイダー数 | 97 |
| 登録モデル総数 | 約 3,053 |
| OpenCode バージョン | 21 |

### モデルリストの取得方法

- **完全に静的** — `models.json` は OpenCode のリリース時にバンドルされるスナップショット
- LM Studio の `/v1/models` エンドポイントへの動的問い合わせは **行われない**
- OpenCode をアップデートしない限り、モデルリストは変わらない

### LM Studio プロバイダーの現状

```json
{
  "id": "lmstudio",
  "env": ["LMSTUDIO_API_KEY"],
  "npm": "@ai-sdk/openai-compatible",
  "api": "http://127.0.0.1:1234/v1",
  "name": "LMStudio",
  "doc": "https://lmstudio.ai/models"
}
```

登録済みモデルは **3つのみ**：

| モデル ID | 名前 | コンテキスト長 | 出力長 |
|-----------|------|--------------|--------|
| `qwen/qwen3-30b-a3b-2507` | Qwen3 30B A3B 2507 | 262,144 | 16,384 |
| `qwen/qwen3-coder-30b` | Qwen3 Coder 30B | 262,144 | 65,536 |
| `openai/gpt-oss-20b` | GPT OSS 20B | 131,072 | 32,768 |

### モデル定義のスキーマ

各モデルは以下のフィールドを持つ：

```json
{
  "id": "モデルID（プロバイダー側で認識される名前）",
  "name": "表示名",
  "family": "モデルファミリー",
  "attachment": false,
  "reasoning": false,
  "tool_call": true,
  "temperature": true,
  "knowledge": "2025-04",
  "release_date": "2025-07-30",
  "last_updated": "2025-07-30",
  "modalities": {
    "input": ["text"],
    "output": ["text"]
  },
  "open_weights": true,
  "cost": {
    "input": 0,
    "output": 0
  },
  "limit": {
    "context": 262144,
    "output": 16384
  }
}
```

### プロバイダーの仕組み

- LM Studio は `@ai-sdk/openai-compatible` パッケージ経由で通信する（OpenAI 互換 API）
- ローカル実行のため `cost` は全て `0`
- 認証キーは `LMSTUDIO_API_KEY` 環境変数（通常は不要）

## 問題点

1. **モデルリストが静的** — LM Studio にどんなモデルをダウンロードしても、`models.json` に定義がなければ OpenCode で選択できない
2. **更新頻度が低い** — OpenCode のリリースサイクルに依存するため、新しいモデルがすぐに反映されない
3. **ローカルプロバイダーとの相性が悪い** — LM Studio のようにユーザーが自由にモデルを入れ替えるユースケースに対応できていない

## 対策方法

### 対策1: models.json を手動編集する（即効性あり）

`~/.cache/opencode/models.json` を直接編集し、使いたいモデルを `lmstudio.models` に追加する。

#### 手順

1. LM Studio で使いたいモデルの情報を確認する
2. `models.json` を開き、`lmstudio.models` 内に新しいモデル定義を追加する

#### 追加するモデル定義のテンプレート

```json
{
  "id": "モデルID（LM Studioで表示されるモデル名と一致させる）",
  "name": "表示名（任意）",
  "family": "ファミリー名",
  "attachment": false,
  "reasoning": false,
  "tool_call": true,
  "temperature": true,
  "modalities": {
    "input": ["text"],
    "output": ["text"]
  },
  "open_weights": true,
  "cost": {
    "input": 0,
    "output": 0
  },
  "limit": {
    "context": 32768,
    "output": 8192
  }
}
```

#### 注意点

- `id` フィールドは **LM Studio のモデル識別子と完全に一致** させる必要がある
- `limit.context` と `limit.output` はモデルの実際の仕様に合わせる
- `tool_call` はモデルが function calling をサポートするかどうかに合わせる
- **OpenCode をアップデートすると上書きされる可能性がある**（バックアップ推奨）

#### 例: Llama 3.1 8B を追加する場合

```json
"meta-llama/llama-3.1-8b-instruct": {
  "id": "meta-llama/llama-3.1-8b-instruct",
  "name": "Llama 3.1 8B Instruct",
  "family": "llama",
  "attachment": false,
  "reasoning": false,
  "tool_call": true,
  "temperature": true,
  "modalities": {
    "input": ["text"],
    "output": ["text"]
  },
  "open_weights": true,
  "cost": {
    "input": 0,
    "output": 0
  },
  "limit": {
    "context": 131072,
    "output": 8192
  }
}
```

### 対策2: OpenCode をアップデートする

新しいバージョンで `models.json` が更新されている可能性がある。

```bash
# 最新版に更新（インストール方法による）
# 公式サイトから再ダウンロード、またはパッケージマネージャで更新
```

### 対策3: 開発元に機能要望を出す

OpenCode の GitHub リポジトリに Issue を作成し、以下を要望する：

- LM Studio 等のローカルプロバイダーについて `/v1/models` エンドポイントからモデル一覧を動的に取得する機能
- または、ユーザー定義のカスタムモデル設定ファイルのサポート

## 参考: 関連ファイル一覧

| ファイル | 説明 |
|---------|------|
| `~/.cache/opencode/models.json` | モデル定義（静的） |
| `~/.cache/opencode/package.json` | 依存パッケージ |
| `~/.cache/opencode/version` | OpenCode バージョン番号 |
| `~/AppData/Local/OpenCode/opencode-cli.exe` | CLI バイナリ（Go製, 167MB） |
| `~/.cache/opencode/node_modules/opencode-anthropic-auth/` | 認証プラグイン |
