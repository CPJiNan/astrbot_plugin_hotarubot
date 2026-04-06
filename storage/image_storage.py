import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class ImageStorage:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.images_file = self.storage_path / "images.json"
        self._images = self._load_images()
        self._next_id = max(self._images.keys(), default=0) + 1

    def next_id(self) -> int:
        id = self._next_id
        self._next_id += 1
        return id

    def _load_images(self) -> Dict[int, Dict]:
        if self.images_file.exists():
            with open(self.images_file, 'r', encoding='utf-8') as f:
                try:
                    return {int(k): v for k, v in json.load(f).items()}
                except (json.JSONDecodeError, ValueError):
                    return {}
        return {}

    def _save_images(self):
        with open(self.images_file, 'w', encoding='utf-8') as f:
            json.dump(self._images, f, ensure_ascii=False, indent=2)

    def get_image_by_id(self, image_id: int) -> Optional[Dict]:
        return self._images.get(image_id)

    def get_images_by_description(self, description: str) -> List[Dict]:
        return [img for img in self._images.values() if description in img.get("description", "")]

    def get_random_image(self) -> Optional[Dict]:
        if not self._images:
            return None
        import random
        return random.choice(list(self._images.values()))

    def get_latest_image(self) -> Optional[Dict]:
        if not self._images:
            return None
        latest_id = max(self._images.keys())
        return self._images.get(latest_id)

    def upload_image(self, id: int, file: str, description: str = "", uploader: int = -1) -> Dict:
        image = {
            "id": id,
            "file": file,
            "description": description,
            "uploader": uploader,
            "uploadTime": int(time.time() * 1000)
        }
        self._images[id] = image
        self._save_images()
        return image

    def set_image_description(self, image_id: int, description: str) -> Optional[Dict]:
        if image_id in self._images:
            self._images[image_id]["description"] = description
            self._save_images()
            return self._images[image_id]
        return None

    def get_count(self) -> int:
        return len(self._images)
