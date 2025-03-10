import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [inputQuery, setInputQuery] = useState('');
  const [followUpQuery, setFollowUpQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [assistantName, setAssistantName] = useState('AI Local Knowledge Search');
  const [history, setHistory] = useState([]);
  const [isNewAnswer, setIsNewAnswer] = useState(false);
  const conversationEndRef = useRef(null);
  
  // Define base URL for API calls - use absolute URL in development, relative in production
  const baseUrl = process.env.NODE_ENV === 'development' 
    ? 'http://localhost:5001' 
    : '';

  // Fetch assistant description when component mounts
  useEffect(() => {
    fetch(`${baseUrl}/api/description`)
      .then(response => response.json())
      .then(data => {
        setAssistantName(data.name);
        document.title = data.name; // Update the page title as well
      })
      .catch(error => {
        console.error('Error fetching assistant description:', error);
      });
  }, [baseUrl]);

  // Modify the useEffect to only scroll when follow-up box appears
  useEffect(() => {
    // Only scroll if we have history and we're not loading (same condition as follow-up box display)
    if (history.length > 0 && !loading) {
      scrollToBottom();
    }
  }, [history, loading]);

  // Add animation effect for new answers
  useEffect(() => {
    if (response && !loading) {
      setIsNewAnswer(true);
      const timer = setTimeout(() => {
        setIsNewAnswer(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [response, loading]);

  const scrollToBottom = () => {
    // Scroll the entire viewport instead of just the conversation container
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    });
    
    // Also scroll the conversation end ref as a fallback
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendQuery = (query, isFollowUp = false) => {
    if (query) {
      setLoading(true);
      setResponse(''); // Clear any previous response
      
      const requestData = {
        query: query,
        history: history
      };
      
      // Use POST instead of GET
      fetch(`${baseUrl}/api/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          setResponse(data.answer);
          setLoading(false);
          
          // Update with history from server response
          if (data.history && Array.isArray(data.history)) {
            setHistory(data.history);
          } else {
            // Fallback if server doesn't return history
            const newEntry = {
              question: query,
              answer: data.answer
            };
            setHistory(prevHistory => [...prevHistory, newEntry]);
          }
          
          // Clear the input fields
          if (isFollowUp) {
            setFollowUpQuery('');
          } else {
            setInputQuery('');
          }
        })
        .catch(error => {
          console.error('Error fetching answer:', error);
          setResponse(`Error: ${error.message}`);
          setLoading(false);
        });
    }
  };

  const handleAnswer = (e) => {
    e.preventDefault(); 
    const formData = new FormData(e.target);
    const query = formData.get('query');
    
    if (query) {
      setInputQuery(query);
      sendQuery(query);
    }
  };

  const handleFollowUp = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const query = formData.get('followUpQuery');
    
    if (query) {
      setFollowUpQuery(query);
      sendQuery(query, true);
    }
  };

  const handleNewChat = () => {
    // Clear all conversation state
    setInputQuery('');
    setFollowUpQuery('');
    setResponse('');
    setHistory([]);
    setIsNewAnswer(false);
  };

  return (
    <div className="App">
      <h1 className="app-title">{assistantName}</h1>
      
      {/* Google-style query input - only show when there's no history and not loading */}
      {(history.length === 0 && !loading) && (
        <div className="centered-container">
          <form onSubmit={handleAnswer} className="form-container">
            <div className="google-search-box">
              <div className="search-icon">
                <svg focusable="false" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
                  <path fill="#9aa0a6" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path>
                </svg>
              </div>
              <input
                type="text"
                name="query"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask a question about local knowledge..."
                className="google-search-input"
                autoComplete="off"
                autoCorrect="off"
                spellCheck="false"
                autoCapitalize="off"
              />
              <div className="search-actions">
                <button 
                  type="button"
                  onClick={handleNewChat}
                  className="icon-button"
                  title="Clear and start a new chat"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4285f4">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="google-buttons">
              <button 
                type="submit" 
                disabled={loading}
                className="google-button"
              >
                {loading ? 'Loading...' : 'Ask'}
              </button>
              <button 
                type="button" 
                onClick={handleNewChat}
                className="google-button"
              >
                New
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Conversation history */}
      <div className="conversation-container">
        {history.length > 0 ? (
          <div className="conversation-history">
            {history.map((entry, index) => (
              <div key={index} className={index === history.length - 1 && isNewAnswer ? 'fade-in' : ''}>
                <div className="question-box">
                  <p className="question-text">{entry.question}</p>
                </div>
                <div className="answer-box">
                  {index === history.length - 1 && isNewAnswer ? (
                    <div className="typewriter-text">
                      <ReactMarkdown>
                        {entry.answer}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <ReactMarkdown>
                      {entry.answer}
                    </ReactMarkdown>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : 'Enter a query to get started.'}
        
        {/* Loading indicator */}
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner-container">
              <div className="spinner"></div>
            </div>
            <p>Searching for answers...</p>
          </div>
        )}
        
        {/* Ref for scrolling */}
        <div ref={conversationEndRef} className="scroll-ref" />
      </div>
      
      {/* Google-style follow-up input - only show after an answer is displayed */}
      {history.length > 0 && !loading && (
        <div className="followup-container">
          <form onSubmit={handleFollowUp} className="form-container">
            <div className="google-search-box">
              <div className="search-icon">
                <svg focusable="false" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
                  <path fill="#9aa0a6" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path>
                </svg>
              </div>
              <input
                type="text"
                name="followUpQuery"
                value={followUpQuery}
                onChange={(e) => setFollowUpQuery(e.target.value)}
                placeholder="Ask a follow-up question..."
                className="google-search-input"
                autoComplete="off"
                autoCorrect="off"
                spellCheck="false"
                autoCapitalize="off"
              />
              <div className="search-actions">
                <button 
                  type="button"
                  onClick={handleNewChat}
                  className="icon-button"
                  title="Clear and start a new chat"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4285f4">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="google-buttons">
              <button 
                type="submit" 
                disabled={loading}
                className="google-button"
              >
                Ask
              </button>
              <button 
                type="button" 
                onClick={handleNewChat}
                className="google-button"
              >
                New
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;