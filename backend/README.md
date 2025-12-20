# Sniper Trading Bot

A production-ready algorithmic trading system optimized for **NVIDIA RTX 3050 (4GB VRAM)** that operates as a "Sniper" - making few but highly accurate trades through a three-tier filtering mechanism.

## 🎯 Philosophy

**Quality over Quantity**: This bot doesn't make 100 trades per day hoping for 51% success. It waits for perfect conditions and might make only 1 trade per day (or even zero), but with a very high win rate.

## 🏗️ Architecture

### Three-Tier Filtering System

1. **Stage 1: Technical Hard Filter** (No GPU, <0.1s)
   - Eliminates 90%+ of potential trades immediately
   - RSI, MACD, multi-timeframe trend analysis
   - Volume confirmation
   - Minimum score: 70/100

2. **Stage 2: News Sentiment** (SQL only, <0.5s)
   - Validates trade direction with fundamental data
   - Checks if news sentiment aligns with technical signals
   - SQL database of pre-scored financial news

3. **Stage 3: RAG + LLM Decision** (GPU: 2.5-4GB VRAM, 2-5s)
   - **Only loads if Stage 1 & 2 pass** (Lazy loading)
   - Retrieves relevant strategies from vector database
   - LLM makes final decision with 90%+ confidence requirement
   - Uses Llama 3.2 3B or Llama 3.1 8B (quantized)

## 📋 Prerequisites

### Software
- Python 3.9+
- MetaTrader 5
- Ollama (for local LLM)

### Hardware
- Minimum: 8GB RAM, any GPU
- Recommended: 16GB RAM, NVIDIA RTX 3050 4GB

## 🚀 Installation

### 1. Clone or Download Project
```bash
cd yatırımdanışmanı-al
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Ollama and Pull Model
Download Ollama from [ollama.ai](https://ollama.ai)

```bash
# Pull lightweight model (recommended)
ollama pull llama3.2:3b

# OR pull more capable model
ollama pull llama3.1:8b-instruct-q4_K_M
```

### 5. Configure MT5 Credentials
Copy `.env.example` to `.env` and fill in your details:

```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

Edit `.env`:
```
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

### 6. Add Strategy PDFs (Optional)
Place your trading strategy PDF books in:
```
data/strategies/
```

If no PDFs are added, a sample strategy will be created automatically.

## 🎮 Usage

### Start the Bot
```bash
python main.py
```

### Configuration
Edit `config.py` to adjust:
- Trading symbols (default: EURUSD, GBPUSD, XAUUSD)
- Risk per trade (default: 1%)
- Check interval (default: 5 minutes)
- Technical thresholds (RSI, MACD, etc.)
- LLM model selection
- Confidence requirements

### Add News Data (Optional)
```python
from filters.stage2_news import NewsFilter

nf = NewsFilter()
nf.add_sample_news()  # Add test data
```

For production, integrate with a news API to populate the database.

## 📊 Expected Performance

- **Trades per day**: 0-5 (Sniper mode)
- **Win rate target**: >70%
- **Average confidence**: >92%
- **Risk/Reward ratio**: Minimum 2:1

## 🛠️ Project Structure

```
sniper-trading-bot/
├── main.py                    # Main trading loop
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
├── .env                      # Credentials (not in git)
│
├── core/                     # Core trading modules
│   ├── broker.py            # MT5 connection
│   ├── data_fetcher.py      # Market data
│   └── risk_manager.py      # Position sizing
│
├── filters/                  # Three-tier filters
│   ├── stage1_technical.py  # Technical analysis
│   ├── stage2_news.py       # News sentiment
│   └── stage3_llm.py        # RAG + LLM decision
│
├── rag/                      # RAG components
│   ├── vector_store.py      # ChromaDB management
│   └── retriever.py         # PDF processing
│
├── llm/                      # LLM components
│   ├── ollama_client.py     # Ollama API
│   └── prompts.py           # System prompts
│
├── database/                 # SQL database
│   ├── news_db.py           # News operations
│   └── schema.sql           # Database schema
│
├── utils/                    # Utilities
│   └── logger.py            # Logging
│
├── data/                     # Data storage
│   ├── strategies/          # PDF strategy books
│   └── embeddings/          # Vector database
│
└── logs/                     # Log files
```

## ⚙️ Customization

### Change LLM Model
Edit `config.py`:
```python
LLM_MODEL = "llama3.2:3b"  # Fast, <3GB VRAM
# LLM_MODEL = "llama3.1:8b-instruct-q4_K_M"  # Better reasoning, ~4GB VRAM
```

### Adjust Risk
Edit `config.py`:
```python
RISK_PERCENT = 1.0  # Risk 1% per trade
MIN_RISK_REWARD_RATIO = 2.0  # Minimum 2:1 reward
```

### Add Trading Symbols
Edit `config.py`:
```python
SYMBOLS = ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"]
```

## 🐛 Troubleshooting

### "MT5 initialization failed"
- Make sure MetaTrader 5 is installed
- Verify credentials in `.env`
- Check if MT5 terminal is running

### "Ollama server not responding"
```bash
ollama serve  # Start Ollama server
```

### "Model not found"
```bash
ollama pull llama3.2:3b
```

### "No PDF files found"
This is normal for first run. The system will create a sample strategy. Add your own PDFs to `data/strategies/` for better results.

## 📝 License

This project is for educational purposes. Trading involves risk. Always test on a demo account first.

## ⚠️ Disclaimer

**This bot is for educational purposes only.** Trading financial instruments involves substantial risk and can result in the loss of your capital. Never trade with money you cannot afford to lose. Always thoroughly test any algorithmic trading system on a demo account before using real funds.

## 🤝 Contributing

Contributions welcome! Please test changes thoroughly on demo accounts.

## 📞 Support

For issues, please check:
1. MT5 connection is working
2. Ollama is running (`ollama serve`)
3. Model is downloaded (`ollama list`)
4. `.env` file is configured correctly
