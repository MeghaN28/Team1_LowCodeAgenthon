import { useState, useRef, useEffect } from 'react'
import WelcomeScreen from '../components/WelcomeScreen'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import './Chatbot.css'

const inventoryData = [
  { id: 1, name: 'Paracetamol 500mg', category: 'Pain Relief', quantity: 150, threshold: 50 },
  { id: 2, name: 'Ibuprofen 400mg', category: 'Pain Relief', quantity: 25, threshold: 50 },
  { id: 3, name: 'Amoxicillin 250mg', category: 'Antibiotics', quantity: 0, threshold: 30 },
  { id: 4, name: 'Aspirin 100mg', category: 'Pain Relief', quantity: 200, threshold: 50 },
  { id: 5, name: 'Insulin Vial', category: 'Diabetes', quantity: 45, threshold: 40 },
  { id: 6, name: 'Bandages', category: 'First Aid', quantity: 300, threshold: 100 },
  { id: 7, name: 'Gauze Pads', category: 'First Aid', quantity: 15, threshold: 50 },
  { id: 8, name: 'Antiseptic Solution', category: 'First Aid', quantity: 80, threshold: 50 },
  { id: 9, name: 'Metformin 500mg', category: 'Diabetes', quantity: 120, threshold: 50 },
  { id: 10, name: 'Ciprofloxacin 500mg', category: 'Antibiotics', quantity: 60, threshold: 50 },
]

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your SupplySoul assistant. Ask me about stock levels, item details, or search for specific medications.",
      sender: 'bot',
      timestamp: new Date()
    }
  ])
  const [inputText, setInputText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const getStockStatus = (item) => {
    if (item.quantity === 0) return 'out of stock'
    if (item.quantity <= item.threshold) return 'low stock'
    return 'in stock'
  }

  const processQuery = (query) => {
    const lowerQuery = query.toLowerCase()

    // Search for specific item
    const itemMatch = inventoryData.find(item =>
      item.name.toLowerCase().includes(lowerQuery)
    )

    if (itemMatch) {
      const status = getStockStatus(itemMatch)
      return `${itemMatch.name} is currently ${status}. Quantity: ${itemMatch.quantity} units. Category: ${itemMatch.category}. Threshold: ${itemMatch.threshold} units.`
    }

    // Check for category queries
    const categories = ['pain relief', 'antibiotics', 'diabetes', 'first aid', 'medical supplies', 'medical equipment']
    const categoryMatch = categories.find(cat => lowerQuery.includes(cat))

    if (categoryMatch) {
      const categoryItems = inventoryData.filter(item =>
        item.category.toLowerCase().includes(categoryMatch)
      )
      if (categoryItems.length > 0) {
        const itemsList = categoryItems.map(item =>
          `${item.name} (${item.quantity} units, ${getStockStatus(item)})`
        ).join(', ')
        return `Items in ${categoryMatch}: ${itemsList}`
      }
    }

    // Check for stock status queries
    if (lowerQuery.includes('out of stock') || lowerQuery.includes('out-of-stock')) {
      const outOfStock = inventoryData.filter(item => item.quantity === 0)
      if (outOfStock.length > 0) {
        return `Out of stock items: ${outOfStock.map(item => item.name).join(', ')}`
      }
      return 'All items are currently in stock!'
    }

    if (lowerQuery.includes('low stock') || lowerQuery.includes('low-stock')) {
      const lowStock = inventoryData.filter(item => item.quantity > 0 && item.quantity <= item.threshold)
      if (lowStock.length > 0) {
        return `Low stock items: ${lowStock.map(item => `${item.name} (${item.quantity} units)`).join(', ')}`
      }
      return 'No items are currently low in stock.'
    }

    // General inventory query
    if (lowerQuery.includes('total') || lowerQuery.includes('how many') || lowerQuery.includes('count')) {
      const totalItems = inventoryData.length
      const inStock = inventoryData.filter(item => item.quantity > item.threshold).length
      const lowStock = inventoryData.filter(item => item.quantity > 0 && item.quantity <= item.threshold).length
      const outOfStock = inventoryData.filter(item => item.quantity === 0).length
      return `Total items: ${totalItems}. In stock: ${inStock}, Low stock: ${lowStock}, Out of stock: ${outOfStock}`
    }

    // Default response
    return "I can help you with:\n- Searching for specific items (e.g., 'Paracetamol')\n- Checking stock status (e.g., 'low stock items')\n- Category information (e.g., 'pain relief items')\n- General inventory statistics\n\nTry asking me something specific!"
  }

  const handleSendMessage = async (text = inputText) => {
    if (!text.trim() || isProcessing) return

    const userMessage = {
      id: messages.length + 1,
      text: text,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsProcessing(true)

    // Simulate processing delay
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        text: processQuery(text),
        sender: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botResponse])
      setIsProcessing(false)
    }, 500)
  }

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = false
      recognitionRef.current.lang = 'en-US'

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setInputText(transcript)
        setIsListening(false)
        setTimeout(() => {
          handleSendMessage(transcript)
        }, 100)
      }

      recognitionRef.current.onerror = () => {
        setIsListening(false)
      }

      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }
  }, [])

  const handleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser.')
      return
    }

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      recognitionRef.current.start()
      setIsListening(true)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const quickQuestions = [
    "What items are low in stock?",
    "Show me all pain relief items",
    "How many items are out of stock?",
    "What's the total inventory count?"
  ]

  const handleQuickQuestion = (question) => {
    setInputText(question)
    setTimeout(() => {
      handleSendMessage(question)
    }, 100)
  }

  return (
    <div className="chatbot-page-chatgpt">
      <div className="chat-container-chatgpt">
        {messages.length === 1 && (
          <WelcomeScreen
            quickQuestions={quickQuestions}
            handleQuickQuestion={handleQuickQuestion}
          />
        )}

        <MessageList
          messages={messages}
          isProcessing={isProcessing}
          messagesEndRef={messagesEndRef}
        />

        <ChatInput
          inputText={inputText}
          setInputText={setInputText}
          handleKeyPress={handleKeyPress}
          handleVoiceInput={handleVoiceInput}
          isListening={isListening}
          handleSendMessage={handleSendMessage}
          isProcessing={isProcessing}
        />
      </div>
    </div>
  )
}

export default Chatbot

