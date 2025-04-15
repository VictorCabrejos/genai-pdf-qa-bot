# Student Setup Guide for GenAI PDF Q&A Bot

> **Updated: April 15, 2025** - This guide now includes PostgreSQL setup instructions following the database migration.

This guide will walk you through the process of setting up and running the GenAI PDF Q&A Bot project on your local machine. Follow these steps carefully to ensure you have a working development environment.

## Prerequisites

Before you begin, make sure you have the following software installed on your computer:

- **Python 3.11** or higher ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **PostgreSQL 14+** ([Download PostgreSQL](https://www.postgresql.org/download/))
- **Visual Studio Code** (recommended, but any code editor will work) ([Download VS Code](https://code.visualstudio.com/download))

## Step 1: Clone the Repository

1. Open your terminal or command prompt
2. Navigate to the directory where you want to store the project
3. Clone the repository by running:

```bash
git clone https://github.com/yourusername/genai-pdf-qa-bot.git
cd genai-pdf-qa-bot
```

## Step 2: Set Up a Python Virtual Environment

Creating a virtual environment keeps the project dependencies isolated from your system Python installation.

### For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### For macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Once activated, your terminal prompt should change to indicate that you're now working within the virtual environment.

## Step 3: Install Dependencies

Install all required packages using pip:

```bash
pip install -r requirements.txt
```

This may take a few minutes as it installs all necessary libraries including FastAPI, SQLAlchemy, OpenAI, and other dependencies.

## Step 4: Set Up PostgreSQL Database

The application now uses PostgreSQL for data storage. Follow these steps to set up the database:

1. **Install PostgreSQL**:
   - Follow the instructions for your operating system at [postgresql.org/download](https://www.postgresql.org/download/)
   - Remember your PostgreSQL admin password during installation

2. **Create a Database**:
   - For Windows: Open pgAdmin (installed with PostgreSQL)
   - For macOS/Linux: Open terminal and connect to PostgreSQL:
     ```bash
     sudo -u postgres psql
     ```
   - Create a new database:
     ```sql
     CREATE DATABASE pdf_qa_bot;
     ```
   - (Optional) Create a dedicated user:
     ```sql
     CREATE USER pdf_user WITH PASSWORD 'your_password';
     GRANT ALL PRIVILEGES ON DATABASE pdf_qa_bot TO pdf_user;
     ```

3. **Install pgvector Extension**:
   - Follow installation instructions at [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
   - Once installed, enable the extension in your database:
     ```sql
     \c pdf_qa_bot
     CREATE EXTENSION vector;
     ```

## Step 5: Get an OpenAI API Key

The application requires an OpenAI API key to function:

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in to your OpenAI account
3. Navigate to the API section
4. Create a new API key
5. Copy the API key (you'll need it in the next step)

> **Important**: OpenAI API usage incurs costs based on the number of tokens processed. As a student, be mindful of your usage. You can set billing limits in the OpenAI dashboard to avoid unexpected charges.

## Step 6: Set Up Environment Variables

1. Create a file named `.env` in the root directory of the project
2. Add your configuration to the file:

```
# OpenAI API Key
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost/pdf_qa_bot
# Or if you created a dedicated user:
# DATABASE_URL=postgresql://pdf_user:your_password@localhost/pdf_qa_bot

# Security
JWT_SECRET_KEY=your_secret_key_here

# API configuration
PORT=8000
HOST=0.0.0.0
```

Replace placeholders with your actual values.

> **Security Note**: Never commit your `.env` file to version control. The `.gitignore` file should already be configured to exclude it.

## Step 7: Run Database Migrations

Initialize the database schema:

```bash
alembic upgrade head
```

This will create all necessary tables in your PostgreSQL database.

## Step 8: Run the Application

Start the FastAPI server with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The `--reload` flag enables auto-reloading when you make changes to the code, which is helpful during development.

You should see output indicating that the server is running, usually at `http://127.0.0.1:8000`.

## Step 9: Access the Application

Open your web browser and navigate to:

```
http://127.0.0.1:8000
```

You should now see the landing page of the GenAI PDF Q&A Bot, featuring an animated PDF robot.

## Common Issues and Troubleshooting

### Database Connection Issues

If you encounter database errors:
- Verify your PostgreSQL service is running
- Check that your database credentials in `.env` are correct
- Ensure you've run the migrations with `alembic upgrade head`
- Make sure the pgvector extension is properly installed

### API Key Issues

If you see errors related to authentication with OpenAI, check:
- Your API key is correctly set in the `.env` file
- Your OpenAI account has billing set up
- You have sufficient credits in your OpenAI account

### Migration Errors

If Alembic migration fails:
- Check PostgreSQL is running
- Ensure your database connection string is correct
- Try running migrations with verbosity: `alembic upgrade head --verbose`

### Module Not Found Errors

If Python complains about missing modules:
- Make sure you've activated the virtual environment
- Try reinstalling dependencies: `pip install -r requirements.txt`

### Port Already in Use

If port 8000 is already in use, you can specify a different port:

```bash
uvicorn app.main:app --reload --port 8001
```

## Working with the Application

### Creating an Account

1. Click "Sign Up" on the landing page
2. Enter your details to create a new account
3. Log in with your credentials

### Uploading PDFs

1. After logging in, you'll see your dashboard
2. Click "Upload PDF" to add a document
3. Wait for the processing to complete (this includes text extraction and embedding generation)

### Asking Questions

1. Click on a PDF in your dashboard
2. Use the question interface to ask questions about the document
3. The system will retrieve relevant parts of the document and generate an answer

### Generating Quizzes

1. Navigate to the Quiz section
2. Select a PDF from your library
3. Configure the number of questions and difficulty level
4. Click "Generate Quiz" to create a quiz based on the document content
5. Answer the questions and get immediate feedback

## Extending the Project

As a software engineering student, you might want to extend or modify the project. Here are some tips:

- The project follows a Service-Oriented MVC architecture
- Review the [Technical Architecture Overview](../architecture/technical-overview.md) to understand the components
- Backend code is in the `app/` directory
- Frontend templates are in the `templates/` directory
- AI functionality is primarily in the `app/services/` directory

## Contributing to the Project

If you make improvements or bug fixes, consider contributing them back:

1. Create a fork of the repository
2. Make your changes in a new branch
3. Test thoroughly
4. Submit a pull request with a clear description of your changes

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [LangChain Documentation](https://langchain.readthedocs.io/)
- [Python Virtual Environments Guide](https://docs.python.org/3/library/venv.html)

---

If you encounter any problems not covered in this guide, please reach out to your instructor for assistance.