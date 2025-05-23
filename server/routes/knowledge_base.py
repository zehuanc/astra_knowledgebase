from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Body
from typing import List, Optional, Dict, Any
from server.schemas.document import (
    Document, DocumentCreate, WebDocumentCreate, 
    FileDocumentCreate, QADocumentCreate, DocumentUpdate
)
from server.utils.document_processor import (
    process_web_document, process_file_document, 
    process_qa_document,
    get_documents, update_document
)
import uuid
from datetime import datetime
import json
import httpx
from server.config import get_settings
import os
from server.utils.dify_document import DifyDocument, DifyDocumentResponse

router = APIRouter()


@router.post("/datasets/{dataset_id}/imports", response_model=DifyDocumentResponse)
async def create_document_in_kb(
    dataset_id: str,
    import_type: str = Query(..., alias="type", description="Import type: web, file, or qa"),
    title: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    questions: Optional[str] = Form(None),
    answers: Optional[str] = Form(None)
):
    """
    Import a document to the knowledge base using RESTful style API
    
    Supports different import types:
    - web: Import from a web URL
    - file: Import from an uploaded file
    - qa: Import from question-answer pairs
    """
    try:
        # according to import type, handle different import methods
        dify_doc = DifyDocument(dataset_id=dataset_id)
        if import_type == "web":
            if not url:
                raise HTTPException(status_code=400, detail="URL is required for web imports")
            
            return await dify_doc.create_from_web(
                dataset_id=dataset_id,
                url=url,
                title=title,
            )
        
        elif import_type == "file":
            if not file:
                raise HTTPException(status_code=400, detail="File is required for file imports")
            


        elif import_type == "qa":
            if not questions or not answers:
                raise HTTPException(status_code=400, detail="Questions and answers are required for Q&A imports")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid import type: {import_type}. Supported types: web, file, qa")
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import document: {str(e)}")

@router.delete("/datasets/{dataset_id}/documents/{document_id}", response_model=Dict[str, str])
async def delete_document_endpoint(
    dataset_id: str,
    document_id: str
):
    """Delete a document from the knowledge base"""
    try:
        dify_doc = DifyDocument(dataset_id=dataset_id)
        res = await dify_doc.delete_document(document_id)
        
        if res:
            return {"status": "success", "message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/datasets/{dataset_id}/documents")
async def get_documents_from_knowledgebase(
    dataset_id: str,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """Get documents from a knowledge base"""
    try:
        # Get documents
        dify_doc = DifyDocument(dataset_id=dataset_id)
        res = await dify_doc.list_documents(page=skip, limit=limit, keyword=search)
        
        return res['data']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@router.patch("/datasets/{dataset_id}/documents/{document_id}", response_model=Document)
async def update_document_metadata_endpoint(
    dataset_id: str,
    document_id: str,
    update_data: DocumentUpdate
):
    """Update document metadata"""
    try:
        # Update document
        updated_document = update_document(dataset_id, document_id, update_data)
        
        if not updated_document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return updated_document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}") 