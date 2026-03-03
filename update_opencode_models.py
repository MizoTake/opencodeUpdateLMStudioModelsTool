import os
import sys
import json
import argparse
import requests
from typing import Dict, List, Optional

# LM Studio API デフォルト設定
DEFAULT_LMSTUDIO_BASE = "http://127.0.0.1:1234/v1"

# OpenCode 設定ファイルパス
OPENCODE_CONFIG_DIR = os.path.expanduser("~/.config/opencode")
OPENCODE_CONFIG_PATH = os.path.join(OPENCODE_CONFIG_DIR, "opencode.jsonc")

# カスタムプロバイダーID
PROVIDER_ID = "lmstudio"


def create_model_entry(model_id: str, **kwargs) -> Dict:
    """opencode.jsonc 用のモデルエントリを生成する"""
    entry = {
        "name": kwargs.get("name", model_id),
        "tool_call": kwargs.get("tool_call", True),
        "temperature": kwargs.get("temperature", True),
        "cost": {
            "input": 0,
            "output": 0
        },
        "limit": {
            "context": kwargs.get("context_length", 32768),
            "output": kwargs.get("output_length", 8192)
        }
    }
    return entry


def load_opencode_config() -> Dict:
    """既存の opencode.jsonc を読み込む（なければ空の設定を返す）"""
    if not os.path.exists(OPENCODE_CONFIG_PATH):
        return {}
    try:
        with open(OPENCODE_CONFIG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        # JSONC（コメント付きJSON）の簡易対応: 行コメントを除去
        lines = []
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("//"):
                continue
            lines.append(line)
        return json.loads("\n".join(lines))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to read {OPENCODE_CONFIG_PATH}: {e}")
        return {}


def fetch_lmstudio_models(api_base: str, api_key: Optional[str] = None) -> List[Dict]:
    """LM Studioの/v1/modelsエンドポイントからモデル一覧を取得する"""
    url = f"{api_base}/models"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", [])
        elif response.status_code in (401, 403):
            print(f"Authentication failed ({response.status_code}).")
            print("LM Studio API requires an API key.")
            print("  --api-key YOUR_KEY  or  set LMSTUDIO_API_KEY environment variable")
            return []
        else:
            print(f"Failed to fetch models: {response.status_code} {response.text}")
            return []
    except requests.RequestException as e:
        print(f"Error fetching models from {url}: {e}")
        return []


def update_opencode_config(models_data: List[Dict], api_base: str) -> bool:
    """opencode.jsonc の lmstudio プロバイダーセクションを更新する"""
    config = load_opencode_config()

    # provider セクションを確保
    if "provider" not in config:
        config["provider"] = {}

    # lmstudio プロバイダー定義を構築
    provider_def = {
        "name": "LM Studio",
        "npm": "@ai-sdk/openai-compatible",
        "models": {},
        "options": {
            "baseURL": api_base
        }
    }

    # API キーは opencode.jsonc に書き込まず、環境変数 LMSTUDIO_API_KEY で管理する
    # OpenCode は env 定義に従って環境変数から自動的に読み取る
    provider_def["env"] = ["LMSTUDIO_API_KEY"]

    # モデルエントリを生成
    for model in models_data:
        model_id = model["id"]
        context_length = model.get("context_length", 32768)
        output_length = model.get("max_tokens", 8192)

        provider_def["models"][model_id] = create_model_entry(
            model_id=model_id,
            name=model.get("name", model_id),
            tool_call=model.get("tool_call", True),
            temperature=model.get("temperature", True),
            context_length=context_length,
            output_length=output_length,
        )

    config["provider"][PROVIDER_ID] = provider_def

    # disabled_providers から lmstudio を除去
    disabled = config.get("disabled_providers", [])
    if PROVIDER_ID in disabled:
        disabled.remove(PROVIDER_ID)
        config["disabled_providers"] = disabled

    # 空の disabled_providers は削除
    if not config.get("disabled_providers"):
        config.pop("disabled_providers", None)

    # 設定ディレクトリを作成
    os.makedirs(OPENCODE_CONFIG_DIR, exist_ok=True)

    # ファイルに保存
    try:
        with open(OPENCODE_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Successfully updated {OPENCODE_CONFIG_PATH}")
        return True
    except OSError as e:
        print(f"Error writing config: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch LM Studio models and register them in opencode.jsonc"
    )
    # exe（PyInstaller）実行時はデフォルトで force を有効にする
    is_frozen = getattr(sys, "frozen", False)
    parser.add_argument(
        "--force", action="store_true",
        default=is_frozen,
        help="Force update even if lmstudio models already exist in config"
            + (" (default: True in exe mode)" if is_frozen else "")
    )
    parser.add_argument(
        "--api-base",
        default=os.environ.get("LMSTUDIO_API_BASE", DEFAULT_LMSTUDIO_BASE),
        help=f"LM Studio API base URL (default: {DEFAULT_LMSTUDIO_BASE}, env: LMSTUDIO_API_BASE)"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("LMSTUDIO_API_KEY"),
        help="LM Studio API key (default: env LMSTUDIO_API_KEY)"
    )
    args = parser.parse_args()

    # 既存の設定に lmstudio モデルが存在する場合は確認
    config = load_opencode_config()
    existing_models = config.get("provider", {}).get(PROVIDER_ID, {}).get("models", {})
    if existing_models and not args.force:
        print(f"opencode.jsonc already has {len(existing_models)} lmstudio model(s)")
        print("Use --force to update")
        sys.exit(0)

    # LM Studio のモデルを取得
    print(f"Fetching models from LM Studio ({args.api_base})...")
    models_data = fetch_lmstudio_models(args.api_base, args.api_key)

    if not models_data:
        print("No models found from LM Studio")
        sys.exit(1)

    print(f"Found {len(models_data)} model(s)")

    # opencode.jsonc を更新
    if update_opencode_config(models_data, args.api_base):
        print("Update completed successfully")
        print("Restart OpenCode to apply changes.")
        sys.exit(0)
    else:
        print("Update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
