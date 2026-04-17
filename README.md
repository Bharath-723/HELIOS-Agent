# HELIOS - AI-Powered Desktop Assistant

HELIOS is an intelligent desktop automation and assistance system that uses natural language processing and AI to help with various tasks including file management, email composition, web search, note-taking, and system controls.

## Features

- 🤖 Natural Language Understanding & Routing
- 📧 Gmail Integration
- 🔍 Web Search
- 📝 Notes Management
- 📄 File Creation & Management
- ⏰ Task Scheduling
- 🖥️ System Controls
- 💬 Chat History Tracking

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/HELIOS.git
   cd HELIOS
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   - Create a `.env` file with your API keys and configuration

6. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

- `core/` - Core modules (LLM engine, NL router)
- `modules/` - Feature modules (chat, email, search, etc.)
- `data/` - Data storage (chat history, notes, scheduled tasks)
- `main.py` - Entry point
- `agent.py` - Agent implementation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

M Bharath
