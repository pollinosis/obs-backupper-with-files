# OBS Backup Tool

OBSの設定と画像ファイルを完全にバックアップ・リストアするツール

## 特徴

- ✅ シーンコレクションの完全バックアップ
- ✅ プロファイル設定のバックアップ
- ✅ 参照されている画像・動画ファイルも自動収集
- ✅ ZIPファイルで一括管理
- ✅ 選択的バックアップ/リストア対応

## インストール

```bash
# Pythonが必要です（3.7以上）
python --version
```

## 使い方

### GUI版（かんたん）

```bash
# GUIを起動
python obs_backup_gui.py

# またはバッチファイルをダブルクリック
run_gui.bat
```

**GUI版の新機能:**
- OBS設定パスを自由に変更可能（ポータブル版やカスタムインストールに対応）
- 設定は自動保存され、次回起動時に復元
- デフォルトボタンで標準パスに戻せます

### コマンドライン版

#### 1. 設定を確認

```bash
python obs_backup_tool.py list
```

現在のシーンコレクションとプロファイルを表示します。

#### 2. バックアップを作成

```bash
# すべてをバックアップ
python obs_backup_tool.py backup

# カスタムOBSパスを指定
python obs_backup_tool.py --obs-path "D:\OBS-Portable\config" backup

# 出力先を指定
python obs_backup_tool.py backup -o C:\Backups

# 特定のシーンコレクションのみ
python obs_backup_tool.py backup -s "配信用" "録画用"

# 特定のプロファイルのみ
python obs_backup_tool.py backup -p "高品質" "低遅延"
```

#### 3. バックアップから復元

```bash
# 完全復元（設定＋メディアファイル）
python obs_backup_tool.py restore obs_backup_20240101_120000.zip

# 設定のみ復元（メディアファイルは復元しない）
python obs_backup_tool.py restore obs_backup_20240101_120000.zip --no-media
```

## バックアップ内容

- `basic/scenes/*.json` - シーンコレクション
- `basic/profiles/*/` - プロファイル設定
- `media/` - 参照されている画像・動画ファイル
- `media_mapping.json` - メディアファイルのパス対応表
- `backup_metadata.json` - バックアップ情報

## ダウンロード

[Releases](https://github.com/yourusername/obs-backup-tool/releases)ページから最新版をダウンロード：
- `OBS-Backup-Tool.exe` - GUI版（推奨）
- `OBS-Backup-Tool-CLI.exe` - コマンドライン版

## 注意事項

- 復元前に現在の設定が自動バックアップされます
- 大量のメディアファイルがある場合、バックアップサイズが大きくなります
- OBSが起動中の場合は終了してから復元してください