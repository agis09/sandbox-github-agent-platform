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

## Invaders（ミニゲーム）

標準ライブラリのみで動く、端末版 Space Invaders。ロジックは `Game` クラスに集約されており、端末なしで単体テストできる。

```bash
python3 invaders.py
```

操作キー:

| キー | 動作 |
| --- | --- |
| `←` / `h` | 左に移動 |
| `→` / `l` | 右に移動 |
| `Space` / `j` | 発砲 |
| `q` | 終了 |
| `r` | ゲームオーバー画面でのリスタート |

- 画面上部の固定行にスコアを表示（敵を撃破すると 10 点加算）
- 敵がプレイヤーの行に到達すると GAME OVER（`r` でリスタート、`q` で終了）
- ロジックの単体テスト: `python3 -m unittest test_invaders -v`
