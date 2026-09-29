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

## Invaders game

標準ライブラリのみで動作するターミナル版 Invaders。
ロジックは `invaders_game.py`（純粋関数・端末非依存）、CLI は `invaders_cli.py`。

### 実行

```bash
python3 invaders_cli.py
python3 -m invaders_cli
python3 invaders_cli.py --ticks 30   # 非対話スモークラン（N フレームで終了）
```

curses が使える TTY では curses レンダラ、それ以外（CI / 非 TTY など）は
plain ANSI レンダラに自動フォールバック（`--renderer curses|ansi` で指定可）。

### 操作

- 移動: ←/→ または `h`/`l`
- 射撃: スペースまたは `j`
- 終了: `q`

### ルール

- 敵 1 体撃破で +10 点（スコアは画面上部に表示）
- 残機 3。敵弾に撃たれると残機 1 減り、敵陣・弾が初期状態に戻る
- 敵が最下段（プレイヤー行）に到達するか残機が 0 になると GAME OVER
- 敵を全滅させれば VICTORY

### テスト

ゲームロジックは端末に依存しないため、ヘッドレスで検証できる:

```bash
python3 -m unittest discover
```
