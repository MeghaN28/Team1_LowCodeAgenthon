import { useState, useRef, useEffect } from 'react'
import WelcomeScreen from '../components/WelcomeScreen'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import './Chatbot.css'

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      id: crypto.randomUUID(),
      text: "Hello! I'm your SupplySoul assistant. Ask me about stock levels, item details, or search for specific medications.",
      sender: 'bot',
      timestamp: new Date()
    }
  ])
  const [inputText, setInputText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [agentError, setAgentError] = useState(null)
  const [mode, setMode] = useState('text') // 'text' or 'voice'

  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)
  const audioRef = useRef(null)

  const AGENT_ID = "f800f4c2-eb25-467c-942b-b81de85e2f1c"
  const IGENTIC_ENDPOINT_BASE = "https://container-hackathon-sk.salmonpebble-59bd07ab.eastus.azurecontainerapps.io/api/iGenticAutonomousAgent/Executor"
  const IGENTIC_URL = `${IGENTIC_ENDPOINT_BASE}/${AGENT_ID}`
  const IGENTIC_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_IGENTIC_TOKEN"
  }

  const responseCacheRef = useRef({})

  // -------------------------
  // Auto-scroll
  // -------------------------
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // -------------------------
  // Initialize Speech Recognition
  // -------------------------
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recog = new SpeechRecognition()
    recog.continuous = false
    recog.interimResults = false
    recog.lang = 'en-US'

    recog.onresult = event => {
      const transcript = event.results[0][0].transcript.toLowerCase().trim()
      setInputText(transcript)

      if (transcript.includes("stop") || transcript.includes("pause")) {
        stopAudio()
        sendControlToAgent("stop_audio", localStorage.getItem("last_bot_message") || "")
        return
      }

      if (transcript.includes("continue")) {
        const lastMsg = localStorage.getItem("last_bot_message")
        if (lastMsg) sendToAgent(`Continue: ${lastMsg}`, true)
        return
      }

      if (mode === 'voice') setTimeout(() => handleSendMessage(transcript), 150)
    }

    recog.onerror = () => setIsListening(false)
    recog.onend = () => setIsListening(false)

    recognitionRef.current = recog
  }, [mode])

  // -------------------------
  // Cleanup audio on unmount or navigation
  // -------------------------
  useEffect(() => {
    return () => stopAudio()
  }, [])

  // -------------------------
  // SEND MESSAGE TO AGENT
  // -------------------------
  // -------------------------
// SEND MESSAGE TO AGENT
// -------------------------
const sendToAgent = async (text, isControlCommand = false) => {
  if (!text?.trim()) return
  setIsProcessing(true)
  setAgentError(null)

  // Add user message to chat
  setMessages(prev => [
    ...prev,
    { id: crypto.randomUUID(), text, sender: 'user', timestamp: new Date() }
  ])

  // Always treat as live query: fetch fresh data
  const sessionIdToUse = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString()

  const payload = {
    UserInput: text,
    sessionId: sessionIdToUse,
    executionId: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(),
    connectionID: "react-chatbot",
    isImage: false,
    base64string: "",
    evalId: "",
    userInputType: isControlCommand ? "control" : "text"
  }

  try {
    const res = await fetch(IGENTIC_URL, {
      method: 'POST',
      headers: IGENTIC_HEADERS,
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error(`iGentic error: ${res.status}`)

    const data = await res.json()
    const botMessageText = data.result || "No response from agent."

    // Always add fresh response to chat
    setMessages(prev => [
      ...prev,
      { id: crypto.randomUUID(), text: botMessageText, sender: 'bot', timestamp: new Date() }
    ])

    localStorage.setItem("last_bot_message", botMessageText)
    if (mode === 'voice') await playBotAudio(botMessageText)

  } catch (err) {
    console.error(err)
    setAgentError(err.message)
    setMessages(prev => [
      ...prev,
      { id: crypto.randomUUID(), text: `Error: ${err.message}`, sender: 'bot', timestamp: new Date() }
    ])
  }

  setIsProcessing(false)
}


  const handleSendMessage = (text = inputText) => {
    if (!text.trim() || isProcessing) return
    setInputText('')
    sendToAgent(text)
  }

  // -------------------------
  // MIC BUTTON / VOICE MODE
  // -------------------------
  const toggleVoiceInput = () => {
    if (audioRef.current) stopAudio()
    if (mode !== 'voice') return

    if (!recognitionRef.current) {
      alert("Speech recognition not supported.")
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

  // -------------------------
  // TEXT-TO-SPEECH
  // -------------------------
  const playBotAudio = async (text) => {
    if (mode !== 'voice') return
    try {
      stopAudio()
      const res = await fetch("http://localhost:8080/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      })
      if (!res.ok) return console.error("TTS error")

      const audioBlob = await res.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      audioRef.current = audio
      audio.play().catch(() => console.warn("Autoplay blocked"))
    } catch (err) {
      console.error("TTS failure:", err)
    }
  }

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current = null
    }
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
  }

  const sendControlToAgent = async (command, context) => {
    const payload = {
      UserInput: command,
      sessionId: localStorage.getItem("igentic_chat_session") || "",
      executionId: crypto.randomUUID || Date.now().toString(),
      connectionID: "react-chatbot",
      isControlCommand: true
    }
    try {
      await fetch(IGENTIC_URL, {
        method: 'POST',
        headers: IGENTIC_HEADERS,
        body: JSON.stringify(payload)
      })
    } catch (err) {
      console.error("Control error:", err)
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

  const handleQuickQuestion = q => {
    setInputText(q)
    setTimeout(() => handleSendMessage(q), 100)
  }

  return (
    <div className="chatbot-page-chatgpt">
      <div className="chat-container-chatgpt">

        {/* Mode Selector */}
        <div style={{ marginBottom: '10px' }}>
          <button onClick={() => setMode('text')} disabled={mode === 'text'}>Text Mode</button>
          <button onClick={() => setMode('voice')} disabled={mode === 'voice'}>Voice Mode</button>
        </div>

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

        {mode === 'text' && (
          <ChatInput
            inputText={inputText}
            setInputText={setInputText}
            handleKeyPress={handleKeyPress}
            handleVoiceInput={toggleVoiceInput} // optional
            isListening={isListening}
            handleSendMessage={handleSendMessage}
            isProcessing={isProcessing}
          />
        )}

        {mode === 'voice' && (
          <div style={{ textAlign: 'center', margin: '10px' }}>
            <button onClick={toggleVoiceInput}>
              {isListening ? "Stop Listening" : "Start Listening"}
            </button>
          </div>
        )}

        {agentError && (
          <div className="agent-error">Agent Error: {agentError}</div>
        )}
      </div>
    </div>
  )
}

export default Chatbot
