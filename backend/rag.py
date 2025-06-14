import os
from typing import List, Optional, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.docstore.document import Document
from openai import OpenAI
from backend.scraper import DocumentationScraper
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DocumentationRAG:
    """
    Retrieval-Augmented Generation system for documentation.
    Manages vector storage, retrieval, and AI-powered Q&A.
    """
    
    def __init__(self, collection_name: str = "docs_vectors"):
        self.collection_name = collection_name
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = None
        self.doc_metadata = {}
    
    def create_vector_store(self, documentation_url: str, max_pages: int = 50):
        """
        Create vector store from documentation website.
        This is the main entry point for indexing new documentation.
        """
        print(f"🚀 Starting documentation ingestion for: {documentation_url}")
        
        # Step 1: Scrape documentation
        scraper = DocumentationScraper(documentation_url, max_pages)
        documents = scraper.scrape_documentation()
        
        if not documents:
            raise ValueError("No documents were scraped. Please check the URL and try again.")
        
        # Store metadata about this documentation
        self.doc_metadata = {
            'url': documentation_url,
            'pages_scraped': len(documents),
            'total_characters': sum(doc.metadata['length'] for doc in documents),
            'has_code_examples': sum(1 for doc in documents if doc.metadata.get('has_code', False))
        }
        
        # Step 2: Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Optimal size for context
            chunk_overlap=200,  # Overlap for continuity
            separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
            length_function=len
        )
        
        split_docs = text_splitter.split_documents(documents)
        print(f"📄 Split into {len(split_docs)} chunks")
        
        # Step 3: Create vector store
        print("🔍 Creating embeddings and vector store...")
        
        # Qdrant connection settings
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
        
        try:
            self.vector_store = QdrantVectorStore.from_documents(
                documents=split_docs,
                url=qdrant_url,
                api_key=qdrant_api_key,
                embedding=self.embedding_model,
                collection_name=self.collection_name,
                force_recreate=True  # Always create fresh collection
            )
            
            print("✅ Vector store created successfully!")
            print(f"   Collection: {self.collection_name}")
            print(f"   Documents: {len(split_docs)}")
            
        except Exception as e:
            raise Exception(f"Failed to create vector store: {str(e)}. Make sure Qdrant is running.")
        
        return self.vector_store
    
    def load_existing_vector_store(self):
        """Load existing vector store from Qdrant"""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
        
        try:
            self.vector_store = QdrantVectorStore.from_existing_collection(
                url=qdrant_url,
                api_key=qdrant_api_key,
                embedding=self.embedding_model,
                collection_name=self.collection_name
            )
            print(f"✅ Loaded existing vector store: {self.collection_name}")
            return self.vector_store
        except Exception as e:
            raise Exception(f"Failed to load vector store: {str(e)}")
    
    def format_search_results(self, results: List[Document]) -> str:
        """Format search results for context"""
        context_parts = []
        
        for i, result in enumerate(results, 1):
            # Extract metadata
            title = result.metadata.get('title', 'Unknown')
            source = result.metadata.get('source', 'Unknown')
            has_code = result.metadata.get('has_code', False)
            
            # Format the result
            context_parts.append(f"""
📄 **Source {i}**: {title}
🔗 URL: {source}
{'💻 Contains code examples' if has_code else ''}

{result.page_content}

---""")
        
        return "\n".join(context_parts)
    
    def query(self, question: str, num_results: int = 4) -> str:
        """
        Query the documentation and get an AI-powered response.
        Returns a formatted answer with code examples and source citations.
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Create or load one first.")
        
        # Step 1: Search for relevant documents
        try:
            search_results = self.vector_store.similarity_search(
                query=question,
                k=num_results
            )
        except Exception as e:
            return f"Error searching documentation: {str(e)}"
        
        if not search_results:
            return "I couldn't find relevant information in the documentation. Try rephrasing your question."
        
        # Step 2: Format context from search results
        context = self.format_search_results(search_results)
        
        # Step 3: Determine if the question is asking for code
        is_code_request = any(keyword in question.lower() for keyword in [
            'code', 'example', 'how to', 'implement', 'write', 'create',
            'function', 'class', 'method', 'syntax', 'snippet'
        ])
        
        # Step 4: Create system prompt
        system_prompt = f"""You are DocChat AI, an expert documentation assistant. Your role is to provide accurate, helpful answers based on the provided documentation context.

**Guidelines:**
1. Answer ONLY based on the provided context. If the information isn't in the context, say so clearly.
2. When providing code examples:
   - Use proper syntax highlighting with ```language blocks
   - Ensure code is complete and runnable
   - Add helpful comments
   - Show multiple approaches if relevant
3. Always cite which source(s) your answer comes from
4. Structure your answer clearly with:
   - A direct answer to the question
   - Supporting details/explanation
   - Code examples (if relevant)
   - Links to the documentation for further reading
5. Be concise but thorough
6. If the user is asking for code, prioritize showing working examples

**Context from documentation:**
{context}"""
        
        # Add code-specific instructions if needed
        if is_code_request:
            system_prompt += """

**Note:** The user is asking for code/implementation details. Prioritize providing clear, working code examples with explanations."""
        
        # Step 5: Get response from OpenAI
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for best quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.1,  # Low temperature for factual accuracy
                max_tokens=2000  # Enough for detailed responses with code
            )
            
            answer = response.choices[0].message.content
            
            # Step 6: Post-process the answer
            # Ensure code blocks are properly formatted
            answer = self._ensure_code_formatting(answer)
            
            # Add source links at the end
            unique_sources = list(set(doc.metadata.get('source', '') for doc in search_results))
            if unique_sources:
                answer += "\n\n---\n📚 **Sources:**\n"
                for source in unique_sources[:3]:  # Limit to 3 sources
                    if source:
                        answer += f"- {source}\n"
            
            return answer
            
        except Exception as e:
            return f"Error generating response: {str(e)}. Please check your OpenAI API key."
    
    def _ensure_code_formatting(self, text: str) -> str:
        """Ensure code blocks are properly formatted for syntax highlighting"""
        # Pattern to find code blocks without language specification
        pattern = r'```\n(.*?)```'
        
        def add_language(match):
            code = match.group(1)
            # Try to detect language
            if 'import ' in code or 'def ' in code or 'class ' in code:
                return f'```python\n{code}```'
            elif 'function ' in code or 'const ' in code or 'let ' in code:
                return f'```javascript\n{code}```'
            elif 'interface ' in code or 'type ' in code:
                return f'```typescript\n{code}```'
            elif '<' in code and '>' in code:
                return f'```html\n{code}```'
            else:
                return f'```\n{code}```'
        
        text = re.sub(pattern, add_language, text, flags=re.DOTALL)
        return text
    
    def get_statistics(self) -> Dict:
        """Get statistics about the indexed documentation"""
        if not self.vector_store:
            return {"status": "No vector store loaded"}
        
        stats = {
            "collection_name": self.collection_name,
            "indexed": True,
            **self.doc_metadata
        }
        
        return stats