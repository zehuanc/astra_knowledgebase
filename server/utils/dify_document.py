import httpx
import json
import os
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from server.config import get_settings
from server.schemas.document import DocumentImportConfig

class DataSourceInfo(BaseModel):
    """
    数据源信息模型
    
    根据不同的数据源类型，可能包含不同的字段：
    - upload_file: 上传文件时包含 upload_file_id
    - notion: Notion导入时包含相关Notion信息
    - web: 网页导入时包含URL信息
    """
    upload_file_id: Optional[str] = None
    url: Optional[str] = None
    notion_page_id: Optional[str] = None
    notion_workspace_id: Optional[str] = None
    
class DocumentResponse(BaseModel):
    """Dify API 文档响应模型"""
    id: str = ""
    position: Optional[int] = 1
    data_source_type: Optional[str] = None  # 数据源类型: upload_file, notion, web, api等
    data_source_info: Optional[DataSourceInfo] = None
    dataset_process_rule_id: Optional[str] = ""
    name: Optional[str] = None  # 文档名称/标题
    created_from: Optional[str] = "api"  # 创建来源
    created_by: Optional[str] = ""  # 创建者ID
    created_at: Optional[int] = None  # 创建时间戳
    tokens: int = 0  # 令牌数量
    indexing_status: Optional[str] = "waiting"  # 索引状态: waiting, indexing, completed, error
    error: Optional[str] = None  # 错误信息
    enabled: bool = True  # 是否启用
    disabled_at: Optional[int] = None  # 禁用时间戳
    disabled_by: Optional[str] = None  # 禁用者ID
    archived: bool = False  # 是否归档
    display_status: Optional[str] = "queuing"  # 显示状态
    word_count: int = 0  # 单词数
    hit_count: int = 0  # 命中数
    doc_form: Optional[str] = "text_model"  # 文档形式: text_model, qa_model, hierarchical_model
    content: Optional[str] = None  # 文档内容(可能不在返回中)

class DifyDocumentResponse(BaseModel):
    """Dify API 完整响应模型"""
    document: DocumentResponse
    batch: Optional[str] = ""
    
    def __getattr__(self, name):
        """允许直接访问document属性"""
        if name in self.document.__fields__:
            return getattr(self.document, name)
        return super().__getattr__(name)

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
        settings = get_settings()
        jina_token = settings.JINA_TOKEN
        
        if not jina_token:
            raise ValueError("JINA_TOKEN not configured in environment variables")
        
        jina_url = "https://r.jina.ai"
        request_url = f"{jina_url}/{url}"
        jina_headers = {'Authorization': f'Bearer {jina_token}'}
        
        jina_response = requests.get(request_url, headers=jina_headers)
        
        # check response status
        if jina_response.status_code != 200:
            raise ValueError(f"Failed to crawl URL: {url}. Status code: {jina_response.status_code}")
        
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
                             dataset_id: str = None) -> DifyDocumentResponse:
        """
        从网页创建文档
        
        Args:
            url
            title
            dataset_id
            
        Returns:
            DifyDocumentResponse
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        crawler_response_text = self.jina_crawler(url)
        response = self.create_from_text(
            crawler_response_text, 
            title, 
            dataset_id, 
            doc_form="text_model", 
            import_mode="default"
        )
            
        return response
    
    async def create_from_text(self, 
                              text: str, 
                              title: str,
                              dataset_id: str = None,
                              doc_form: Optional[str] = None,
                              import_mode: Optional[str] = None) -> DifyDocumentResponse:
        """
        Args:
            text: content of the document
            title: title of the document
            dataset_id: unique identifier of the dataset
            doc_form: form of the document, text_model | hierarchical_model | qa_model
            
        Returns:
            DifyDocumentResponse
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")

        import_mode = import_mode or "default"
        if import_mode == "default":
            # default config
            config_data = {
                "name": title,
                "text": text,
                "indexing_technique": "high_quality",
                "process_rule": {"mode": "automatic"}
            }
        else:
            raise ValueError("Invalid import mode")
        
        # doc_form:
        # text_model Text documents are directly embedded; economy mode defaults to using this form
        # hierarchical_model Parent-child mode
        # qa_model Q&A Mode: Generates Q&A pairs for segmented documents and then embeds the questions
        doc_form = doc_form or "text_model"
        if doc_form:
            config_data["doc_form"] = doc_form
        
        
        config = DocumentImportConfig(**config_data)
        

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
        Args:
            document_id
            dataset_id
            
        Returns:
            DifyDocumentResponse
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
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
        Args:
            dataset_id
            page
            limit
            keyword
            
        Returns:
            Dict
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
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
        Args:
            document_id
            dataset_id
            
        Returns:
            bool
        """
        dataset_id = dataset_id or self.dataset_id
        if not dataset_id:
            raise ValueError("Dataset ID is required")
        
        
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

async def test_create_from_text():
    """
    测试 create_from_text 方法
    
    此函数演示如何使用 create_from_text 方法创建文档，
    并展示不同参数的使用方式。
    """
    from server.config import get_settings
    
    settings = get_settings()
    #web_url = input("请输入网页URL: ")
    # 确保有有效的 dataset_id 和 API 密钥
    #dataset_id = "8ac47ff4-01f5-40c9-895f-59035683f0a0"
    dataset_id = "bf9da2ca-0cc0-4c38-b7aa-60b8de0b8440"
    
    # 创建 DifyDocument 实例
    dify_doc = DifyDocument(dataset_id=dataset_id)
    #web_text= dify_doc.jina_crawler(web_url)
    qa_pairs = [
        {"question": "What is the capital of France?", "answer": "The capital of France is Paris."},
        {"question": "What is the hometown of Zehuan?", "answer": "Changsha, Hunan, China."},
        {"question": "What is the name of Zehuan's first pet?", "answer": "Garth"},
    ]

    try:
        print("测试场景 1: 基本用法 - 只提供必需参数")
        response = await dify_doc.create_from_text(
            text=json.dumps(qa_pairs),
            title="QA Test",
            doc_form="qa_model"
        )
        
        # 打印完整响应对象
        print("响应对象类型:", type(response))
        print("响应对象:", response)
        
        # 测试直接访问 document 属性
        print("\n通过 __getattr__ 访问 document 属性:")
        print("文档ID:", response.id)
        print("文档名称:", response.name)
        print("索引状态:", response.indexing_status)
        print("显示状态:", response.display_status)
        
        # 直接访问 document 对象
        print("\n直接访问 document 对象:")
        print("文档ID:", response.document.id)
        print("文档名称:", response.document.name)
        print("索引状态:", response.document.indexing_status)
        print("批次ID:", response.batch)
        
        print("---")
    except Exception as e:
        print(f" {str(e)}")
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_create_from_text())


