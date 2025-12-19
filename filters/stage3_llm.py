"""Stage 3: RAG + LLM Decision Engine
Final decision maker with strategy knowledge
GPU usage: 2.5-4GB VRAM (only loaded when Stage 1 & 2 pass)
"""

import config
# Lazy import RAG components to avoid heavy dependencies (torch, etc.) when disabled
# from rag.vector_store import VectorStore
# from rag.retriever import DocumentLoader
from llm.ollama_client import OllamaClient
from llm.prompts import get_system_prompt, build_decision_prompt, validate_llm_response
from utils.logger import setup_logger, log_trade_decision

logger = setup_logger("LLMDecision")


class LLMDecisionEngine:
    """
    RAG + LLM decision making system
    Only loads when Stage 1 and Stage 2 pass (Lazy Loading)
    """
    
    def __init__(self, model_name=None, rag_data_path=None):
        """
        Args:
            model_name: LLM model to use (default from config)
            rag_data_path: Path to strategy PDFs
        """
        logger.info("🔧 Initializing LLM Decision Engine...")
        
        # Initialize LLM client based on config
        if config.USE_GEMINI_API:
            from llm.gemini_client import GeminiClient
            self.llm = GeminiClient(model_name=config.GEMINI_MODEL)
            logger.info("✅ Using Gemini API (cloud-based)")
        else:
            from llm.ollama_client import OllamaClient
            self.llm = OllamaClient(model_name=model_name)
            logger.info("✅ Using Ollama (local)")
        
        # Initialize RAG components only if enabled
        if config.ENABLE_RAG:
            from rag.vector_store import VectorStore
            from rag.retriever import DocumentLoader
            
            self.vector_store = VectorStore()
            self.doc_loader = DocumentLoader(data_path=rag_data_path)
        else:
            self.vector_store = None
            self.doc_loader = None
            logger.info("ℹ️ RAG is disabled in config")
        
        # Initialize learning system
        from utils.learning_system import TradePerformanceTracker
        self.learning_system = TradePerformanceTracker()
        
        # Load strategy documents into vector store if enabled and empty
        if config.ENABLE_RAG and self.vector_store.count() == 0:
            self._initialize_rag()
        elif config.ENABLE_RAG:
            logger.info(f"✅ RAG knowledge base ready ({self.vector_store.count()} documents)")
        
        logger.info("✅ LLM Decision Engine initialized with self-learning capability")
    
    def _initialize_rag(self):
        """Load PDFs and populate vector store"""
        logger.info("📚 Loading strategy documents...")
        
        # Load all PDFs
        documents = self.doc_loader.load_all_pdfs()
        
        if not documents:
            logger.warning("⚠️ No strategy documents found, creating sample...")
            self.doc_loader.create_sample_document()
            documents = self.doc_loader.load_all_pdfs()
        
        # Add to vector store
        all_texts = []
        all_ids = []
        all_metadatas = []
        
        for doc_name, chunks in documents.items():
            for i, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_ids.append(f"{doc_name}_chunk_{i}")
                all_metadatas.append({"source": doc_name, "chunk_id": i})
        
        if all_texts:
            self.vector_store.add_texts(all_texts, all_ids, all_metadatas)
            logger.info(f"✅ RAG initialized with {len(all_texts)} text chunks")
        else:
            logger.warning("⚠️ No text chunks to add to RAG")
    
    def make_decision(self, context):
        """
        Make final trading decision using RAG + LLM
        
        Args:
            context: Dict with:
                - symbol: Trading symbol
                - technical_signals: Technical analysis results
                - technical_score: Technical score
                - news_sentiment: News sentiment score
                - relevant_news: List of news articles
                - current_price: Current market price
                - direction: Suggested direction from Stage 1
                
        Returns:
            Dict with decision, confidence, entry/SL/TP prices
        """
        symbol = context.get("symbol", "UNKNOWN")
        direction = context.get("direction", "NEUTRAL")
        
        try:
            # ========================================
            # RAG: Retrieve relevant strategy knowledge
            # ========================================
            
            strategy_excerpts = []
            
            if config.ENABLE_RAG:
                # Build query for RAG
                query = f"Trading strategy for {direction} {symbol} with trend alignment and risk management"
                
                logger.debug(f"🔍 Querying RAG for relevant strategies...")
                strategy_excerpts = self.vector_store.query(query, top_k=config.RAG_TOP_K)
                
                if not strategy_excerpts:
                    logger.warning("⚠️ No strategy excerpts retrieved from RAG")
                    strategy_excerpts = ["No specific strategy knowledge available."]
            else:
                strategy_excerpts = ["RAG is disabled. Rely on technicals and patterns."]
            
            # ========================================
            # LEARNING: Get learned patterns
            # ========================================
            
            learned_patterns = None
            try:
                learned_patterns = self.learning_system.get_learned_patterns(days_back=30)
                if learned_patterns:
                    logger.debug(f"🧠 Using {len(learned_patterns)} learned patterns")
            except Exception as e:
                logger.warning(f"Could not load learned patterns: {str(e)}")
            
            # ========================================
            # LLM: Generate decision (with learned patterns)
            # ========================================
            
            system_prompt = get_system_prompt()
            user_prompt = build_decision_prompt(context, strategy_excerpts, learned_patterns)
            
            logger.debug(f"🤖 Calling LLM for decision...")
            
            # Get LLM response
            response_text = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=config.LLM_TEMPERATURE
            )
            
            # RAW LOG (User Request)
            logger.info("=" * 30 + " RAW LLM RESPONSE " + "=" * 30)
            logger.info(response_text if response_text else "EMPTY RESPONSE")
            logger.info("=" * 78)
            
            if not response_text:
                logger.error("❌ LLM yanıt üretemedi")
                return {
                    "decision": "PASS",
                    "confidence": 0,
                    "reasoning": "LLM çıkarımı başarısız",
                    "entry_price": 0,
                    "stop_loss": 0,
                    "take_profit": 0,
                    "risk_reward_ratio": 0
                }
            
            # ========================================
            # Parse and validate response (Yanıtı doğrula)
            # ========================================
            
            decision_data = validate_llm_response(response_text)
            
            if not decision_data:
                logger.error("❌ LLM yanıt doğrulaması başarısız")
                return {
                    "decision": "PASS",
                    "confidence": 0,
                    "reasoning": "Geçersiz LLM yanıt formatı",
                    "entry_price": 0,
                    "stop_loss": 0,
                    "take_profit": 0,
                    "risk_reward_ratio": 0
                }
            
            # ========================================
            # Apply confidence threshold
            # ========================================
            
            if decision_data["confidence"] < config.MIN_CONFIDENCE:
                logger.info(f"⚠️ Güven %{decision_data['confidence']}, eşiğin (%{config.MIN_CONFIDENCE}) altında")
                decision_data["decision"] = "PASS"
                # Failsafe for None reasoning
                current_reason = decision_data.get("reasoning") or ""
                decision_data["reasoning"] = current_reason + f" (Güven %{decision_data['confidence']} < %{config.MIN_CONFIDENCE})"
            
            # Log result
            result_for_log = {
                "pass": decision_data["decision"] != "PASS",
                "confidence": decision_data["confidence"],
                "reason": decision_data["reasoning"]
            }
            log_trade_decision(logger, symbol, 3, result_for_log)
            
            return decision_data
        
        except Exception as e:
            logger.error(f"❌ LLM karar motorunda hata: {str(e)}")
            return {
                "decision": "PASS",
                "confidence": 0,
                "reasoning": f"Karar motoru hatası: {str(e)}",
                "entry_price": 0,
                "stop_loss": 0,
                "take_profit": 0,
                "risk_reward_ratio": 0
            }
