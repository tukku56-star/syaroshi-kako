# drrrkari.com（デュラチャ）技術仕様

---

## 1. ログイン画面構成
- **HTML**: 静的ページ。ユーザーはアイコン選択と名前入力（最大34文字）を行う。
- **隠しフィールド**: `language=ja-JP` と選択したアイコンの値。
- **送信ボタン**: `<a>` 要素に `onclick="document.loginForm.submit()"` を付与し、フォーム送信。
- **CSRF 対策**: トークンが hidden フィールドとして埋め込まれる。

## 2. ログイン処理（サーバ側）
- **ルーティング**: `Dura_Controller_Default` にリクエストが振り分けられる。
- **既存セッション**: ある場合はラウンジへリダイレクト。
- **新規ログイン**: `_login()` が呼ばれ、以下を検証:
  - 名前の空白・文字数制限
  - CSRF トークンの有効性
  - アイコンが存在しない場合はデフォルトアイコンへ置換
- **ユーザー情報保存**: `Dura_Class_User::login()` が実行され、以下がセッションに格納される:
  - `name`, `icon`, `id`, `language`, `admin_flag`
- **ID 生成**: `md5(name + REMOTE_ADDR)`（IP アドレスはハッシュ化）

## 3. ラウンジ画面（部屋一覧）
- **コントローラ**: `Dura_Controller_Lounge`
- **部屋情報取得**: `Dura_Model_RoomHandler::loadAll()` が `trust_path/xml` 配下の `room_<id>.xml` を走査し、期限切れ（`DURA_CHAT_ROOM_EXPIRE`、デフォルト30分）を除外。
- **テンプレート**: `lounge.default.php`
  - 部屋名、作成者、現在人数/定員を表示
  - 定員未満の部屋に「入室」ボタンを出力（POST で `room` コントローラへ ID 送信）
- **部屋情報保存**: 各部屋は XML ファイル `room_<id>.xml` に以下を保持:
  - `<name>`, `<update>`, `<limit>`, `<host>`, `<language>`
  - `<users>`（ユーザーリスト）
  - `<talks>`（チャット履歴）

## 4. チャットルーム内処理
### 入室 (`room` コントローラ `_login()`)
- XML を読み込み、定員チェックと同名・同アイコンの重複チェック。
- `<users>` に `<user>` エントリ (`name`, `id`, `icon`, `update`) を追加。
- 期限切れユーザーは削除し、ホストが不在の場合は次のユーザーへホスト権限を移譲。

### メッセージ送信 (`_message()`)
- POST データを受け取り、`<talks>` に `<talk>` を追加:
  - `id`（一意）、`uid`（ユーザーID）、`name`, `message`, `icon`, `time`
- `DURA_LOG_LIMIT`（標準25件）を超えると古いエントリを削除。
- 通常はページリロード、AJAX モードでは即時レスポンスでページ遷移なし。

### 退室・ホスト交代・追放
- `_logout()`：自分の `<user>` エントリを削除。部屋が空になると XML ファイル自体を削除。
- `_moveHostRight()`：ホストが退室した際に `<users>` の先頭ユーザーへ権限移譲し、システムメッセージを追加。
- `_banUser()`（ホスト専用）：対象ユーザーをリストから削除し、`Banned {1}.` をログに記録。

## 5. データ構造・保存形式
- **部屋 XML** (`room_<id>.xml`):
  ```xml
  <room>
    <name>...</name>
    <update>timestamp</update>
    <limit>max_users</limit>
    <host>user_id</host>
    <language>ja-JP</language>
    <users>
      <user>
        <name>...</name>
        <id>md5(name+IP)</id>
        <icon>...</icon>
        <update>timestamp</update>
      </user>
      ...
    </users>
    <talks>
      <talk>
        <id>unique</id>
        <uid>user_id</uid>
        <name>...</name>
        <message>...</message>
        <icon>...</icon>
        <time>timestamp</time>
      </talk>
      ...
    </talks>
  </room>
  ```
- **セッション**: PHP セッションに `user` オブジェクト（名前・アイコン・ID・言語・admin）と `room` 配列（入室中の部屋 ID）を保持。
- **ID 生成**: `md5(name + REMOTE_ADDR)` により匿名性と同一ユーザーの再認識を実現。

## 6. クライアント側動作
- **テンプレート `theme.php`**: jQuery、言語翻訳、`jquery.chat.js` を読み込む。
- **`jquery.chat.js`**:
  - `postAction` = `duraUrl + '/ajax.php?ajax=1'` で非同期 POST（メッセージ送信）。
  - `getAction` = `duraUrl + '/ajax.php?fast=1'` を 1.5 秒間隔でポーリングし、部屋更新を取得。
  - `useComet = 1` の場合は長時間ポーリングでサーバ側ファイル更新を待機。
  - 受信データは **XML**（`<room>` 以下に `<users>` と `<talks>`）で、jQuery の `.find()` で要素抽出し DOM に反映。
  - メッセージ重複防止、文字数上限 (`GlobalMessageMaxLength`) 超過時は省略 (`...`)。
  - UI 更新は `updateProccess()` がタイムスタンプ変化時に実行し、最新メッセージは `prepend()`、最大 50 件保持。
  - `writeUserList()` がユーザーリストとホスト権限ボタンを更新。クリックで名前をテキストエリアへ挿入、音声通知 (`jquery.sound.js`) も実装。

## 7. ネットワーク上のデータ形式
- **`ajax.php` のレスポンス**: XML（JSON ではない）。構造は:
  ```xml
  <room>
    <name>...</name>
    <update>...</update>
    <limit>...</limit>
    <host>...</host>
    <language>...</language>
    <users>...</users>
    <talks>...</talks>
    <error>code</error>
  </room>
  ```
- **エラーコード**:
  - `1`: セッションに部屋 ID が無い
  - `2`: 部屋が存在しない
  - `3`: ログインしていない
- **クライアント側**は XML をそのまま解析し、JSON 変換は行わない。

---

**備考**: 本システムはデータベースを使用せず、サーバ側ファイルシステム（XML）で状態管理を行うことで、ファイル更新タイムスタンプとハッシュを利用したリアルタイムチャットを実現しています。
