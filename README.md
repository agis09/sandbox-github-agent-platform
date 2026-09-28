# sandbox-github-agent-platform

agent-platform の E2E / k3s PoC で使用する **sandbox fixture リポジトリ**。
社内コード・実 Issue 文面は置かない。小さな Python CLI をサンプルアプリとして同梱する。

## アプリの実行

```bash
python3 sandbox_app.py --name world
python3 sandbox_app.py --name fixture --json
python3 -m pytest test_sandbox_app.py
```

## 用途

- `agentctl plan / execute / publish / review` の対象（公開 github.com）
- Reader App / Publisher App（最小権限、この repo のみにインストール）
