from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum

class DocumentSource(str, Enum):
    WEB = "web"
    FILE = "file"
    QA = "qa"

class DocumentBase(BaseModel):
    title: str
    source_type: DocumentSource
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentCreate(DocumentBase):
    content: str
    
class WebDocumentCreate(DocumentCreate):
    url: HttpUrl
    source_type: DocumentSource = DocumentSource.WEB

class FileDocumentCreate(DocumentCreate):
    filename: str
    file_type: str
    source_type: DocumentSource = DocumentSource.FILE

class QADocumentCreate(DocumentCreate):
    questions: List[str]
    answers: List[str]
    source_type: DocumentSource = DocumentSource.QA

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class Document(DocumentBase):
    id: str
    dataset_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 

class IndexingTechnique(str, Enum):
    HIGH_QUALITY = "high_quality"
    ECONOMY = "economy"

class DocumentForm(str, Enum):
    TEXT_MODEL = "text_model"
    HIERARCHICAL_MODEL = "hierarchical_model"
    QA_MODEL = "qa_model"

class DocumentLanguage(str, Enum):
    ENGLISH = "English"
    CHINESE = "Chinese"

class ProcessMode(str, Enum):
    AUTOMATIC = "automatic"
    CUSTOM = "custom"

class SearchMethod(str, Enum):
    HYBRID_SEARCH = "hybrid_search"
    SEMANTIC_SEARCH = "semantic_search"
    FULL_TEXT_SEARCH = "full_text_search"

class RerankingMode(BaseModel):
    reranking_provider_name: str = Field("", description="Rerank model provider")
    reranking_model_name: str = Field("", description="Rerank model name")

class RetrievalModel(BaseModel):
    search_method: SearchMethod = Field(
        default=SearchMethod.HYBRID_SEARCH, 
        description="Search method: hybrid_search, semantic_search, or full_text_search"
    )
    reranking_enable: bool = Field(default=True, description="Whether to enable reranking")
    reranking_mode: RerankingMode = Field(default_factory=RerankingMode, description="Reranking configuration")
    top_k: int = Field(default=3, description="Top k results to rerank")
    score_threshold_enabled: bool = Field(default=True, description="Whether to enable score threshold")
    score_threshold: float = Field(default=0.5, description="Score threshold")

class ProcessRule(BaseModel):
    mode: ProcessMode = Field(default=ProcessMode.AUTOMATIC, description="Processing mode: automatic or custom")

class DocumentImportConfig(BaseModel):
    """Configuration for document import"""
    name: str = Field(..., description="Document name")
    text: str = Field(..., description="Document text content")
    indexing_technique: IndexingTechnique = Field(
        default=IndexingTechnique.HIGH_QUALITY, 
        description="Indexing technique: high_quality or economy"
    )
    process_rule: ProcessRule = Field(
        default_factory=ProcessRule, 
        description="Document processing rules"
    )
    
    # 以下字段设为可选
    doc_form: Optional[DocumentForm] = Field(
        None, 
        description="Document form: text_model, hierarchical_model, or qa_model"
    )
    doc_language: Optional[DocumentLanguage] = Field(
        None, 
        description="Document language: English or Chinese"
    )
    retrieval_model: Optional[RetrievalModel] = Field(
        None, 
        description="Retrieval model configuration"
    )
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    embedding_model_provider: Optional[str] = Field(None, description="Embedding model provider")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "name": "Example Document",
                "text": "This is an example document content.",
                "indexing_technique": "high_quality",
                "process_rule": {
                    "mode": "automatic"
                },
                # 可选字段示例
                "doc_form": "text_model",
                "doc_language": "English",
                "retrieval_model": {
                    "search_method": "hybrid_search",
                    "reranking_enable": True,
                    "reranking_mode": {
                        "reranking_provider_name": "",
                        "reranking_model_name": ""
                    },
                    "top_k": 3,
                    "score_threshold_enabled": True,
                    "score_threshold": 0.5
                },
                "embedding_model": "text-embedding-ada-002",
                "embedding_model_provider": "openai"
            }
        }
        
    def dict(self, *args, **kwargs):
        """Override the dict method to exclude None values"""
        result = super().dict(*args, **kwargs)
        return {k: v for k, v in result.items() if v is not None} 