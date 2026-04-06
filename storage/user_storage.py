import json
from pathlib import Path
from typing import Dict, List, Optional


class UserStorage:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.users_file = self.storage_path / "users.json"
        self._users = self._load_users()

    def _load_users(self) -> Dict[int, Dict]:
        if self.users_file.exists():
            with open(self.users_file, 'r', encoding='utf-8') as f:
                try:
                    return {int(k): v for k, v in json.load(f).items()}
                except (json.JSONDecodeError, ValueError):
                    return {}
        return {}

    def _save_users(self):
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self._users, f, ensure_ascii=False, indent=2)

    def get_user(self, user_id: int) -> Optional[Dict]:
        return self._users.get(user_id)

    def add_user(self, user_id: int):
        if user_id not in self._users:
            self._users[user_id] = {
                "id": user_id,
                "permissions": []
            }
            self._save_users()

    def remove_user(self, user_id: int):
        if user_id in self._users:
            del self._users[user_id]
            self._save_users()

    def get_permissions(self, user_id: int) -> List[str]:
        user = self.get_user(user_id)
        return user.get("permissions", []) if user else []

    def has_permission(self, user_id: int, permission: str) -> bool:
        return permission in self.get_permissions(user_id)

    def add_permission(self, user_id: int, permission: str):
        if user_id not in self._users:
            self.add_user(user_id)
        if permission not in self._users[user_id]["permissions"]:
            self._users[user_id]["permissions"].append(permission)
            self._save_users()

    def remove_permission(self, user_id: int, permission: str):
        if user_id in self._users and permission in self._users[user_id]["permissions"]:
            self._users[user_id]["permissions"].remove(permission)
            self._save_users()
