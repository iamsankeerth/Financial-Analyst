<p align="center">
  <img src="https://img.icons8.com/fluency/96/stocks-growth.png" alt="Financial Analyst" width="96" height="96">
  <h1 align="center">Financial Analyst AI</h1>
</p>

<p align="center">
  <strong>AI-Powered Stock Analysis Tool with Semantic Memory</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/SvelteKit-5.0+-orange?logo=svelte&logoColor=white" alt="SvelteKit">
  <img src="https://img.shields.io/badge/Gemini-2.0-blue?logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/mem0-Semantic%20Memory-purple" alt="mem0">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi&logoColor=white" alt="FastAPI">
</p>

---

## 📖 Overview

**Financial Analyst AI** is an intelligent stock analysis tool that uses Google's Gemini LLM to generate Python code for financial visualization and analysis. It features **semantic memory** powered by mem0, allowing the AI to remember context from previous conversations and provide coherent follow-up responses.

### ✨ Key Features

- 🤖 **AI-Powered Analysis** - Uses Gemini 2.0 Flash for intelligent code generation
- 🧠 **Semantic Memory** - mem0 enables context retention across conversations
- 📊 **Real-time Charts** - Dynamic matplotlib visualizations for stocks, crypto, and indices
- 💹 **Multi-Asset Support** - Analyze stocks (AAPL, MSFT), crypto (BTC-USD), indices (^GSPC), commodities (GLD)
- 🔄 **Follow-up Questions** - Ask "What about the correlation?" and the AI remembers the context
- 🌙 **Dark Theme UI** - Modern SvelteKit frontend with glassmorphism design

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Svelte Frontend (Port 5173)                  │
│                    - Chat Interface                             │
│                    - Chart Display                              │
│                    - Code Viewer                                │
└─────────────────────────────┬───────────────────────────────────┘
                              │ POST /analyze
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8000)                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ mem0.search │ -> │ Gemini LLM  │ -> │  mem0.add   │         │
│  │  (context)  │    │ (generate)  │    │  (store)    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
| :--- | :--- |
| **Python 3.11+** | Core runtime |
| **FastAPI** | REST API framework |
| **LangChain** | LLM orchestration |
| **Google Gemini 2.0** | AI code generation |
| **mem0** | Semantic memory layer |
| **yfinance** | Real-time stock data |
| **matplotlib** | Chart generation |
| **pandas** | Data manipulation |

### Frontend
| Technology | Purpose |
| :--- | :--- |
| **SvelteKit 5** | Frontend framework |
| **TypeScript** | Type safety |
| **TailwindCSS** | Styling |
| **Convex** | Backend-as-a-service |
| **Vite** | Build tool |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ and pnpm
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/iamsankeerth/Financial-Analyst.git
cd Financial-Analyst

# Switch to backend branch
git checkout feature/financial-analyst-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env

# Start the backend server
python api_server.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

```bash
# Switch to frontend branch
git checkout feature/financial-analyst-frontend

# Install dependencies
pnpm install

# Create .env file with Convex URL
cp .env.example .env

# Start Convex development server (in a separate terminal)
npx convex dev

# Start the frontend
pnpm dev
```

The frontend will start on `http://localhost:5173`

---

## ⚙️ Configuration

### Environment Variables

#### Backend (`.env`)
```env
GOOGLE_API_KEY=your_gemini_api_key_here
# or
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Frontend (`.env`)
```env
PUBLIC_CONVEX_URL=your_convex_deployment_url
BETTER_AUTH_SECRET=your_auth_secret
GITHUB_CLIENT_ID=your_github_oauth_id
GITHUB_CLIENT_SECRET=your_github_oauth_secret
```

---

## 📝 Usage Examples

### Basic Queries

| Query | Description |
| :--- | :--- |
| "Show me Apple stock for the last 6 months" | Single stock chart |
| "Compare AAPL and MSFT with 50-day moving averages" | Multi-stock comparison |
| "Analyze correlation between Bitcoin and S&P 500" | Correlation analysis |
| "What's the current price of Tesla?" | Real-time price |

### Follow-up Questions

The AI remembers context from previous queries:

1. **You:** "Analyze the correlation between Bitcoin and S&P 500"
2. **AI:** Shows correlation chart (0.27)
3. **You:** "What does this correlation mean?"
4. **AI:** Explains the 0.27 correlation (knows you're talking about BTC/S&P)

---

## 📁 Project Structure

```
Financial-Analyst/
├── feature/financial-analyst-backend/
│   ├── api_server.py          # FastAPI REST endpoints
│   ├── finance_crew.py        # LLM + mem0 integration
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # API keys (not committed)
│
└── feature/financial-analyst-frontend/
    ├── src/
    │   ├── routes/
    │   │   ├── chat/          # Chat interface
    │   │   ├── account/       # User settings
    │   │   └── api/           # API routes
    │   └── lib/
    │       ├── components/    # UI components
    │       └── backend/       # Convex functions
    ├── convex/                # Convex schema & functions
    └── package.json           # Node dependencies
```

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/analyze` | Analyze a stock query |
| `GET` | `/health` | Health check |
| `GET` | `/memories/{user_id}` | Get user's stored memories |
| `DELETE` | `/memories/{user_id}` | Clear user's memories |

### Example Request

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me Tesla stock for 3 months", "user_id": "user123"}'
```

---

## 🧠 How mem0 Works

mem0 provides **semantic memory** instead of raw chat history:

| Traditional Chat History | mem0 Semantic Memory |
| :--- | :--- |
| Stores raw messages | Extracts semantic facts |
| "Show AAPL vs MSFT correlation" | "User analyzed AAPL/MSFT correlation = 0.89" |
| Limited context window | Infinite memory via vector search |
| Exact string matching | Semantic similarity matching |

This allows the AI to understand follow-up questions like "What about adding moving averages?" even without explicit mention of the stocks.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) for the LLM
- [mem0](https://mem0.ai/) for semantic memory
- [yfinance](https://github.com/ranaroussi/yfinance) for stock data
- [thom.chat](https://github.com/TGlide/thom-chat) for UI inspiration

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/iamsankeerth">@iamsankeerth</a>
</p>
