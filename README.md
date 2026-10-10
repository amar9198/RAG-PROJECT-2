# 🧠 Deep Learning RAG Chat Assistant

An AI-powered **Retrieval-Augmented Generation (RAG)** application that allows users to ask questions about deep learning documents and receive context-aware answers using semantic search and large language models.

🔗 **Live Demo:** [Try the RAG Chat Assistant](https://rag-project-2-zpubvdumfp9hand7zueyu9.streamlit.app/)

💻 **GitHub Repository:** [RAG-PROJECT-2](https://github.com/amar9198/RAG-PROJECT-2)

---

## 📌 Project Overview

The Deep Learning RAG Chat Assistant combines document processing, vector embeddings, semantic retrieval, and generative AI to answer questions using relevant document content.

Instead of relying only on a language model's existing knowledge, the application retrieves relevant information from a document and uses it as context to generate answers.

This project demonstrates how modern AI technologies can be combined to build an interactive document question-answering system.

## ✨ Features

- 📄 **Document Processing:** Load and process documents for retrieval.
- ✂️ **Text Splitting:** Divide documents into manageable chunks.
- 🔎 **Semantic Search:** Find relevant content using vector embeddings.
- 🗄️ **Vector Database:** Store and retrieve document embeddings using ChromaDB.
- 🤖 **AI-Powered Answers:** Generate context-aware responses using a Groq-hosted language model.
- 💬 **Interactive Chat Interface:** Ask questions through a Streamlit application.
- 🎯 **MMR Retrieval:** Retrieve relevant and diverse document chunks.
- 🔗 **Modular Architecture:** Separate document loaders, retrievers, database utilities, and RAG pipeline logic.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application interface |
| LangChain | RAG pipeline orchestration |
| ChromaDB | Vector storage and similarity search |
| Mistral AI | Text embedding generation |
| Groq | Language model inference |
| PyPDF / document loaders | Document ingestion |
| Git and GitHub | Version control and source code hosting |

## ⚙️ How It Works

1. **Document Loading:** The application loads the source document.
2. **Text Chunking:** The document is divided into smaller text segments.
3. **Embedding Generation:** Text segments are converted into vector embeddings.
4. **Vector Storage:** The embeddings are stored in ChromaDB.
5. **Question Processing:** The user submits a question through the chat interface.
6. **Relevant Retrieval:** The retriever searches for relevant document chunks.
7. **Answer Generation:** The language model uses the retrieved context to generate an answer.
8. **Response Display:** The answer is presented to the user through Streamlit.

## 🏗️ Project Structure

```text
RAG-PROJECT-2/
│
├── app.py
├── app2.py
├── main.py
├── page.py
├── rag_pipeline.py
├── database.py
├── create_database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── retrievers/
│   ├── arxiv_retriever.py
│   ├── mmr.py
│   └── multiquery.py
│
├── documents loaders/
├── data/
├── chroma_db/
└── vector_store/
```

*Note: The structure above is illustrative. Adjust filenames and folders to match the actual files in your repository. The deployed Streamlit entry point may differ.*

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/amar9198/RAG-PROJECT-2.git
cd RAG-PROJECT-2
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure API keys

Create a `.env` file in the project root if your application uses `python-dotenv`.

```env
MISTRAL_API_KEY=your_mistral_api_key
GROQ_API_KEY=your_groq_api_key
```

Replace the placeholder values with your own API keys.

**Security:** Never commit `.env` or expose your API keys publicly.

### 5. Run the application

If the Streamlit entry point is `app.py`:

```bash
streamlit run app.py
```

If your application uses `app2.py` instead:

```bash
streamlit run app2.py
```

Use the entry point configured for your application.

## ☁️ Deployment

This application is deployed using Streamlit Community Cloud.

**Live application:** [RAG-PROJECT-2](https://rag-project-2-zpubvdumfp9hand7zueyu9.streamlit.app/)

To deploy your own version:

1. Push the project to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect your GitHub repository.
4. Select the appropriate branch and Streamlit entry-point file.
5. Add the required API keys under the application's Secrets settings.
6. Deploy the application.

## 🔐 Environment Variables

Configure the API keys required by your application in your local `.env` file or Streamlit Secrets.

```toml
MISTRAL_API_KEY = "your_mistral_api_key"
GROQ_API_KEY = "your_groq_api_key"
```

Only include environment variables that your code actually uses. Never publish real credentials in your repository.

## 🎯 Use Cases

- Question answering over deep learning documents
- AI-powered document research
- Semantic search and information retrieval
- Learning and exploring RAG architectures
- Building knowledge assistants over custom documents

## 🔮 Future Improvements

- Support for multiple PDF and document uploads
- Chat history and conversational memory
- Source citations for generated answers
- Improved error handling and API key validation
- Support for additional document formats
- Enhanced user interface and retrieval evaluation

## 👨‍💻 Author

**Amar Prajapati**

GitHub: [@amar9198](https://github.com/amar9198)

## 📄 License

Add a license to this repository if you intend to distribute or reuse the project under specific terms.

---

⭐ If you find this project useful, consider starring the repository!
