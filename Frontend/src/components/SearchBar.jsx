function SearchBar({ searchTerm, setSearchTerm }) {
    return (
        <div className="search-wrapper">
            <div className="search-box-modern">
                <span className="search-icon-modern">🔍</span>
                <input
                    type="text"
                    placeholder="Search by name, category, or status..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input-modern"
                />
                {searchTerm && (
                    <button
                        className="clear-search"
                        onClick={() => setSearchTerm('')}
                        aria-label="Clear search"
                    >
                        ✕
                    </button>
                )}
            </div>
        </div>
    )
}

export default SearchBar
