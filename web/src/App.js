import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

// Utility function to decode URLs within content
const decodeUrlsInContent = (content) => {
  if (!content) return content;
  
  // This regex looks for URLs or URL-encoded patterns
  return content.replace(/(https?:\/\/[^\s]+)|(www\.[^\s]+)|(%[0-9A-Fa-f]{2})/g, (match) => {
    try {
      // Check if it's a URL-encoded character
      if (match.startsWith('%')) {
        return decodeURIComponent(match);
      }
      // For full URLs, try to decode them while preserving the URL structure
      if (match.startsWith('http') || match.startsWith('www')) {
        // Decode the URL but preserve essential encoded characters
        // This prevents breaking valid URLs
        return decodeURIComponent(match.replace(/\%([0-9A-F]{2})/g, (_, hex) => {
          const code = parseInt(hex, 16);
          // Don't decode essential URL characters
          if ([33, 35, 36, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 58, 59, 61, 63, 64, 91, 93, 95].includes(code)) {
            return '%' + hex;
          }
          return String.fromCharCode(code);
        }));
      }
      return match;
    } catch (e) {
      console.warn('Failed to decode URL:', match, e);
      return match;
    }
  });
};

function App() {
  const [inputQuery, setInputQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [assistantName, setAssistantName] = useState('AI Local Knowledge Search');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const query = formData.get('query');
    
    if (query) {
      setInputQuery(query);
      setLoading(true);
      
      try {
        const res = await fetch(`/api/answer?query=${encodeURIComponent(query)}`);
        const data = await res.json();
        
        if (res.ok) {
          // Process response to decode URLs while preserving markdown
          const processedOutput = decodeUrlsInContent(data.response.output);
          setResponse(processedOutput);
          
          // Set the assistant name if available
          if (data.ai_assistant_name) {
            setAssistantName(data.ai_assistant_name);
          }
        } else {
          setResponse(`Error: ${data.error || 'Failed to get response'}`);
        }
      } catch (error) {
        setResponse(`Error: ${error.message}`);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="App" style={{
      fontFamily: "'Roboto', 'Arial', sans-serif",
      maxWidth: '800px',
      margin: '0 auto',
      padding: '40px 20px',
      color: '#202124'
    }}>
      <h1 style={{
        fontSize: '28px',
        fontWeight: '400',
        marginBottom: '30px',
        color: '#5f6368',
        textAlign: 'center'
      }}>{assistantName}</h1>
      
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '40px'
      }}>
        <form onSubmit={handleSubmit} style={{
          width: '100%',
          maxWidth: '600px',
          position: 'relative'
        }}>
          <div style={{
            display: 'flex',
            boxShadow: '0 1px 6px rgba(32,33,36,.28)',
            borderRadius: '24px',
            padding: '8px 16px',
            alignItems: 'center'
          }}>
            <input
              type="text"
              name="query"
              placeholder="Ask a question about local knowledge..."
              style={{
                width: '100%',
                padding: '12px 0',
                fontSize: '16px',
                border: 'none',
                outline: 'none'
              }}
            />
            <button 
              type="submit" 
              disabled={loading}
              style={{
                background: loading ? '#f1f3f4' : '#4285f4',
                color: loading ? '#80868b' : 'white',
                border: 'none',
                borderRadius: '24px',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: loading ? 'default' : 'pointer',
                marginLeft: '10px',
                transition: 'background-color 0.2s'
              }}
            >
              {loading ? 'Loading...' : 'Search'}
            </button>
          </div>
        </form>
      </div>
      
      <div style={{
        backgroundColor: loading ? '#f8f9fa' : 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
        minHeight: '200px',
        textAlign: 'left',
        fontSize: '15px',
        lineHeight: '1.6',
        color: '#202124'
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: '#5f6368' }}>
            <div style={{ marginBottom: '15px' }}>
              <div className="spinner"></div>
            </div>
            <p>Searching for answers...</p>
          </div>
        ) : (
          response ? (
            <ReactMarkdown>
              {response}
            </ReactMarkdown>
          ) : 'Enter a query to get started.'
        )}
      </div>
    </div>
  );
}

export default App;