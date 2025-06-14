# 🤖 DocChat AI - Chat with Any Documentation

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.31.0-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

DocChat AI is a powerful RAG-based chatbot that lets you have intelligent conversations with any documentation website. Simply provide a documentation URL, and DocChat AI will crawl it, understand it, and answer your questions with code examples and references.

![DocChat AI Demo](https://via.placeholder.com/800x400/0e1117/00d4ff?text=DocChat+AI+Demo)

## ✨ Features

- 🌐 **Universal Documentation Support** - Works with any documentation site
- 🤖 **AI-Powered Q&A** - Accurate answers using GPT-4
- 📝 **Code Examples** - Syntax highlighting with one-click copy
- 🌓 **Dark/Light Mode** - Automatic theme detection
- 📱 **Fully Responsive** - Works on desktop, tablet, and mobile
- ⚡ **Real-time Progress** - See what's happening during processing
- 💾 **Persistent Storage** - Documentation stays indexed for instant access

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Qdrant (local Docker or cloud)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/docchat-ai.git
cd docchat-ai
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. **Start Qdrant** (choose one)

Option A - Local Docker:
```bash
docker-compose up -d
```

Option B - Use Qdrant Cloud:
- Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
- Update `.env` with cloud credentials

5. **Run the app**
```bash
streamlit run app.py
```

## 🧪 Tested Documentation Sites

- ✅ Python: `https://docs.python.org/3/`
- ✅ React: `https://react.dev/learn`
- ✅ FastAPI: `https://fastapi.tiangolo.com/`
- ✅ Django: `https://docs.djangoproject.com/`
- ✅ And many more!

## 📖 Usage

1. **Add Documentation**: Enter a documentation URL in the sidebar
2. **Wait for Processing**: The app will crawl and index the documentation
3. **Start Chatting**: Ask questions and get instant answers with code examples

## 🚂 Deployment

### Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Click the button above
2. Add your environment variables
3. Deploy!

See [deployment guide](railway-deployment.md) for detailed instructions.

## 🛠️ Configuration

Adjust settings in `backend/scraper.py`:
- `max_pages`: Number of pages to crawl (default: 50)
- `chunk_size`: Size of text chunks (default: 1500)
- `chunk_overlap`: Overlap between chunks (default: 200)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenAI](https://openai.com/) and [Qdrant](https://qdrant.tech/)
- Documentation parsing with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

## 📧 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter)

Project Link: [https://github.com/yourusername/docchat-ai](https://github.com/yourusername/docchat-ai)

---

Made with ❤️ by the DocChat AI Team