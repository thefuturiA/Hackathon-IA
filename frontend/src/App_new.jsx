import { useState, useEffect, useRef } from 'react'
import './App.css'

// Composant principal du chatbot ANDF
function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Bonjour ! Je suis l'assistant intelligent de l'ANDF (Agence Nationale du Domaine et du Foncier) du Bénin. Je peux vous aider avec vos questions sur le foncier, les titres de propriété, les procédures administratives et la réglementation. Comment puis-je vous aider aujourd'hui ?",
      timestamp: new Date()
    }
  ])
  
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [apiStatus, setApiStatus] = useState('disconnected')
  const messagesEndRef = useRef(null)

  // Vérification de l'état de l'API
  useEffect(() => {
    checkApiHealth()
  }, [])

  // Auto-scroll vers le bas des messages
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const checkApiHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health')
      if (response.ok) {
        setApiStatus('connected')
      } else {
        setApiStatus('error')
      }
    } catch (error) {
      setApiStatus('disconnected')
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          max_results: 5
        })
      })

      if (!response.ok) {
        throw new Error('Erreur de connexion avec le serveur')
      }

      const data = await response.json()
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer,
        confidence: data.confidence,
        sources: data.sources || [],
        timestamp: new Date()
      }

      setMessages(prev => [...prev, botMessage])
      
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: `Désolé, une erreur s'est produite : ${error.message}. Veuillez vérifier que le serveur backend est démarré (http://localhost:8000).`,
        isError: true,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  // Suggestions de questions prédéfinies
  const suggestionQuestions = [
    "Comment obtenir un titre foncier au Bénin ?",
    "Quels sont les documents nécessaires pour acheter un terrain ?",
    "Quelle est la procédure d'immatriculation ?",
    "Comment vérifier la régularité d'un terrain ?",
    "Quels sont les services de l'ANDF ?"
  ]

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Assistant ANDF</h1>
                <p className="text-sm text-gray-600">Agence Nationale du Domaine et du Foncier - Bénin</p>
              </div>
            </div>
            
            {/* Indicateur de statut API */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                apiStatus === 'connected' ? 'bg-green-500' : 
                apiStatus === 'error' ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-gray-600">
                {apiStatus === 'connected' ? 'En ligne' : 
                 apiStatus === 'error' ? 'Erreur' : 'Hors ligne'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Zone des messages */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow-lg h-[600px] flex flex-col">
          
          {/* Messages container */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-lg p-3 ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : message.isError 
                      ? 'bg-red-100 text-red-800 border border-red-200'
                      : 'bg-gray-100 text-gray-800'
                }`}>
                  <div className="whitespace-pre-wrap break-words">
                    {message.content}
                  </div>
                  
                  {/* Afficher la confidence et les sources pour les réponses du bot */}
                  {message.type === 'bot' && message.confidence && (
                    <div className="mt-2 text-xs opacity-70">
                      <div>Confiance: {Math.round(message.confidence * 100)}%</div>
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-1">
                          Sources: {message.sources.length} document(s) ANDF
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="text-xs opacity-70 mt-2">
                    {formatTimestamp(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Indicateur de frappe */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Assistant en train d'analyser...</div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Suggestions de questions (affichées seulement au début) */}
          {messages.length === 1 && (
            <div className="px-4 pb-2">
              <div className="text-sm text-gray-600 mb-2">Suggestions de questions :</div>
              <div className="flex flex-wrap gap-2">
                {suggestionQuestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="text-xs bg-blue-50 text-blue-700 px-3 py-2 rounded-full hover:bg-blue-100 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Zone de saisie */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Posez votre question sur le foncier béninois..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="2"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  'Envoyer'
                )}
              </button>
            </div>
            
            {/* Informations sur l'état de la connexion */}
            {apiStatus === 'disconnected' && (
              <div className="mt-2 text-sm text-red-600 flex items-center space-x-1">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span>Serveur hors ligne. Démarrez le backend avec: cd backend && ./start.sh</span>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer avec informations */}
      <footer className="max-w-4xl mx-auto px-4 py-4">
        <div className="text-center text-sm text-gray-600">
          <p>Assistant intelligent basé sur les informations officielles de l'ANDF</p>
          <p className="mt-1">
            Pour les démarches officielles, veuillez consulter directement{' '}
            <a href="https://www.andf.bj" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
              le site de l'ANDF
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
