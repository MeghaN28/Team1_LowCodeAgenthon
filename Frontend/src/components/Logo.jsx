import './Logo.css'

function Logo() {
  return (
    <div className="logo-container">
      <svg 
        className="logo-icon" 
        viewBox="0 0 60 60" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Central Octagon */}
        <path
          d="M30 10L40 15L45 25L40 35L30 40L20 35L15 25L20 15L30 10Z"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
        />
        {/* Inner Square */}
        <rect
          x="25"
          y="25"
          width="10"
          height="10"
          stroke="currentColor"
          strokeWidth="1.5"
          fill="none"
        />
        {/* Top connection */}
        <line x1="30" y1="10" x2="30" y2="5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="30" cy="5" r="2" fill="currentColor"/>
        {/* Bottom connection */}
        <line x1="30" y1="40" x2="30" y2="45" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="30" cy="45" r="2" fill="currentColor"/>
        {/* Left connection */}
        <line x1="20" y1="25" x2="15" y2="25" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="15" cy="25" r="2" fill="currentColor"/>
        {/* Right connection */}
        <line x1="40" y1="25" x2="45" y2="25" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="45" cy="25" r="2" fill="currentColor"/>
        {/* Top-left diagonal */}
        <line x1="20" y1="15" x2="12" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="12" cy="8" r="2" fill="currentColor"/>
        {/* Top-right diagonal */}
        <line x1="40" y1="15" x2="48" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="48" cy="8" r="2" fill="currentColor"/>
        {/* Bottom-left diagonal */}
        <line x1="20" y1="35" x2="12" y2="42" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="12" cy="42" r="2" fill="currentColor"/>
        {/* Bottom-right diagonal */}
        <line x1="40" y1="35" x2="48" y2="42" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <circle cx="48" cy="42" r="2" fill="currentColor"/>
      </svg>
      <span className="logo-text">
        <span className="logo-text-accent">SUPPLY</span>
        <span className="logo-text-main">SOUL</span>
      </span>
    </div>
  )
}

export default Logo

