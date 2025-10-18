#!/usr/bin/env python3
"""
OBS Backup Tool - Complete backup solution including media files
"""

import os
import json
import shutil
import zipfile
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
import hashlib


class OBSBackupTool:
    def __init__(self, custom_obs_path: Optional[str] = None):
        if custom_obs_path:
            self.obs_config_path = Path(custom_obs_path)
            if not self.obs_config_path.exists():
                print(f"Warning: Custom OBS path does not exist: {custom_obs_path}")
        else:
            self.obs_config_path = self._find_obs_config_path()
        self.media_files = set()
        self.processed_files = set()
        
    def _find_obs_config_path(self) -> Path:
        """Find OBS configuration directory based on OS"""
        home = Path.home()
        
        # Windows paths
        possible_paths = [
            home / "AppData" / "Roaming" / "obs-studio",
            home / "AppData" / "Roaming" / "obs-studio-portable",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        # Default to standard Windows path
        return home / "AppData" / "Roaming" / "obs-studio"
    
    def set_obs_path(self, path: str) -> bool:
        """Set custom OBS configuration path"""
        new_path = Path(path)
        if new_path.exists():
            self.obs_config_path = new_path
            return True
        return False
    
    def _extract_file_paths_from_json(self, data: dict) -> Set[str]:
        """Recursively extract file paths from JSON data"""
        files = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Common keys that contain file paths in OBS
                if key in ["file", "path", "local_file", "image_file", "video", "url"]:
                    if isinstance(value, str) and os.path.exists(value):
                        files.add(value)
                elif key == "settings" and isinstance(value, dict):
                    # Special handling for source settings
                    if "file" in value and isinstance(value["file"], str):
                        if os.path.exists(value["file"]):
                            files.add(value["file"])
                    if "local_file" in value and isinstance(value["local_file"], bool) and value["local_file"]:
                        if "url" in value and isinstance(value["url"], str):
                            if os.path.exists(value["url"]):
                                files.add(value["url"])
                    files.update(self._extract_file_paths_from_json(value))
                else:
                    files.update(self._extract_file_paths_from_json(value))
        elif isinstance(data, list):
            for item in data:
                files.update(self._extract_file_paths_from_json(item))
                
        return files
    
    def _collect_scene_collection_files(self, collection_name: str) -> Set[str]:
        """Collect all media files referenced in a scene collection"""
        files = set()
        scene_file = self.obs_config_path / "basic" / "scenes" / f"{collection_name}.json"
        
        if not scene_file.exists():
            print(f"Warning: Scene collection file not found: {scene_file}")
            return files
            
        try:
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
                files.update(self._extract_file_paths_from_json(scene_data))
        except Exception as e:
            print(f"Error reading scene collection: {e}")
            
        return files
    
    def _collect_profile_files(self, profile_name: str) -> Set[str]:
        """Collect all media files referenced in a profile"""
        files = set()
        profile_dir = self.obs_config_path / "basic" / "profiles" / profile_name
        
        if not profile_dir.exists():
            print(f"Warning: Profile directory not found: {profile_dir}")
            return files
            
        # Check stream encoder settings
        for settings_file in profile_dir.glob("*.json"):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    files.update(self._extract_file_paths_from_json(data))
            except Exception as e:
                print(f"Error reading {settings_file}: {e}")
                
        return files
    
    def create_backup(self, output_path: str, 
                     scene_collections: Optional[List[str]] = None,
                     profiles: Optional[List[str]] = None) -> bool:
        """Create a complete backup including configuration and media files"""
        
        backup_name = f"obs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        backup_path = Path(output_path) / backup_name
        
        print(f"Creating backup: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Backup basic configuration
                basic_dir = self.obs_config_path / "basic"
                if basic_dir.exists():
                    for root, dirs, files in os.walk(basic_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arc_name = file_path.relative_to(self.obs_config_path)
                            backup_zip.write(file_path, arc_name)
                            print(f"Added config: {arc_name}")
                
                # Collect media files from scene collections
                all_media_files = set()
                
                if scene_collections:
                    for collection in scene_collections:
                        all_media_files.update(self._collect_scene_collection_files(collection))
                else:
                    # Backup all scene collections
                    scenes_dir = self.obs_config_path / "basic" / "scenes"
                    if scenes_dir.exists():
                        for scene_file in scenes_dir.glob("*.json"):
                            collection_name = scene_file.stem
                            all_media_files.update(self._collect_scene_collection_files(collection_name))
                
                # Collect media files from profiles
                if profiles:
                    for profile in profiles:
                        all_media_files.update(self._collect_profile_files(profile))
                else:
                    # Backup all profiles
                    profiles_dir = self.obs_config_path / "basic" / "profiles"
                    if profiles_dir.exists():
                        for profile_dir in profiles_dir.iterdir():
                            if profile_dir.is_dir():
                                all_media_files.update(self._collect_profile_files(profile_dir.name))
                
                # Add media files to backup
                media_info = {}
                for media_file in all_media_files:
                    try:
                        media_path = Path(media_file)
                        if media_path.exists() and media_path.is_file():
                            # Calculate hash for deduplication
                            file_hash = self._calculate_file_hash(media_path)
                            arc_name = f"media/{file_hash}/{media_path.name}"
                            
                            # Store mapping for restore
                            media_info[str(media_path)] = arc_name
                            
                            # Add file to zip
                            backup_zip.write(media_path, arc_name)
                            print(f"Added media: {media_path.name}")
                    except Exception as e:
                        print(f"Error adding media file {media_file}: {e}")
                
                # Save media mapping info
                media_info_json = json.dumps(media_info, indent=2)
                backup_zip.writestr("media_mapping.json", media_info_json)
                
                # Save backup metadata
                metadata = {
                    "backup_date": datetime.now().isoformat(),
                    "obs_config_path": str(self.obs_config_path),
                    "total_media_files": len(all_media_files),
                    "scene_collections": scene_collections or "all",
                    "profiles": profiles or "all"
                }
                backup_zip.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
                
            print(f"Backup completed successfully: {backup_path}")
            print(f"Total media files backed up: {len(all_media_files)}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_backup(self, backup_path: str, restore_media: bool = True) -> bool:
        """Restore OBS configuration and media files from backup"""
        
        if not Path(backup_path).exists():
            print(f"Error: Backup file not found: {backup_path}")
            return False
            
        print(f"Restoring from backup: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Read metadata
                try:
                    metadata = json.loads(backup_zip.read("backup_metadata.json"))
                    print(f"Backup created: {metadata['backup_date']}")
                    print(f"Media files in backup: {metadata['total_media_files']}")
                except:
                    print("Warning: No metadata found in backup")
                
                # Read media mapping
                media_mapping = {}
                try:
                    media_mapping = json.loads(backup_zip.read("media_mapping.json"))
                except:
                    print("Warning: No media mapping found in backup")
                
                # Create backup of current configuration
                current_backup = self.obs_config_path.parent / f"obs-studio_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if self.obs_config_path.exists():
                    print(f"Backing up current configuration to: {current_backup}")
                    shutil.copytree(self.obs_config_path, current_backup)
                
                # Extract configuration files
                config_files = [f for f in backup_zip.namelist() 
                              if f.startswith("basic/") and not f.startswith("media/")]
                
                for file_name in config_files:
                    target_path = self.obs_config_path / file_name
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    data = backup_zip.read(file_name)
                    with open(target_path, 'wb') as f:
                        f.write(data)
                    print(f"Restored config: {file_name}")
                
                # Restore media files if requested
                if restore_media and media_mapping:
                    print("Restoring media files...")
                    
                    # Create a reverse mapping from archive path to original path
                    reverse_mapping = {v: k for k, v in media_mapping.items()}
                    
                    media_files = [f for f in backup_zip.namelist() if f.startswith("media/")]
                    for arc_path in media_files:
                        if arc_path in reverse_mapping:
                            original_path = Path(reverse_mapping[arc_path])
                            
                            # Create directory if needed
                            original_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Extract file
                            data = backup_zip.read(arc_path)
                            with open(original_path, 'wb') as f:
                                f.write(data)
                            print(f"Restored media: {original_path.name} -> {original_path}")
                
                print("Restore completed successfully!")
                return True
                
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of a file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]  # Use first 16 chars for brevity
    
    def list_scene_collections(self) -> List[str]:
        """List all available scene collections"""
        scenes_dir = self.obs_config_path / "basic" / "scenes"
        if not scenes_dir.exists():
            return []
        
        collections = []
        for scene_file in scenes_dir.glob("*.json"):
            collections.append(scene_file.stem)
        
        return collections
    
    def list_profiles(self) -> List[str]:
        """List all available profiles"""
        profiles_dir = self.obs_config_path / "basic" / "profiles"
        if not profiles_dir.exists():
            return []
            
        profiles = []
        for profile_dir in profiles_dir.iterdir():
            if profile_dir.is_dir():
                profiles.append(profile_dir.name)
                
        return profiles


def main():
    parser = argparse.ArgumentParser(description="OBS Backup Tool - Complete backup including media files")
    parser.add_argument('--obs-path', help='Custom OBS configuration directory path')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create a backup')
    backup_parser.add_argument('-o', '--output', default='.', help='Output directory for backup')
    backup_parser.add_argument('-s', '--scenes', nargs='*', help='Specific scene collections to backup (default: all)')
    backup_parser.add_argument('-p', '--profiles', nargs='*', help='Specific profiles to backup (default: all)')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_file', help='Path to backup file')
    restore_parser.add_argument('--no-media', action='store_true', help='Skip restoring media files')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List scene collections and profiles')
    
    args = parser.parse_args()
    
    tool = OBSBackupTool(args.obs_path if hasattr(args, 'obs_path') else None)
    
    if args.command == 'backup':
        tool.create_backup(args.output, args.scenes, args.profiles)
        
    elif args.command == 'restore':
        tool.restore_backup(args.backup_file, not args.no_media)
        
    elif args.command == 'list':
        print("\nOBS Configuration path:", tool.obs_config_path)
        
        print("\nScene Collections:")
        collections = tool.list_scene_collections()
        if collections:
            for collection in collections:
                print(f"  - {collection}")
        else:
            print("  No scene collections found")
            
        print("\nProfiles:")
        profiles = tool.list_profiles()
        if profiles:
            for profile in profiles:
                print(f"  - {profile}")
        else:
            print("  No profiles found")
            
    else:
        parser.print_help()


if __name__ == "__main__":
    main()