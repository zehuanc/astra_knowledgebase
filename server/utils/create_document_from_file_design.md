request body
    data:{
        original_document_id: Optional[string]
        indexing_technique: 
            high_quality: High quality: embedding using embedding model, built as vector database index
            economy: Economy: Build using inverted index of keyword table index
        
        doc_form: Format of indexed content
            text_model: Text documents are directly embedded; economy mode defaults to using this form
            hierarchical_model: Parent-child mode
            qa_model: Q&A Mode: Generates Q&A pairs for segmented documents and then embeds the questions
        doc_language: In Q&A mode, specify the language of the document, for example: English, Chinese
        process_rule: Processing rules
            mode: Cleaning, segmentation mode, automatic / custom
            rules: Custom rules (in automatic mode, this field is empty)
                pre_processing_rules: Preprocessing rules
                id: Unique identifier for the preprocessing rule
                enumerate
                remove_extra_spaces Replace consecutive spaces, newlines, tabs
                remove_urls_emails Delete URL, email address
                enabled: Whether to select this rule or not. If no document ID is passed in, it represents the default value.
    }
