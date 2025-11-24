import { useState, useRef, useEffect } from 'react'
import WelcomeScreen from '../components/WelcomeScreen'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import './Chatbot.css'

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
  const [agentError, setAgentError] = useState(null)
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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // -------------------------
  // Send message to main agent
  // -------------------------
  const sendToAgent = async (text) => {
    setIsProcessing(true)
    setAgentError(null)

    const userMessage = { id: messages.length + 1, text, sender: 'user', timestamp: new Date() }
    setMessages(prev => [...prev, userMessage])

    let sessionIdToUse = ""
    if (!text.toLowerCase().includes("stock") && localStorage.getItem("igentic_chat_session")) {
      sessionIdToUse = localStorage.getItem("igentic_chat_session")
    }

    const payload = {
      UserInput: JSON.stringify({ prompt: text }),
      sessionId: sessionIdToUse,
      executionId: crypto.randomUUID ? crypto.randomUUID() : (Date.now().toString() + Math.random().toString()),
      connectionID: "react-chatbot",
      isImage: false,
      base64string: "",
      evalId: "",
      userInputType: "text"
    }

    try {
      const res = await fetch(IGENTIC_URL, { method: 'POST', headers: IGENTIC_HEADERS, body: JSON.stringify(payload) })
      if (!res.ok) throw new Error(`iGentic API error: ${res.status} ${await res.text()}`)
      const data = await res.json()
      if (data.session_id) localStorage.setItem("igentic_chat_session", data.session_id)

      const botMessageText = data.result || JSON.stringify(data, null, 2)
      setMessages(prev => [...prev, { id: prev.length + 1, text: botMessageText, sender: 'bot', timestamp: new Date() }])

      // Play TTS
      playBotAudio(botMessageText)

    } catch (err) {
      console.error(err)
      setAgentError(err.message || String(err))
      setMessages(prev => [...prev, { id: prev.length + 1, text: `Error: ${err.message || "Agent error"}`, sender: 'bot', timestamp: new Date() }])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSendMessage = (text = inputText) => {
    if (!text.trim() || isProcessing) return
    setInputText('')
    sendToAgent(text)
  }

  // -------------------------
  // STT + control commands
  // -------------------------
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recog = new SpeechRecognition()
    recog.continuous = false
    recog.interimResults = false
    recog.lang = 'en-US'

    recog.onresult = (event) => {
      const transcript = event.results[0][0].transcript.toLowerCase().trim()
      setInputText(transcript)

      // Check for TTS control commands first
      if (transcript.includes("stop") || transcript.includes("hold on") || transcript.includes("pause")) {
        stopAudio()
        setMessages(prev => [...prev, { id: prev.length + 1, text: "Audio stopped by user", sender: 'bot', timestamp: new Date() }])
        sendControlToAgent(transcript, lastBotMessage())
        return
      }

      setTimeout(() => handleSendMessage(transcript), 150)
    }

    recog.onerror = (e) => { console.error("SpeechRecognition error", e); setIsListening(false) }
    recog.onend = () => { setIsListening(false) }
    recognitionRef.current = recog
  }, [])

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) return alert("Speech recognition not available.")
    if (isListening) { recognitionRef.current.stop(); setIsListening(false) }
    else { recognitionRef.current.start(); setIsListening(true) }
  }

  // -------------------------
  // TTS playback
  // -------------------------
  const playBotAudio = async (text) => {
  try {
    stopAudio()
    const res = await fetch("http://localhost:8080/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    })

    if (!res.ok) {
      const txt = await res.text()
      console.error("TTS backend error:", txt)
      return
    }

    const audioBlob = await res.blob()
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)
    audioRef.current = audio
    audio.play().catch(err => console.warn("Autoplay blocked", err))

  } catch (err) {
    console.error("TTS error:", err)
  }
}


  const stopAudio = () => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0; audioRef.current = null }
  }

  const sendControlToAgent = async (command, contextText) => {
    const payload = {
      UserInput: JSON.stringify({ command, context: contextText }),
      sessionId: localStorage.getItem("igentic_chat_session") || "",
      executionId: crypto.randomUUID ? crypto.randomUUID() : (Date.now().toString() + Math.random().toString()),
      connectionID: "react-chatbot",
      isControlCommand: true
    }
    try {
      const res = await fetch(IGENTIC_URL, { method: 'POST', headers: IGENTIC_HEADERS, body: JSON.stringify(payload) })
      if (!res.ok) throw new Error(`Control agent error: ${res.status}`)
      const data = await res.json()
      console.log("Control agent response:", data)
    } catch (err) { console.error("Control command error:", err) }
  }

  const lastBotMessage = () => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].sender === 'bot') return messages[i].text
    }
    return ""
  }

  const handleKeyPress = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage() } }

  const quickQuestions = [
    "What items are low in stock?",
    "Show me all pain relief items",
    "How many items are out of stock?",
    "What's the total inventory count?"
  ]

  const handleQuickQuestion = (question) => { setInputText(question); setTimeout(() => handleSendMessage(question), 100) }

  return (
    <div className="chatbot-page-chatgpt">
      <div className="chat-container-chatgpt">
        {messages.length === 1 && <WelcomeScreen quickQuestions={quickQuestions} handleQuickQuestion={handleQuickQuestion} />}
        <MessageList messages={messages} isProcessing={isProcessing} messagesEndRef={messagesEndRef} />
        <ChatInput
          inputText={inputText}
          setInputText={setInputText}
          handleKeyPress={handleKeyPress}
          handleVoiceInput={toggleVoiceInput}
          isListening={isListening}
          handleSendMessage={handleSendMessage}
          isProcessing={isProcessing}
        />
        {agentError && <div className="agent-error">Agent Error: {agentError}</div>}
      </div>
    </div>
  )
}

export default Chatbot
