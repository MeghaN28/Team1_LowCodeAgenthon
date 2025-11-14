function WelcomeScreen({ quickQuestions, handleQuickQuestion }) {
    return (
        <div className="welcome-screen">
            <div className="welcome-content">
                <div className="welcome-icon">💬</div>
                <h1 className="welcome-title">SupplySoul Assistant</h1>
                <p className="welcome-subtitle">How can I help you with your inventory today?</p>
                <div className="suggestions-grid">
                    {quickQuestions.map((question, index) => (
                        <button
                            key={index}
                            onClick={() => handleQuickQuestion(question)}
                            className="suggestion-button"
                        >
                            {question}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default WelcomeScreen
