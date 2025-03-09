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

  return (
    <div className="App">
      <h1 className="app-title">{assistantName}</h1>
      
      {/* Initial query input */}
      <div className="centered-container">
        <form onSubmit={handleAnswer} className="form-container">
          <div className="search-box">
            <input
              type="text"
              name="query"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask a question about local knowledge..."
              className="search-input"
            />
            <button 
              type="submit" 
              disabled={loading}
              className={`search-button ${loading ? 'disabled' : ''}`}
            >
              {loading ? 'Loading...' : 'Search'}
            </button>
          </div>
        </form>
      </div>
      
      {/* Conversation history */}
      <div className="conversation-container">
        {history.length > 0 ? (
          <div className="conversation-history">
            {history.map((entry, index) => (
              <div key={index} className={index === history.length - 1 && isNewAnswer ? 'fade-in' : ''}>
                <div className="question-box">
                  <p className="question-label">
                    <span role="img" aria-label="question">❓</span> You asked:
                  </p>
                  <p className="question-text">{entry.question}</p>
                </div>
                <div className="answer-box">
                  <p className="answer-label">
                    <span role="img" aria-label="answer">💡</span> Answer:
                  </p>
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
      
      {/* Follow-up question input - only show after an answer is displayed */}
      {history.length > 0 && !loading && (
        <div className="followup-container">
          <form onSubmit={handleFollowUp} className="form-container">
            <div className="search-box">
              <input
                type="text"
                name="followUpQuery"
                value={followUpQuery}
                onChange={(e) => setFollowUpQuery(e.target.value)}
                placeholder="Ask a follow-up question..."
                className="search-input"
              />
              <button 
                type="submit" 
                disabled={loading}
                className="search-button"
              >
                Follow-up Search
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;