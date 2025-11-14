function MessageList({ messages, isProcessing, messagesEndRef }) {
    return (
        <div className="messages-container">
            {messages.map((message) => (
                <div
                    key={message.id}
                    className={`message-row ${message.sender === 'user' ? 'user-row' : 'bot-row'}`}
                >
                    <div className="message-group">
                        {message.sender === 'bot' && (
                            <div className="avatar-bot">🤖</div>
                        )}
                        {message.sender === 'user' && (
                            <div className="avatar-user">👤</div>
                        )}
                        <div className="message-content-chatgpt">
                            <div className="message-text">
                                {message.text.split('\n').map((line, idx) => (
                                    <p key={idx}>{line}</p>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            ))}
            {isProcessing && (
                <div className="message-row bot-row">
                    <div className="message-group">
                        <div className="avatar-bot">🤖</div>
                        <div className="message-content-chatgpt">
                            <div className="typing-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>
    )
}

export default MessageList
