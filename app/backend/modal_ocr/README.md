# Modal OCR Service

GPU-accelerated document parsing using Modal serverless infrastructure with Marker library.

## Features

- **GPU Acceleration**: Uses NVIDIA L40S GPUs for fast OCR processing
- **Auto-scaling**: 0 to N instances based on demand (pay only for usage)
- **Parallel Processing**: Large documents (>50 pages) are automatically split and processed in parallel
- **Model Caching**: Model weights cached in Modal Volume for fast cold starts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Zeabur)                         │
│  ┌─────────────┐    ┌───────────────┐    ┌──────────────┐  │
│  │   FastAPI   │───▶│ ModalParser   │───▶│ Modal Client │  │
│  └─────────────┘    └───────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ HTTP/gRPC
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Modal Serverless                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 parse_document()                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ Worker 1   │  │ Worker 2   │  │ Worker 3   │ ... │  │
│  │  │ Pages 1-50 │  │ Pages 51-100│ │ Pages 101-150   │  │
│  │  │   (GPU)    │  │   (GPU)    │  │   (GPU)    │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Modal Volume (Model Cache)               │  │
│  │                    ~5GB Marker models                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Setup

### 1. Install Modal CLI

```bash
pip install modal
```

### 2. Authenticate with Modal

```bash
modal token new
```

This will open a browser to authenticate and store credentials locally.

### 3. Deploy the Modal App

```bash
# From project root
cd app/backend
modal deploy modal_ocr/app.py
```

### 4. Configure Backend

Add to your `.env`:

```env
# Enable Modal OCR
OCR_MODE=modal
# Or use auto mode with Modal fallback:
# OCR_MODE=auto
# MODAL_ENABLED=true

MODAL_APP_NAME=research-agent-ocr
```

## Usage

### Direct Modal Call (for testing)

```bash
# Test with a sample document
modal run modal_ocr/app.py

# Test with your own PDF
modal run modal_ocr/app.py --document-filename /path/to/document.pdf
```

### From Backend Code

```python
from research_agent.infrastructure.parser.modal_parser import ModalParser

parser = ModalParser()
result = await parser.parse("/path/to/document.pdf")

print(f"Pages: {result.page_count}")
print(f"Content: {result.pages[0].content}")
```

## Processing Modes

| Document Size | Processing Mode | Parallel Workers | Est. Time |
|---------------|-----------------|------------------|-----------|
| 1-50 pages    | Single Task     | 1                | 1-3 min   |
| 51-150 pages  | Fan-out         | 3                | 3-5 min   |
| 151-300 pages | Fan-out         | 6                | 3-5 min   |
| 300+ pages    | Fan-out         | 6+               | 5-10 min  |

## Cost Estimation

| Item                     | Cost                    |
|--------------------------|-------------------------|
| L40S GPU                 | ~$0.00081/second (~$2.9/hour) |
| Model Cache Volume       | Free (included)         |
| Small PDF (10 pages)     | ~$0.02-0.05             |
| Medium PDF (100 pages)   | ~$0.24                  |
| Large PDF (300 pages)    | ~$0.72-0.90             |

## Monitoring

View logs and metrics in the Modal dashboard:
https://modal.com/apps/research-agent-ocr

## Troubleshooting

### Cold Start Issues

First request after deployment may take 30-60 seconds as models are loaded.
Subsequent requests are much faster (2-5 seconds).

### Authentication Errors

```bash
# Re-authenticate
modal token new

# Check token status
modal token info
```

### Deployment Errors

```bash
# Check app status
modal app list

# View logs
modal app logs research-agent-ocr
```

## Development

### Local Testing

```bash
# Run locally (still uses Modal cloud GPUs)
modal run modal_ocr/app.py --document-filename test.pdf
```

### Modifying the App

After changes to `app.py`:

```bash
modal deploy modal_ocr/app.py
```

## License Notes

- **Marker Library**: GPL-3.0 license. Commercial use requires compliance with GPL terms.
- **Modal**: Commercial service with free tier. See [Modal Pricing](https://modal.com/pricing).















