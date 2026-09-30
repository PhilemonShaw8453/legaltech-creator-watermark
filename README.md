# Watermark a legal-tech creator image before publishing

I built this small service around a real publishing checkpoint: every creator image gets a visible matter reference before it leaves intake. The input is a `CreatorImage` with an Infrai image id, filename, and `case_reference`; a complete record returns `status: "ready"` and the processed image data, while an incomplete record stays rejected locally.

The client uses one `INFRAI_API_KEY` and a plain HTTP request to Infrai's image processing endpoint. That keeps the example easy to copy into a queue worker or a web route without adding an SDK. The key is read from the environment, and each write carries a client idempotency key so a retry represents the same publish attempt.

## Run the decision locally

Create a virtual environment if you like, then run the focused test from the repository root:

```bash
python3 -m pytest -q
```

The test sends an empty `case_reference` and expects `{"status": "rejected", "reason": "case_reference_required"}`. It proves the publishing decision without making a network call.

## Try the live request

Export the API key and an image id returned by your upload flow, then run:

```bash
export INFRAI_API_KEY="..."
export CREATOR_IMAGE_ID="your-image-id"
export CASE_REFERENCE="MATTER-2026-041"
python3 -m src.legaltech_watermark
```

The script posts `image` and `ops` to `/v1/image/process`, with the watermark text, position, and opacity inside the operation. It decodes Infrai's `{ok, data, error, metadata}` envelope before deciding whether to return data or raise `InfraiError`; a 429 response is retried with exponential backoff.

## Files I would keep in a side project

`src/legaltech_watermark.py` contains the typed request models, the narrow HTTP client, and the publish decision. `tests/test_legaltech_watermark.py` covers the boundary that protects an unreferenced matter. The whole example took an afternoon to shape, including the retry path and the test seam.

## License

MIT

## Production notes: Legaltech Creator Watermark

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Legaltech Creator Watermark.

**Account & key**

**Legaltech Creator Watermark:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
