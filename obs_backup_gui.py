#!/usr/bin/env python3
"""
OBS Backup Tool - GUI Version
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import sys
import json
from datetime import datetime
import os

# Import the backup tool
from obs_backup_tool import OBSBackupTool


class OBSBackupGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OBS Backup Tool")
        self.root.geometry("800x650")
        
        # Set icon if available
        self.root.resizable(True, True)
        
        # Load saved configuration
        self.config_file = Path("config.json")
        self.app_config = self.load_app_config()
        
        # Initialize tool with saved OBS path if available
        custom_obs_path = self.app_config.get("obs_config_path")
        self.tool = OBSBackupTool(custom_obs_path)
        
        # Variables
        default_backup_dir = self.app_config.get("default_backup_dir", str(Path.home() / "Desktop"))
        self.backup_output_dir = tk.StringVar(value=default_backup_dir)
        self.obs_config_path = tk.StringVar(value=str(self.tool.obs_config_path))
        self.selected_scenes = []
        self.selected_profiles = []
        
        self.setup_ui()
        self.load_configurations()
        
        # Save config on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Setup the main UI"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Backup tab
        self.backup_frame = ttk.Frame(notebook)
        notebook.add(self.backup_frame, text="バックアップ")
        self.setup_backup_tab()
        
        # Restore tab
        self.restore_frame = ttk.Frame(notebook)
        notebook.add(self.restore_frame, text="リストア")
        self.setup_restore_tab()
        
        # Log tab
        self.log_frame = ttk.Frame(notebook)
        notebook.add(self.log_frame, text="ログ")
        self.setup_log_tab()
        
    def setup_backup_tab(self):
        """Setup backup tab UI"""
        # Title
        title = ttk.Label(self.backup_frame, text="OBSバックアップ作成", font=("", 14, "bold"))
        title.pack(pady=10)
        
        # Configuration info
        info_frame = ttk.LabelFrame(self.backup_frame, text="OBS設定情報", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # OBS config path with browse button
        path_frame = ttk.Frame(info_frame)
        path_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(path_frame, text="設定パス:").pack(side=tk.LEFT, padx=(0, 5))
        self.config_path_entry = ttk.Entry(path_frame, textvariable=self.obs_config_path, width=50)
        self.config_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="変更...", command=self.browse_obs_config).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(path_frame, text="デフォルト", command=self.reset_obs_config).pack(side=tk.LEFT, padx=(5, 0))
        
        # Scene Collections selection
        scenes_frame = ttk.LabelFrame(self.backup_frame, text="シーンコレクション", padding=10)
        scenes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Listbox with scrollbar for scenes
        scenes_scroll = ttk.Scrollbar(scenes_frame)
        scenes_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.scenes_listbox = tk.Listbox(scenes_frame, selectmode=tk.MULTIPLE, height=6,
                                         yscrollcommand=scenes_scroll.set)
        self.scenes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scenes_scroll.config(command=self.scenes_listbox.yview)
        
        # Select all/none buttons for scenes
        scenes_btn_frame = ttk.Frame(scenes_frame)
        scenes_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(scenes_btn_frame, text="すべて選択", 
                  command=lambda: self.select_all(self.scenes_listbox)).pack(side=tk.LEFT, padx=2)
        ttk.Button(scenes_btn_frame, text="選択解除", 
                  command=lambda: self.clear_selection(self.scenes_listbox)).pack(side=tk.LEFT, padx=2)
        
        # Profiles selection
        profiles_frame = ttk.LabelFrame(self.backup_frame, text="プロファイル", padding=10)
        profiles_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Listbox with scrollbar for profiles
        profiles_scroll = ttk.Scrollbar(profiles_frame)
        profiles_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.profiles_listbox = tk.Listbox(profiles_frame, selectmode=tk.MULTIPLE, height=6,
                                           yscrollcommand=profiles_scroll.set)
        self.profiles_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        profiles_scroll.config(command=self.profiles_listbox.yview)
        
        # Select all/none buttons for profiles
        profiles_btn_frame = ttk.Frame(profiles_frame)
        profiles_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(profiles_btn_frame, text="すべて選択", 
                  command=lambda: self.select_all(self.profiles_listbox)).pack(side=tk.LEFT, padx=2)
        ttk.Button(profiles_btn_frame, text="選択解除", 
                  command=lambda: self.clear_selection(self.profiles_listbox)).pack(side=tk.LEFT, padx=2)
        
        # Output directory selection
        output_frame = ttk.Frame(self.backup_frame)
        output_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(output_frame, text="保存先:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(output_frame, textvariable=self.backup_output_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="参照...", command=self.browse_output_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # Create backup button
        self.backup_button = ttk.Button(self.backup_frame, text="バックアップ作成", 
                                       command=self.create_backup, style="Accent.TButton")
        self.backup_button.pack(pady=20)
        
        # Progress bar
        self.backup_progress = ttk.Progressbar(self.backup_frame, mode='indeterminate')
        self.backup_progress.pack(fill=tk.X, padx=20, pady=(0, 20))
        
    def setup_restore_tab(self):
        """Setup restore tab UI"""
        # Title
        title = ttk.Label(self.restore_frame, text="OBSバックアップ復元", font=("", 14, "bold"))
        title.pack(pady=10)
        
        # Backup file selection
        file_frame = ttk.LabelFrame(self.restore_frame, text="バックアップファイル", padding=10)
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.restore_file_path = tk.StringVar()
        
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X)
        
        ttk.Entry(file_select_frame, textvariable=self.restore_file_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_select_frame, text="ファイル選択...", command=self.browse_backup_file).pack(side=tk.LEFT, padx=(5, 0))
        
        # Backup info display
        self.backup_info_frame = ttk.LabelFrame(self.restore_frame, text="バックアップ情報", padding=10)
        self.backup_info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.backup_info_text = tk.Text(self.backup_info_frame, height=6, width=60, state=tk.DISABLED)
        self.backup_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Restore options
        options_frame = ttk.LabelFrame(self.restore_frame, text="復元オプション", padding=10)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.restore_media_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="メディアファイルも復元する", 
                       variable=self.restore_media_var).pack(anchor=tk.W)
        
        # Warning message
        warning_frame = ttk.Frame(self.restore_frame)
        warning_frame.pack(fill=tk.X, padx=20, pady=10)
        
        warning_text = "⚠️ 注意: 復元を実行すると現在のOBS設定が上書きされます。\n現在の設定は自動的にバックアップされます。"
        ttk.Label(warning_frame, text=warning_text, foreground="orange").pack()
        
        # Restore button
        self.restore_button = ttk.Button(self.restore_frame, text="復元実行", 
                                        command=self.restore_backup, style="Accent.TButton")
        self.restore_button.pack(pady=20)
        
        # Progress bar
        self.restore_progress = ttk.Progressbar(self.restore_frame, mode='indeterminate')
        self.restore_progress.pack(fill=tk.X, padx=20, pady=(0, 20))
        
    def setup_log_tab(self):
        """Setup log tab UI"""
        # Title
        title = ttk.Label(self.log_frame, text="実行ログ", font=("", 14, "bold"))
        title.pack(pady=10)
        
        # Log text area
        log_container = ttk.Frame(self.log_frame)
        log_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_container, height=20, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Clear button
        ttk.Button(self.log_frame, text="ログクリア", command=self.clear_log).pack(pady=10)
        
    def load_configurations(self):
        """Load available scene collections and profiles"""
        # Clear existing items
        self.scenes_listbox.delete(0, tk.END)
        self.profiles_listbox.delete(0, tk.END)
        
        # Load scene collections
        scenes = self.tool.list_scene_collections()
        for scene in scenes:
            self.scenes_listbox.insert(tk.END, scene)
        
        # Load profiles
        profiles = self.tool.list_profiles()
        for profile in profiles:
            self.profiles_listbox.insert(tk.END, profile)
            
        # Select all by default
        self.select_all(self.scenes_listbox)
        self.select_all(self.profiles_listbox)
        
    def select_all(self, listbox):
        """Select all items in a listbox"""
        listbox.select_set(0, tk.END)
        
    def clear_selection(self, listbox):
        """Clear all selections in a listbox"""
        listbox.select_clear(0, tk.END)
        
    def browse_obs_config(self):
        """Browse for OBS configuration directory"""
        directory = filedialog.askdirectory(
            title="OBS設定ディレクトリを選択（通常はobs-studioフォルダ）",
            initialdir=self.obs_config_path.get()
        )
        if directory:
            # Validate if it looks like an OBS config directory
            path = Path(directory)
            if (path / "basic").exists() or messagebox.askyesno(
                "確認",
                f"選択したディレクトリに'basic'フォルダが見つかりません。\n"
                f"本当にこのディレクトリを使用しますか？\n\n{directory}"
            ):
                if self.tool.set_obs_path(directory):
                    self.obs_config_path.set(directory)
                    self.load_configurations()
                    self.log(f"OBS設定パスを変更しました: {directory}")
                    self.save_app_config()  # Save the new path
                else:
                    messagebox.showerror("エラー", "指定されたディレクトリは存在しません")
    
    def reset_obs_config(self):
        """Reset OBS configuration path to default"""
        default_tool = OBSBackupTool()  # Create new instance with default path
        default_path = str(default_tool.obs_config_path)
        self.tool.set_obs_path(default_path)
        self.obs_config_path.set(default_path)
        self.load_configurations()
        self.log(f"OBS設定パスをデフォルトに戻しました: {default_path}")
    
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="バックアップ保存先を選択",
            initialdir=self.backup_output_dir.get()
        )
        if directory:
            self.backup_output_dir.set(directory)
            
    def browse_backup_file(self):
        """Browse for backup file to restore"""
        filename = filedialog.askopenfilename(
            title="バックアップファイルを選択",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
            initialdir=str(Path.home() / "Desktop")
        )
        if filename:
            self.restore_file_path.set(filename)
            self.load_backup_info(filename)
            
    def load_backup_info(self, backup_path):
        """Load and display backup file information"""
        try:
            import zipfile
            with zipfile.ZipFile(backup_path, 'r') as zf:
                if "backup_metadata.json" in zf.namelist():
                    metadata = json.loads(zf.read("backup_metadata.json"))
                    
                    info_text = f"バックアップ日時: {metadata.get('backup_date', '不明')}\n"
                    info_text += f"メディアファイル数: {metadata.get('total_media_files', 0)}\n"
                    info_text += f"シーンコレクション: {metadata.get('scene_collections', 'all')}\n"
                    info_text += f"プロファイル: {metadata.get('profiles', 'all')}\n"
                    
                    self.backup_info_text.config(state=tk.NORMAL)
                    self.backup_info_text.delete(1.0, tk.END)
                    self.backup_info_text.insert(1.0, info_text)
                    self.backup_info_text.config(state=tk.DISABLED)
                else:
                    self.log("警告: バックアップファイルにメタデータが含まれていません")
        except Exception as e:
            self.log(f"エラー: バックアップ情報の読み込みに失敗: {e}")
            
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
        
    def create_backup(self):
        """Create backup in a separate thread"""
        # Get selected items
        selected_scenes_idx = self.scenes_listbox.curselection()
        selected_scenes = [self.scenes_listbox.get(idx) for idx in selected_scenes_idx] if selected_scenes_idx else None
        
        selected_profiles_idx = self.profiles_listbox.curselection()
        selected_profiles = [self.profiles_listbox.get(idx) for idx in selected_profiles_idx] if selected_profiles_idx else None
        
        output_dir = self.backup_output_dir.get()
        
        if not Path(output_dir).exists():
            messagebox.showerror("エラー", "保存先ディレクトリが存在しません")
            return
            
        # Disable button and start progress
        self.backup_button.config(state=tk.DISABLED)
        self.backup_progress.start(10)
        
        # Create backup in thread
        def backup_thread():
            try:
                self.log("バックアップを開始します...")
                self.log(f"保存先: {output_dir}")
                
                if selected_scenes:
                    self.log(f"選択されたシーンコレクション: {', '.join(selected_scenes)}")
                else:
                    self.log("すべてのシーンコレクションをバックアップします")
                    
                if selected_profiles:
                    self.log(f"選択されたプロファイル: {', '.join(selected_profiles)}")
                else:
                    self.log("すべてのプロファイルをバックアップします")
                
                # Redirect print output to log
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    success = self.tool.create_backup(output_dir, selected_scenes, selected_profiles)
                
                # Add captured output to log
                output = f.getvalue()
                if output:
                    for line in output.strip().split('\n'):
                        self.log(line)
                
                if success:
                    self.log("✅ バックアップが正常に完了しました！")
                    messagebox.showinfo("完了", "バックアップが正常に作成されました")
                else:
                    self.log("❌ バックアップの作成に失敗しました")
                    messagebox.showerror("エラー", "バックアップの作成に失敗しました")
                    
            except Exception as e:
                self.log(f"エラー: {e}")
                messagebox.showerror("エラー", f"バックアップ作成中にエラーが発生しました:\n{e}")
            finally:
                # Re-enable button and stop progress
                self.backup_button.config(state=tk.NORMAL)
                self.backup_progress.stop()
                
        thread = threading.Thread(target=backup_thread, daemon=True)
        thread.start()
        
    def restore_backup(self):
        """Restore backup in a separate thread"""
        backup_file = self.restore_file_path.get()
        
        if not backup_file:
            messagebox.showerror("エラー", "バックアップファイルを選択してください")
            return
            
        if not Path(backup_file).exists():
            messagebox.showerror("エラー", "バックアップファイルが存在しません")
            return
            
        # Confirmation dialog
        result = messagebox.askyesno(
            "確認",
            "現在のOBS設定を上書きしてバックアップから復元しますか？\n\n現在の設定は自動的にバックアップされます。"
        )
        
        if not result:
            return
            
        restore_media = self.restore_media_var.get()
        
        # Disable button and start progress
        self.restore_button.config(state=tk.DISABLED)
        self.restore_progress.start(10)
        
        # Restore in thread
        def restore_thread():
            try:
                self.log("復元を開始します...")
                self.log(f"バックアップファイル: {backup_file}")
                self.log(f"メディアファイルの復元: {'有効' if restore_media else '無効'}")
                
                # Redirect print output to log
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    success = self.tool.restore_backup(backup_file, restore_media)
                
                # Add captured output to log
                output = f.getvalue()
                if output:
                    for line in output.strip().split('\n'):
                        self.log(line)
                
                if success:
                    self.log("✅ 復元が正常に完了しました！")
                    messagebox.showinfo("完了", "バックアップからの復元が完了しました\n\nOBSを再起動してください。")
                else:
                    self.log("❌ 復元に失敗しました")
                    messagebox.showerror("エラー", "バックアップからの復元に失敗しました")
                    
            except Exception as e:
                self.log(f"エラー: {e}")
                messagebox.showerror("エラー", f"復元中にエラーが発生しました:\n{e}")
            finally:
                # Re-enable button and stop progress
                self.restore_button.config(state=tk.NORMAL)
                self.restore_progress.stop()
                
        thread = threading.Thread(target=restore_thread, daemon=True)
        thread.start()
        
    def load_app_config(self):
        """Load application configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Create default config if it doesn't exist
        default_config = {
            "obs_config_path": None,
            "default_backup_dir": None,
            "last_used": None
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
        except:
            pass
        
        return default_config
    
    def save_app_config(self):
        """Save application configuration to file"""
        self.app_config["obs_config_path"] = self.obs_config_path.get() if self.obs_config_path.get() != str(OBSBackupTool().obs_config_path) else None
        self.app_config["default_backup_dir"] = self.backup_output_dir.get()
        self.app_config["last_used"] = datetime.now().isoformat()
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.app_config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def on_closing(self):
        """Handle window closing event"""
        self.save_app_config()
        self.root.destroy()
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()


def main():
    app = OBSBackupGUI()
    app.run()


if __name__ == "__main__":
    main()