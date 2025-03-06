# ailocalsearch
A simple local search application based on AI.

## Environment Setup

This application uses environment variables to store API keys and other sensitive information. Follow these steps to set up your environment:

1. Navigate to the server directory
2. Copy the `.env.example` file and rename it to `.env`:
   ```
   cp server/.env.example server/.env
   ```
3. Edit the `.env` file and replace the placeholder values with your actual API keys:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```
4. Install the required dependencies:
   ```
   pip install -r server/requirements.txt
   ```

## Running the Application

To run the application:

1. Start the server:
   ```
   cd server
   python app.py
   ```
2. Follow the web client setup instructions (if applicable)

Note: Never commit your `.env` file to version control. It's already added to `.gitignore` for your safety.
