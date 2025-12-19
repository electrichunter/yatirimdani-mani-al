"""
PDF Document Loader and Text Chunker
Processes strategy PDFs for RAG
"""

import os
from pathlib import Path
import pypdf
import config
from utils.logger import setup_logger

logger = setup_logger("DocumentLoader")


class DocumentLoader:
    """Load and chunk PDF documents for RAG"""
    
    def __init__(self, data_path=None):
        """
        Args:
            data_path: Path to directory containing PDFs
        """
        self.data_path = data_path or config.RAG_DATA_PATH
    
    def load_pdf(self, pdf_path):
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text string
        """
        try:
            text = ""
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            logger.info(f"📄 Loaded PDF: {os.path.basename(pdf_path)} ({len(text)} chars)")
            return text
        
        except Exception as e:
            logger.error(f"❌ Failed to load PDF {pdf_path}: {str(e)}")
            return None
    
    def chunk_text(self, text, chunk_size=500, overlap=50):
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Approximate chunk size in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only if not too short
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def load_all_pdfs(self):
        """
        Load all PDFs from data directory
        
        Returns:
            Dict mapping document name to list of text chunks
        """
        pdf_path = Path(self.data_path)
        
        if not pdf_path.exists():
            logger.warning(f"⚠️ Data path does not exist: {self.data_path}")
            os.makedirs(self.data_path, exist_ok=True)
            logger.info(f"📁 Created data directory: {self.data_path}")
            logger.info(f"   Place your strategy PDF files in: {self.data_path}")
            return {}
        
        pdf_files = list(pdf_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"⚠️ No PDF files found in {self.data_path}")
            return {}
        
        all_documents = {}
        
        for pdf_file in pdf_files:
            text = self.load_pdf(pdf_file)
            
            if text:
                chunks = self.chunk_text(text)
                all_documents[pdf_file.stem] = chunks
                logger.info(f"  ✅ {pdf_file.name}: {len(chunks)} chunks")
        
        logger.info(f"📚 Loaded {len(all_documents)} documents")
        
        return all_documents
    
    def create_sample_document(self):
        """Create a sample strategy document for testing"""
        sample_text = """
# Trading Strategy: Trend Following with RSI Confirmation

## Entry Rules
1. Identify strong trend using 20, 50, and 200 EMA alignment
2. Wait for RSI to enter oversold (< 30) for buy or overbought (> 70) for sell
3. Confirm with MACD crossover in the same direction
4. Volume must be above average (1.5x or more)
5. Check multiple timeframes (H1, H4, D1) for confluence

## Risk Management
- Risk only 1% of account per trade
- Minimum Risk/Reward ratio: 2:1
- Maximum 3 open positions at once
- Stop loss below/above recent support/resistance

## Exit Rules
- Take profit at predetermined level (2x stop loss minimum)
- Trail stop loss when in profit by 1x risk
- Exit if opposite signal appears on higher timeframe

## Key Principles
- Patience is critical - wait for all conditions to align
- Never trade against the major trend
- Protect capital first, profits second
- Quality over quantity - few perfect trades beat many mediocre ones
        """
        
        sample_path = os.path.join(self.data_path, "sample_strategy.pdf")
        
        # Check if already exists
        if os.path.exists(sample_path):
            logger.info(f"Sample document already exists at {sample_path}")
            return
        
        # Create directory
        os.makedirs(self.data_path, exist_ok=True)
        
        # For now, just save as text file (in production, user adds real PDFs)
        text_path = sample_path.replace('.pdf', '.txt')
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        
        logger.info(f"✅ Created sample strategy document at {text_path}")
        logger.info(f"   (In production, replace with actual PDF strategy books)")
