# AI Financial Chatbot  
**(LangChain + Ollama + Vector Search)**

An AI-powered financial chatbot system designed to answer banking and finance-related queries using semantic search, vector embeddings, and local large language models.  
This project demonstrates the integration of NLP, AI, and backend engineering to build an intelligent financial assistant.

---

## 🚀 Project Overview

The AI Financial Chatbot is built to simulate a real-world financial support system that can:
- Answer financial FAQs
- Understand user intent using embeddings
- Retrieve relevant financial information
- Perform predictive analysis
- Manage user sessions and chat history
- Support admin-side operations

It uses modern AI architecture including vector databases and LLM pipelines.

---

## ✨ Features

- 💬 Intelligent financial chatbot  
- 📚 Vector-based semantic search (FAISS)  
- 🧠 LLM integration using Ollama  
- 🔍 Context-aware question answering  
- 🧾 Chat history management  
- 👤 User session handling  
- 🛠 Admin backend system  
- 📈 Predictive financial analysis module  
- 📂 Modular project architecture  

---

## 🧱 Tech Stack

- **Language:** Python  
- **LLM Framework:** LangChain  
- **LLM Engine:** Ollama  
- **Vector DB:** FAISS  
- **Backend:** Flask  
- **Database:** SQLite  
- **AI Models:** Local LLMs  
- **Embedding Engine:** Vector embeddings  
- **Environment:** Virtual Environment (venv)  

---

## 📁 Project Structure

financial_chatbot/
│
├── app.py # Main application entry point
├── chatbot_logic.py # Core chatbot logic
├── admin_backend.py # Admin backend system
├── session_manager.py # Session & user handling
├── predictive_model.py # ML prediction logic
├── predictive_analysis.py # Financial analysis module
├── create_vector_store.py # Vector store creation
├── create_admin_db.py # Admin DB setup
│
├── data/ # Financial datasets
├── models/ # ML/AI models
├── vector_store/ # FAISS vector database
├── chat_history/ # Chat logs (local only)
│
├── users.json # User data
├── requirements.txt # Dependencies
├── .gitignore # Git ignore rules
└── README.md # Documentation


---

## ⚙️ Setup Instructions (macOS)

### 1️⃣ Install Ollama
```bash
brew install ollama
ollama pull llama3

2️⃣ Clone Repository
git clone https://github.com/Karanshah012/financial-chatbot.git
cd financial-chatbot

3️⃣ Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

4️⃣ Install Dependencies
pip install -r requirements.txt

5️⃣ Run Application
python app.py

🧠 System Architecture (High Level)

User Query
→ NLP Processing
→ Embedding Generation
→ Vector Search (FAISS)
→ Context Retrieval
→ LLM Response Generation (Ollama)
→ Response Output

📌 Use Case Examples

Banking FAQ assistant

Finance support chatbot

AI helpdesk system

Educational finance assistant

Enterprise financial assistant prototype

🔮 Future Enhancements

🌐 Web frontend UI

☁️ Cloud deployment

🔐 Authentication system

📱 Mobile app integration

📊 Dashboard analytics

🤖 Multi-agent AI system

🧠 Fine-tuned financial LLM

👨‍💻 Developer

Karan Shah
AI/ML Enthusiast | Financial AI Systems | Chatbot Developer

📜 License

This project is for educational and research purposes.
