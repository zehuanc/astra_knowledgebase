import httpx
import json
import os
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from server.config import get_settings
from server.schemas.document import DocumentImportConfig

class DifyDocumentResponse(BaseModel):
    """Dify API 文档响应模型"""
    id: str
    dataset_id: str
    document_id: Optional[str] = None
    position: Optional[int] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[str] = None
    error: Optional[str] = None
    tokens: Optional[int] = None
    segments: Optional[List[Dict[str, Any]]] = None
    indexing_status: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    hit_count: Optional[int] = None
    enabled: Optional[bool] = None
    disabled_at: Optional[datetime] = None
    disabled_by: Optional[str] = None
    archived: Optional[bool] = None
    display_status: Optional[str] = None

class DifyDocument:
    """Dify 文档操作类"""
    
    def __init__(self, dataset_id: str = None, api_base_url: str = None):
        """
        初始化 DifyDocument 类
        
        Args:
            dataset_id: 知识库 ID
            api_base_url: API 基础 URL，默认为 https://api.dify.ai/v1
        """
        settings = get_settings()
        self.api_key = settings.DIFY_DATASET_APIKEY
        
        if not self.api_key:
            raise ValueError("Dify API key not configured")
        
        self.dataset_id = dataset_id
        self.api_base_url = api_base_url or "https://api.dify.ai/v1"
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    

    def jina_crawler(self, url: str) -> str:
        jina_url = "https://r.jina.ai"
        request_url = f"{jina_url}/{url}"
        jina_headers = {'Authorization': 'Bearer jina_e76d74a8487f437ebf3a776bc3975305gTJxOo7gkGCGk3qawLlYbNqtzOMY'}
        jina_response = requests.get(request_url, headers=jina_headers)
        return jina_response.text


    async def create_from_file(self, 
                              file_path: str = None, 
                              file_content: bytes = None,
                              file_name: str = None,
                              content_type: str = None,
                              title: str = None,
                              metadata: Union[Dict[str, Any], str] = None,
                              dataset_id: str = None) -> DifyDocumentResponse:
        """
        从文件创建文档
        
        Args:
            file_path: 文件路径（与 file_content 二选一）
            file_content: 文件内容（与 file_path 二选一）
            file_name: 文件名（当使用 file_content 时必须提供）
            content_type: 文件内容类型
            title: 文档标题
            metadata: 文档元数据，可以是字典或 JSON 字符串
            dataset_id: 知识库 ID，如果不提供则使用初始化时的 ID
            
        Returns:
            DifyDocumentResponse: 文档响应对象
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        # 处理文件
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            file_name = file_name or os.path.basename(file_path)
            
            # 如果未提供内容类型，则根据文件扩展名推断
            if not content_type:
                file_ext = os.path.splitext(file_name)[1].lower()
                if file_ext == '.pdf':
                    content_type = "application/pdf"
                elif file_ext == '.txt':
                    content_type = "text/plain"
                elif file_ext == '.docx':
                    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif file_ext == '.doc':
                    content_type = "application/msword"
                else:
                    content_type = "application/octet-stream"
        elif not file_content:
            raise ValueError("Either file_path or file_content must be provided")
        
        if not file_name:
            raise ValueError("file_name is required when using file_content")
        
        # 处理元数据
        if isinstance(metadata, dict):
            metadata_str = json.dumps(metadata)
        elif isinstance(metadata, str):
            # 验证是否为有效的 JSON 字符串
            try:
                json.loads(metadata)
                metadata_str = metadata
            except json.JSONDecodeError:
                metadata_str = "{}"
        else:
            metadata_str = "{}"
        
        # 准备表单数据
        form_data = {}
        if title:
            form_data["title"] = title
        form_data["metadata"] = metadata_str
        
        # 准备文件
        files = {
            "file": (file_name, file_content, content_type or "application/octet-stream")
        }
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/datasets/{dataset_id}/document/create-by-file",
                headers=self._get_headers(),
                data=form_data,
                files=files,
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise httpx.HTTPStatusError(
                    f"Error creating document: {error_detail}",
                    request=response.request,
                    response=response
                )
            
            return DifyDocumentResponse(**response.json())
    
    async def create_from_web(self, 
                             url: str, 
                             title: str = None,
                             metadata: Union[Dict[str, Any], str] = None,
                             dataset_id: str = None) -> DifyDocumentResponse:
        """
        从网页创建文档
        
        Args:
            url: 网页 URL
            title: 文档标题
            metadata: 文档元数据，可以是字典或 JSON 字符串
            dataset_id: 知识库 ID，如果不提供则使用初始化时的 ID
            
        Returns:
            DifyDocumentResponse: 文档响应对象
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        crawler_response_text = self.jina_crawler(url)
        data = {
            "name": url,
            "text": crawler_response_text,
            "indexing_technique": "high_quality",
            "process_rule": {"mode": "automatic"}
        }
        
        if title:
            data["name"] = title
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/datasets/{dataset_id}/document/create-by-text",
                headers=self._get_headers(),
                json=data,
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise httpx.HTTPStatusError(
                    f"Error creating document: {error_detail}",
                    request=response.request,
                    response=response
                )
            
            return DifyDocumentResponse(**response.json())
    
    async def create_from_text(self, 
                              text: str, 
                              title: str,
                              metadata: Union[Dict[str, Any], str] = None,
                              dataset_id: str = None,
                              doc_form: Optional[str] = None,
                              doc_language: Optional[str] = None,
                              embedding_model: Optional[str] = None,
                              embedding_model_provider: Optional[str] = None) -> DifyDocumentResponse:
        """
        从文本创建文档
        
        Args:
            text: 文本内容
            title: 文档标题
            metadata: 文档元数据，可以是字典或 JSON 字符串
            dataset_id: 知识库 ID，如果不提供则使用初始化时的 ID
            doc_form: 文档形式，可选
            doc_language: 文档语言，可选
            embedding_model: 嵌入模型，可选
            embedding_model_provider: 嵌入模型提供商，可选
            
        Returns:
            DifyDocumentResponse: 文档响应对象
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        # 处理元数据
        if isinstance(metadata, dict):
            metadata_str = json.dumps(metadata)
        elif isinstance(metadata, str):
            # 验证是否为有效的 JSON 字符串
            try:
                json.loads(metadata)
                metadata_str = metadata
            except json.JSONDecodeError:
                metadata_str = "{}"
        else:
            metadata_str = "{}"
        
        # 创建基本配置（只包含必填字段）
        config_data = {
            "name": title,
            "text": text,
            "indexing_technique": "high_quality",
            "process_rule": {"mode": "automatic"}
        }
        
        # 添加可选字段（如果提供）
        if doc_form:
            config_data["doc_form"] = doc_form
        
        if doc_language:
            config_data["doc_language"] = doc_language
        
        if embedding_model:
            config_data["embedding_model"] = embedding_model
        
        if embedding_model_provider:
            config_data["embedding_model_provider"] = embedding_model_provider
        
        # 创建文档导入配置
        config = DocumentImportConfig(**config_data)
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/datasets/{dataset_id}/document/create-by-text",
                headers=self._get_headers(),
                json=config.dict(),
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise httpx.HTTPStatusError(
                    f"Error creating document: {error_detail}",
                    request=response.request,
                    response=response
                )
            
            return DifyDocumentResponse(**response.json())
    
    async def get_document(self, 
                          document_id: str,
                          dataset_id: str = None) -> DifyDocumentResponse:
        """
        获取文档详情
        
        Args:
            document_id: 文档 ID
            dataset_id: 知识库 ID，如果不提供则使用初始化时的 ID
            
        Returns:
            DifyDocumentResponse: 文档响应对象
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/datasets/{dataset_id}/documents/{document_id}",
                headers=self._get_headers(),
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise httpx.HTTPStatusError(
                    f"Error getting document: {error_detail}",
                    request=response.request,
                    response=response
                )
            
            return DifyDocumentResponse(**response.json())
    
    async def list_documents(self, 
                            dataset_id: str = None,
                            page: int = 1,
                            limit: int = 20,
                            keyword: str = None) -> Dict[str, Any]:
        """
        获取文档列表
        
        Args:
            dataset_id: 知识库 ID，如果不提供则使用初始化时的 ID
            page: 页码，从 1 开始
            limit: 每页数量，默认 20
            keyword: 搜索关键词
            
        Returns:
            Dict: 包含文档列表和分页信息的字典
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        # 准备查询参数
        params = {
            "page": page,
            "limit": limit
        }
        
        if keyword:
            params["keyword"] = keyword
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/datasets/{dataset_id}/documents",
                headers=self._get_headers(),
                params=params,
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise httpx.HTTPStatusError(
                    f"Error listing documents: {error_detail}",
                    request=response.request,
                    response=response
                )
            
            return response.json()
    
    async def delete_document(self, 
                             document_id: str,
                             dataset_id: str = None) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档 ID
            dataset_id: 知识库 ID，如果不提供则使用初始化时的 ID
            
        Returns:
            bool: 是否删除成功
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.api_base_url}/datasets/{dataset_id}/documents/{document_id}",
                headers=self._get_headers(),
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise httpx.HTTPStatusError(
                    f"Error deleting document: {error_detail}",
                    request=response.request,
                    response=response
                )
            
            return True
    
    async def update_document_metadata(self, 
                                      document_id: str,
                                      metadata: Union[Dict[str, Any], str],
                                      dataset_id: str = None) -> DifyDocumentResponse:
        """
        更新文档元数据
        
        Args:
            document_id: 文档 ID
            metadata: 文档元数据，可以是字典或 JSON 字符串
            dataset_id: 知识库 ID，如果不提供则使用初始化时的 ID
            
        Returns:
            DifyDocumentResponse: 文档响应对象
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        # 处理元数据
        if isinstance(metadata, dict):
            metadata_str = json.dumps(metadata)
        elif isinstance(metadata, str):
            # 验证是否为有效的 JSON 字符串
            try:
                json.loads(metadata)
                metadata_str = metadata
            except json.JSONDecodeError:
                raise ValueError("Invalid metadata JSON string")
        else:
            raise ValueError("metadata must be a dict or a JSON string")
        
        # 准备请求数据
        data = {
            "metadata": metadata_str
        }
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.api_base_url}/datasets/{dataset_id}/documents/{document_id}",
                headers=self._get_headers(),
                json=data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if "message" in error_json:
                        error_detail = error_json["message"]
                except:
                    pass
                raise httpx.HTTPStatusError(
                    f"Error updating document metadata: {error_detail}",
                    request=response.request,
                    response=response
                )
            
            return DifyDocumentResponse(**response.json())
