# 多格式文档支持实现计划

> 扩展文档上传功能，支持扫描版PDF、图片PDF、MP4、MP3、Word、PPT等多种格式，使用 Docling 处理文档类，WhisperX 处理音视频。

## 技术方案

| 文件类型 | 解决方案 | 说明 |
|---------|---------|------|
| PDF (文字/扫描/图片) | Docling | 内置 OCR，支持复杂布局 |
| Word (DOCX) | Docling | 原生支持 |
| PPT (PPTX) | Docling | 原生支持 |
| MP3/MP4 | WhisperX | 精确时间戳 + 说话人分离 |

---

## 后端改动

### 1. 新增抽象接口 `infrastructure/parser/base.py`

统一所有格式的解析器接口，替代原有的 `PDFParser`：

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ParsedPage:
    """统一的解析结果页面"""
    page_number: int
    content: str
    metadata: dict = field(default_factory=dict)  # 图片、时间戳等

class DocumentParser(ABC):
    """文档解析器抽象接口"""
    
    @abstractmethod
    async def parse(self, file_path: str) -> List[ParsedPage]:
        """解析文档，返回页面列表"""
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """返回支持的 MIME 类型列表"""
        pass
```

### 2. Docling 解析器 `infrastructure/parser/docling_parser.py`

处理 PDF、DOCX、PPTX 文件：

```python
import asyncio
from typing import List
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

from research_agent.infrastructure.parser.base import DocumentParser, ParsedPage

class DoclingParser(DocumentParser):
    """使用 Docling 解析 PDF/Word/PPT 文档"""
    
    def __init__(self):
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.PPTX,
            ],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=StandardPdfPipeline,  # 包含 OCR
                ),
            }
        )
    
    async def parse(self, file_path: str) -> List[ParsedPage]:
        """解析文档"""
        result = await asyncio.to_thread(self.converter.convert, file_path)
        
        # 转换为统一格式
        pages = []
        markdown_content = result.document.export_to_markdown()
        
        # Docling 返回整个文档的 Markdown，需要按逻辑分页
        # 对于 PDF 可以按实际页数分割，对于 Word/PPT 按章节分割
        pages.append(ParsedPage(
            page_number=1,
            content=markdown_content,
            metadata={
                "source_format": str(result.input.format),
                "has_ocr": True,
            }
        ))
        
        return pages
    
    def supported_formats(self) -> List[str]:
        return [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]
```

### 3. WhisperX 解析器 `infrastructure/parser/whisperx_parser.py`

处理 MP3、MP4 音视频文件：

```python
import asyncio
from typing import List
import whisperx

from research_agent.infrastructure.parser.base import DocumentParser, ParsedPage

class WhisperXParser(DocumentParser):
    """使用 WhisperX 转录音视频文件"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None  # 延迟加载
    
    def _get_model(self):
        if self._model is None:
            self._model = whisperx.load_model(self.model_size, device="cpu")
        return self._model
    
    async def parse(self, file_path: str) -> List[ParsedPage]:
        """转录音视频文件"""
        model = self._get_model()
        audio = whisperx.load_audio(file_path)
        
        # 在线程池中执行转录
        result = await asyncio.to_thread(model.transcribe, audio)
        
        # 按时间段分页（每30秒一页）
        pages = []
        segment_duration = 30  # 秒
        current_page = 1
        current_content = []
        current_start = 0
        
        for segment in result.get("segments", []):
            segment_start = segment.get("start", 0)
            
            # 如果超过当前页的时间范围，创建新页
            if segment_start >= current_start + segment_duration:
                if current_content:
                    pages.append(ParsedPage(
                        page_number=current_page,
                        content="\n".join(current_content),
                        metadata={
                            "time_start": current_start,
                            "time_end": current_start + segment_duration,
                        }
                    ))
                current_page += 1
                current_content = []
                current_start = (segment_start // segment_duration) * segment_duration
            
            # 添加带时间戳的文本
            timestamp = f"[{self._format_time(segment_start)}]"
            text = segment.get("text", "").strip()
            speaker = segment.get("speaker", "")
            
            if speaker:
                current_content.append(f"{timestamp} [{speaker}]: {text}")
            else:
                current_content.append(f"{timestamp} {text}")
        
        # 添加最后一页
        if current_content:
            pages.append(ParsedPage(
                page_number=current_page,
                content="\n".join(current_content),
                metadata={
                    "time_start": current_start,
                    "time_end": segment_start if result.get("segments") else current_start,
                }
            ))
        
        return pages
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间为 MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def supported_formats(self) -> List[str]:
        return [
            "audio/mpeg",      # MP3
            "audio/wav",       # WAV
            "video/mp4",       # MP4
            "video/webm",      # WebM
        ]
```

### 4. 解析器工厂 `infrastructure/parser/factory.py`

根据 MIME 类型自动选择解析器：

```python
from typing import Optional
from research_agent.infrastructure.parser.base import DocumentParser
from research_agent.infrastructure.parser.docling_parser import DoclingParser
from research_agent.infrastructure.parser.whisperx_parser import WhisperXParser
from research_agent.infrastructure.pdf.pymupdf import PyMuPDFParser

class ParserFactory:
    """解析器工厂 - 根据文件类型选择合适的解析器"""
    
    _docling_parser: Optional[DoclingParser] = None
    _whisperx_parser: Optional[WhisperXParser] = None
    _pymupdf_parser: Optional[PyMuPDFParser] = None
    
    @classmethod
    def get_parser(cls, mime_type: str) -> DocumentParser:
        """根据 MIME 类型获取解析器"""
        
        # 音视频文件
        if mime_type in ["audio/mpeg", "audio/wav", "video/mp4", "video/webm"]:
            if cls._whisperx_parser is None:
                cls._whisperx_parser = WhisperXParser()
            return cls._whisperx_parser
        
        # Office 文档 (Word/PPT) - 使用 Docling
        if mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]:
            if cls._docling_parser is None:
                cls._docling_parser = DoclingParser()
            return cls._docling_parser
        
        # PDF - 可选择 Docling (OCR) 或 PyMuPDF (快速)
        if mime_type == "application/pdf":
            # 默认使用 Docling 以支持 OCR
            if cls._docling_parser is None:
                cls._docling_parser = DoclingParser()
            return cls._docling_parser
        
        raise ValueError(f"Unsupported mime type: {mime_type}")
    
    @classmethod
    def is_supported(cls, mime_type: str) -> bool:
        """检查是否支持该 MIME 类型"""
        supported = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "audio/mpeg",
            "audio/wav",
            "video/mp4",
            "video/webm",
        ]
        return mime_type in supported
```

### 5. 修改 API `api/v1/documents.py`

扩展支持的文件类型：

```python
# 支持的 MIME 类型映射
SUPPORTED_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
    "audio/mpeg": [".mp3"],
    "video/mp4": [".mp4"],
    "audio/wav": [".wav"],
}

def get_mime_type(filename: str) -> str:
    """根据文件扩展名获取 MIME 类型"""
    ext = Path(filename).suffix.lower()
    for mime_type, extensions in SUPPORTED_MIME_TYPES.items():
        if ext in extensions:
            return mime_type
    raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
```

### 6. 修改 Worker `worker/tasks/document_processor.py`

使用 ParserFactory 替代硬编码的 PyMuPDFParser：

```python
# 原代码
pdf_parser = PyMuPDFParser()
pages = await pdf_parser.extract_text(local_path)

# 新代码
from research_agent.infrastructure.parser.factory import ParserFactory

parser = ParserFactory.get_parser(doc.mime_type)
pages = await parser.parse(local_path)
```

### 7. 更新 Document 实体 `domain/entities/document.py`

扩展 mime_type 支持和添加新字段：

```python
from enum import Enum

class DocumentType(str, Enum):
    """文档类型"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    AUDIO = "audio"
    VIDEO = "video"

@dataclass
class Document:
    # 现有字段...
    
    # 新增字段
    document_type: DocumentType = DocumentType.PDF
    duration_seconds: Optional[float] = None  # 音视频时长
    has_ocr: bool = False  # 是否经过 OCR 处理
    transcript_segments: Optional[List[dict]] = None  # 音视频转录分段
```

---

## 前端改动

### 8. 扩展文件上传支持 `components/studio/SourcePanel.tsx`

```tsx
// 当前
<input type="file" hidden accept=".pdf" onChange={handleUpload} />
<Button>Upload PDF</Button>

// 修改为
const ACCEPTED_TYPES = ".pdf,.docx,.pptx,.mp3,.mp4,.wav";
<input type="file" hidden accept={ACCEPTED_TYPES} onChange={handleUpload} />
<Button>Upload File</Button>
```

### 9. 新增多媒体预览组件

根据文件类型渲染不同的预览器：

```
components/studio/viewers/
├── PDFViewer.tsx          # 现有 react-pdf 逻辑抽取
├── AudioVideoPlayer.tsx   # 新增: HTML5 播放器 + 转录文本
├── TranscriptViewer.tsx   # 新增: 时间戳文本展示 (点击跳转)
└── DocumentViewer.tsx     # 新增: Markdown 渲染 (Word/PPT 内容)
```

**AudioVideoPlayer 设计**:
```tsx
interface AudioVideoPlayerProps {
  fileUrl: string;
  transcript?: TranscriptSegment[];  // 从后端获取
}

interface TranscriptSegment {
  start: number;      // 秒
  end: number;
  text: string;
  speaker?: string;   // WhisperX 说话人分离
}

// 组件功能：
// 1. HTML5 原生播放器
// 2. 转录文本同步高亮
// 3. 点击文本跳转到对应时间点
```

### 10. 文件类型图标和缩略图

```tsx
import { FileText, FileType, Presentation, Music, Video, File } from "lucide-react";

// 根据 mime_type 显示不同图标
const getFileIcon = (mimeType: string) => {
  if (mimeType.includes('pdf')) return <FileText />;
  if (mimeType.includes('word')) return <FileType />;
  if (mimeType.includes('presentation')) return <Presentation />;
  if (mimeType.includes('audio')) return <Music />;
  if (mimeType.includes('video')) return <Video />;
  return <File />;
};

// 根据 mime_type 显示不同的标签颜色
const getFileTypeChip = (mimeType: string) => {
  const config = {
    'application/pdf': { label: 'PDF', bgcolor: '#FEE2E2', color: '#DC2626' },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 
      { label: 'DOCX', bgcolor: '#DBEAFE', color: '#2563EB' },
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 
      { label: 'PPTX', bgcolor: '#FEF3C7', color: '#D97706' },
    'audio/mpeg': { label: 'MP3', bgcolor: '#D1FAE5', color: '#059669' },
    'video/mp4': { label: 'MP4', bgcolor: '#EDE9FE', color: '#7C3AED' },
  };
  return config[mimeType] || { label: 'FILE', bgcolor: '#F3F4F6', color: '#6B7280' };
};
```

### 11. 扩展 API 类型 `lib/api.ts`

```typescript
export interface ProjectDocument {
  id: string;
  project_id: string;
  filename: string;
  file_size: number;
  page_count: number;
  status: 'pending' | 'processing' | 'ready' | 'error';
  graph_status?: 'pending' | 'processing' | 'ready' | 'error';
  summary?: string;
  created_at: string;
  
  // 新增字段
  mime_type: string;           // 文件 MIME 类型
  duration_seconds?: number;   // 音视频时长（秒）
  has_transcript?: boolean;    // 是否有转录文本
}

// 转录分段类型
export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string;
}

export interface TranscriptResponse {
  document_id: string;
  segments: TranscriptSegment[];
  duration_seconds: number;
}

// Documents API 扩展
export const documentsApi = {
  // 现有方法...
  
  // 新增: 获取转录文本
  getTranscript: (documentId: string) =>
    fetchApi<TranscriptResponse>(`/api/v1/documents/${documentId}/transcript`),
  
  // 新增: 获取媒体文件流式 URL
  getMediaStreamUrl: (documentId: string) =>
    `${getApiUrl()}/api/v1/documents/${documentId}/stream`,
};
```

### 12. 新增后端转录文本 API

```python
# api/v1/documents.py

@router.get("/documents/{document_id}/transcript")
async def get_transcript(
    document_id: UUID,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取音视频文档的转录文本（带时间戳）
    
    返回格式：
    {
        "document_id": "...",
        "segments": [
            {"start": 0.0, "end": 5.2, "text": "Hello", "speaker": "SPEAKER_00"},
            ...
        ],
        "duration_seconds": 120.5
    }
    """
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.mime_type not in ["audio/mpeg", "video/mp4", "audio/wav"]:
        raise HTTPException(status_code=400, detail="Document is not an audio/video file")
    
    # 从 parsing_metadata 中获取转录分段
    segments = document.parsing_metadata.get("transcript_segments", [])
    duration = document.duration_seconds or 0
    
    return {
        "document_id": str(document_id),
        "segments": segments,
        "duration_seconds": duration,
    }


@router.get("/documents/{document_id}/stream")
async def stream_media(
    document_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """
    流式返回媒体文件（支持 Range 请求用于视频拖拽）
    """
    document = await document_repo.find_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 返回文件流，支持 Range 请求
    return FileResponse(
        path=document.file_path,
        media_type=document.mime_type,
        filename=document.filename,
    )
```

---

## 预览策略

| 文件类型 | 预览方式 | 组件 | 说明 |
|---------|---------|------|------|
| PDF | react-pdf 原生渲染 | PDFViewer | 保持现有实现 |
| Word/PPT | Markdown 文本展示 | DocumentViewer | Docling 输出 Markdown |
| MP3/MP4 | HTML5 播放器 + 转录文本 | AudioVideoPlayer | 支持时间戳跳转 |

---

## 依赖更新 `pyproject.toml`

```toml
dependencies = [
    # 现有依赖...
    
    # 新增
    "docling>=2.0.0",          # 文档解析 (PDF/Word/PPT/OCR)
    "whisperx>=3.0.0",         # 音视频转录
    "torch>=2.0.0",            # WhisperX 依赖
    "ffmpeg-python>=0.2.0",    # 音视频处理
]
```

## 系统依赖

需要安装 FFmpeg（用于 WhisperX 音视频处理）：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Docker (在 Dockerfile 中)
RUN apt-get update && apt-get install -y ffmpeg
```

---

## 实现顺序 (TODO)

1. [ ] 创建统一的文档解析器抽象接口 `infrastructure/parser/base.py`
2. [ ] 实现 Docling 解析器 (PDF/Word/PPT/OCR)
3. [ ] 实现 WhisperX 解析器 (MP3/MP4)
4. [ ] 实现解析器工厂，根据 MIME 类型自动选择
5. [ ] 更新 documents API 支持新文件类型
6. [ ] 修改 document_processor worker 使用新解析器
7. [ ] 更新 Document 实体添加新字段
8. [ ] 更新 pyproject.toml 添加 docling/whisperx 依赖
9. [ ] 前端：扩展文件上传支持新类型
10. [ ] 前端：抽取 PDFViewer 组件
11. [ ] 前端：新增 AudioVideoPlayer 组件
12. [ ] 前端：新增 DocumentViewer 组件 (Markdown 渲染)
13. [ ] 前端：更新文件类型图标和标签
14. [ ] 前端：扩展 API 类型定义
15. [ ] 后端：新增转录文本 API
16. [ ] 集成测试各种文件格式

---

## 注意事项

1. **CPU 性能**: Docling OCR 和 WhisperX 在 CPU 上运行较慢，大文件建议异步处理
2. **内存占用**: WhisperX 模型约需 1-2GB 内存，建议使用 `base` 模型平衡速度和质量
3. **超时处理**: 大型音视频文件处理可能需要较长时间，需要调整 worker 超时配置
4. **音视频预览**: 需要后端提供文件流式访问接口，前端使用 HTML5 原生播放器
5. **存储空间**: 音视频文件通常较大，需要考虑存储策略和清理机制

















