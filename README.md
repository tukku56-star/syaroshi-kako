# 社労士過去問 Android アプリ

このリポジトリは `sharousi_app`（Android アプリ）専用です。  
付箋出題、弱点出題、年度フィルタを含む学習機能を実装しています。

## ディレクトリ構成

- `sharousi_app/` Android Studio プロジェクト本体

## 主な機能

- 一問一答（科目・年度・難易度フィルタ）
- 付箋出題
- 弱点出題
- 検索出題
- 実践テスト（ランダム）
- 解答履歴・学習統計
- `付箋出題.md` / `弱点出題.md` からの履歴初期インポート

## セットアップ

1. Android Studio で `sharousi_app` を開く
2. `local.properties` に Android SDK パスを設定
3. ビルド実行

```bash
cd sharousi_app
./gradlew :app:assembleDebug
```

## デバッグインストール

```bash
cd sharousi_app
./gradlew :app:installDebug
```

## データ

- 問題データ: `sharousi_app/app/src/main/assets/questions.json.gz`
- 付箋履歴: `sharousi_app/app/src/main/assets/付箋出題.md`
- 弱点履歴: `sharousi_app/app/src/main/assets/弱点出題.md`

