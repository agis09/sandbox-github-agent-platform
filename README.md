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

## インベイドゲーム（`invader_game.py`）

標準ライブラリのみで書かれたターミナル版スペースインベーダ。ゲームロジック（`Game` クラス）は I/O と分離されており、テストが端末なしに実行できます。

### 実行方法

```bash
python invader_game.py
```

インタラクティブなターミナル（`stdin` が TTY）で直接実行してください。非 TTY 環境ではヘルプメッセージを表示して終了します。

### 操作方法

| キー | 動作 |
| --- | --- |
| ← / a | 左に移動 |
| → / d | 右に移動 |
| スペース | 射撃（同時に 1 発まで） |
| q | 終了 |
| r | ゲームオーバー後にリスタート |

### スコアとゲームオーバー

- 敵 1 体撃破ごとに 10 点加算
- 敵弾で被弾するとライフ 1（初期 3）を減らし、0 になるとゲームオーバー
- 敵編隊が最下段（プレイヤーの行）まで降下するとゲームオーバー
- 敵を全滅させると勝利

### テスト

ゲームロジックのユニットテスト（`unittest`）は以下で実行します。

```bash
python -m unittest discover
```
