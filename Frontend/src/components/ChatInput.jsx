function ChatInput({
    inputText,
    setInputText,
    handleKeyPress,
    handleVoiceInput,
    isListening,
    handleSendMessage,
    isProcessing
}) {
    return (
        <div className="input-container-chatgpt">
            <div className="input-wrapper-chatgpt">
                <div className="input-box">
                    <textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Message SupplySoul Assistant..."
                        className="input-textarea"
                        rows="1"
                    />
                    <div className="input-actions-chatgpt">
                        {inputText && (
                            <button
                                onClick={() => setInputText('')}
                                className="clear-btn"
                                title="Clear"
                            >
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                            </button>
                        )}
                        <button
                            onClick={handleVoiceInput}
                            className={`voice-btn ${isListening ? 'listening' : ''}`}
                            title="Voice input"
                        >
                            {isListening ? (
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                    <rect x="6" y="6" width="12" height="12" rx="2" />
                                </svg>
                            ) : (
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                                    <line x1="12" y1="19" x2="12" y2="23" />
                                    <line x1="8" y1="23" x2="16" y2="23" />
                                </svg>
                            )}
                        </button>
                        <button
                            onClick={() => handleSendMessage()}
                            disabled={!inputText.trim() || isProcessing}
                            className="send-btn-chatgpt"
                            title="Send message"
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="22" y1="2" x2="11" y2="13" />
                                <polygon points="22 2 15 22 11 13 2 9 22 2" />
                            </svg>
                        </button>
                    </div>
                </div>
                {isListening && (
                    <div className="listening-indicator-chatgpt">
                        <div className="listening-dot"></div>
                        <span>Listening...</span>
                    </div>
                )}
            </div>
        </div>
    )
}

export default ChatInput
