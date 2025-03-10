# ailocalsearch
A simple local search application based on AI.

## Installation Guide

### Prerequisites

- Python 3.12 or higher
- Node.js 23 or higher and npm
- OpenAI API key

### Backend Setup

1. Clone the repository:
   ```
   git clone https://github.com/gaopenghigh/ailocalsearch.git
   cd ailocalsearch
   ```

2. Set up a Python virtual environment (recommended):
   ```
   cd server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```
   pip install -r requirements.txt
   cd ..
   ```

4. Configure environment variables:
   ```
   cp server/.env.example server/.env
   ```

5. Edit the `.env` file and replace the placeholder values with your actual API keys:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

### Frontend Setup

1. Install frontend dependencies:
   ```
   brew install node
   cd web
   npm install
   ```

2. Build the frontend for production:
   ```
   npm run build
   cd ..
   ```

### Download and install the data

```
# Download to ~/Downloads/data_20250305.tar.gz
# untar into server/
cd server && tar xvzf ~/Downloads/data_20250305.tar.gz
``` 

## Development

### Frontend Development

If you're modifying the frontend code:

1. Make your changes in the `web/` directory
2. Rebuild the frontend:
   ```
   cd web
   npm run build
   cd ..
   ```

For frontend-only development with hot reloading, you can run:
```
cd web
npm start
```
This will start a development server at http://localhost:3000 that automatically reloads when you make changes. Note that the API calls will still go to the backend server at http://localhost:5001.

# Run

```
python server/app.py
```
Will listen to 5001 port.

## Note

Never commit your `.env` file to version control. It's already added to `.gitignore` for your safety.
