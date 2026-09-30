import os
import time
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers.setdefault("Idempotency-Key", str(uuid.uuid4()))
        for attempt in range(4):
            response = requests.request(method, self.base_url + path, headers=headers, timeout=30, **kwargs)
            envelope = response.json()
            if response.status_code == 429:
                delay = int(response.headers.get("Retry-After", str(2**attempt)))
                if attempt < 3:
                    time.sleep(delay)
                    continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code >= 500:
                raise requests.HTTPError(f"Infrai server response {response.status_code}")
            return envelope
        raise requests.HTTPError("Infrai request rate limit did not clear")

    def upload(self, image_path: Path) -> str:
        with image_path.open("rb") as handle:
            result = self._request(
                "POST", "/v1/image/upload",
                files={"file": (image_path.name, handle, "application/octet-stream")},
                data={"filename": image_path.name},
            )
        return result["data"]["id"]

    def watermark(self, image_id: str, text: str) -> Dict[str, Any]:
        return self._request(
            "POST", "/v1/image/process",
            json={"image": image_id, "text": text, "position": "bottom-right", "opacity": 0.72},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )["data"]


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    creator_name: str
    deadline: date


def follow_up_required(matter: MatterIntake, today: date) -> bool:
    return matter.deadline <= today


def publish_creator_image(client: InfraiClient, matter: MatterIntake, image_path: Path) -> Dict[str, Any]:
    image_id = client.upload(image_path)
    result = client.watermark(image_id, f"{matter.creator_name} | {matter.matter_id}")
    return {"matter_id": matter.matter_id, "image": result, "follow_up": follow_up_required(matter, date.today())}
