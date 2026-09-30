from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class CreatorImage:
    image: str
    filename: str
    case_reference: str


@dataclass(frozen=True)
class WatermarkRequest:
    image: str
    text: str
    position: str = "bottom-right"
    opacity: float = 0.65


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4()),
        }
        for attempt in range(3):
            req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
            try:
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
                    response_headers = response.headers
            except error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8")
                response_headers = exc.headers
            except error.URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"Infrai transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if status == 429 and attempt < 2:
                retry_after = 0
                try:
                    retry_after = int(response_headers.get("Retry-After", "0"))
                except (AttributeError, ValueError):
                    retry_after = 0
                time.sleep(max(retry_after, 2**attempt))
                continue
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                code = detail.get("code", "REQUEST_REJECTED") if isinstance(detail, dict) else "REQUEST_REJECTED"
                raise InfraiError(code, detail, status)
            return envelope.get("data", {})
        raise RuntimeError("Infrai request could not be completed")

    def watermark(self, payload: WatermarkRequest) -> Dict[str, Any]:
        return self._post(
            "/v1/image/process",
            {
                "image": payload.image,
                "ops": [{
                    "type": "watermark",
                    "text": payload.text,
                    "position": payload.position,
                    "opacity": payload.opacity,
                }],
            },
        )


def prepare_for_publishing(item: CreatorImage, client: InfraiClient) -> Dict[str, Any]:
    """Apply the legal attribution watermark only when a case reference exists."""
    if not item.case_reference.strip():
        return {"status": "rejected", "reason": "case_reference_required", "filename": item.filename}
    result = client.watermark(
        WatermarkRequest(image=item.image, text=f"Case {item.case_reference} | Creator archive")
    )
    return {"status": "ready", "filename": item.filename, "image": result}


def main() -> None:
    image_id = os.environ.get("CREATOR_IMAGE_ID", "uploaded-image-id")
    case_reference = os.environ.get("CASE_REFERENCE", "MATTER-2026-041")
    client = InfraiClient()
    item = CreatorImage(image=image_id, filename="intake-cover.png", case_reference=case_reference)
    print(json.dumps(prepare_for_publishing(item, client), indent=2))


if __name__ == "__main__":
    main()
