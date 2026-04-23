# Maternal & Newborn Health Chatbot API (Sri Lanka)

This project is an AI-powered chatbot designed to assist with maternal and newborn health queries in Sri Lanka. It utilizes **Retrieval-Augmented Generation (RAG)** to provide accurate, context-aware responses in **Sinhala**, based on provided medical documents and strategic plans.

## 🚀 Features

- **RESTful API (FastAPI)**: High-performance async API ready for Flutter integration.
- **Specialized Knowledge Base**: Built on official documents like "Maternal & Newborn Strat Plan" and healthcare worker guidelines.
- **Sinhala Language Support**: Tailored to respond in Sinhala, acting as a helpful AI health officer.
- **Multimodal Capabilities**: Capable of processing both text questions and images to provide relevant advice.
- **RAG Architecture**: Uses FAISS vector store and HuggingFace embeddings to retrieve relevant context before generating answers with Google Gemini.
- **Interactive API Docs**: Auto-generated Swagger UI at `/docs` and ReDoc at `/redoc`.
- **WSO2 Choreo Ready**: Configured for seamless deployment on [Choreo](https://console.choreo.dev/).

## 🛠️ Technology Stack

- **Python** (Backend Logic)
- **FastAPI** (Web Framework / API Server)
- **Uvicorn** (ASGI Server)
- **LangChain** (LLM Framework)
- **Google Gemini** (Generative AI Model)
- **FAISS** (Vector Database)
- **HuggingFace** (Embeddings)

## 📂 Project Structure

```
chatbot/
├── .choreo/
│   └── component.yaml     # WSO2 Choreo deployment configuration
├── data/                   # Source PDF documents for the knowledge base
├── vectorstore/            # Persisted FAISS vector index (auto-generated)
├── app.py                  # Main FastAPI application entry point
├── openapi.yaml            # OpenAPI 3.0 specification
├── Procfile                # Choreo/PaaS process definition
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API Keys)
└── README.md               # Project documentation
```

## ⚙️ Setup & Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd chatbot
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables**
    Create a `.env` file in the root directory and add your Google API Key:
    ```env
    GOOGLE_API_KEY=your_google_api_key_here
    ```

5.  **Prepare Data**
    Ensure your PDF documents are placed in the `data/` directory. The system looks for:
    - `Maternal & Newborn Strat Plan .pdf`
    - `maternal_care_healthcare_workers.pdf`

## 🏃‍♂️ Running Locally

```bash
python app.py
```

Or using Uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

*On the first run, the system will process the PDFs in the `data/` folder to build the vector index. This may take a few moments.*

The server runs at `http://localhost:8000`.

## 📡 API Endpoints

### Health Check
**GET** `/health`

Returns the health status and knowledge base status.

### Chat
**POST** `/chat`

**Request Body (JSON):**
```json
{
  "question": "මාතෘ සෞඛ්‍ය යනු කුමක්ද?",
  "image": "(Optional) Base64 encoded image string"
}
```

**Response (JSON):**
```json
{
  "answer": "Generated answer in Sinhala...",
  "error": null
}
```

### Interactive API Docs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📱 Flutter Integration

To call this API from your Flutter app:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<String> sendMessage(String question, {String? imageBase64}) async {
  final uri = Uri.parse('https://YOUR_CHOREO_URL/chat');
  
  final body = {
    'question': question,
    if (imageBase64 != null) 'image': imageBase64,
  };

  final response = await http.post(
    uri,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode(body),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return data['answer'];
  } else {
    throw Exception('Failed to get response');
  }
}
```

## 🚀 Deploy on WSO2 Choreo

1. Push this project to a **GitHub repository**.
2. Go to [console.choreo.dev](https://console.choreo.dev/) and create a new **Service** component.
3. Connect your GitHub repository.
4. Configure:
   - **Build Preset**: Python
   - **Language Version**: 3.11+
   - **Component Directory**: `/` (root)
5. Add the **`GOOGLE_API_KEY`** environment variable in Choreo's config settings.
6. Build & Deploy.
7. Use the generated Choreo URL in your Flutter app.

## ⚠️ Notes

- The system is configured to **only** answer questions related to maternal and child health.
- Responses are generated using `gemini-flash-latest`.
- This tool is for informational purposes and does not replace professional medical advice.

