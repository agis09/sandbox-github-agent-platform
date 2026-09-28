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

## Space Invaders（ターミナル版）

`curses` を使った最小構成のターミナル版スペースインベーダー。ロジックは純粋な関数群（`GameState` / `new_game` / `move_player` / `shoot` / `tick` / `render`）で書かれており、stdlib のみで動きます。

```bash
python3 invaders_game.py
```

### 操作

- 移動: ← / → または `a` / `d`
- 発砲: スペース（同時に発射できる弾は 1 発まで）
- 終了: `q`

### ルール

- 撃墜した敵 1 体につき 10 点。
- 敵は一定の刻みで下に進み、プレイヤーの行に達するとゲームオーバー。
- 全敵を撃破すると勝利。

ロジックのテストは `python3 -m unittest discover`（または `test_invaders_game.py`）で実行できます。
