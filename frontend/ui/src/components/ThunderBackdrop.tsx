export function ThunderBackdrop() {
  return <div className="thunder-backdrop" aria-hidden="true">
    <div className="thunder-aurora thunder-aurora-one" />
    <div className="thunder-aurora thunder-aurora-two" />
    <div className="thunder-stars" />
    <svg className="lightning-bolt lightning-bolt-one" viewBox="0 0 360 620" fill="none" preserveAspectRatio="none">
      <path d="M284 0L238 84L274 80L186 194L228 188L116 342L157 336L45 610" stroke="url(#boltOne)" strokeWidth="3.5" strokeLinejoin="round" strokeLinecap="round" />
            <path d="M284 0L238 84L274 80L186 194L228 188L116 342L157 336L45 610" stroke="#9b7cff" strokeWidth="22" strokeLinejoin="round" strokeLinecap="round" opacity=".17" filter="url(#glowOne)" />
      <defs><linearGradient id="boltOne" x1="240" y1="0" x2="150" y2="620" gradientUnits="userSpaceOnUse"><stop stopColor="#68d9ff" stopOpacity="0" /><stop offset=".28" stopColor="#b69aff" /><stop offset=".72" stopColor="#6ea1ff" /><stop offset="1" stopColor="#68d9ff" stopOpacity="0" /></linearGradient><filter id="glowOne"><feGaussianBlur stdDeviation="10" /></filter></defs>
    </svg>
    <svg className="lightning-bolt lightning-bolt-two" viewBox="0 0 420 620" fill="none" preserveAspectRatio="none">
      <path d="M62 22L142 105L113 111L205 207L173 215L283 337L247 345L369 486" stroke="url(#boltTwo)" strokeWidth="2.4" strokeLinejoin="round" strokeLinecap="round" />
      <defs><linearGradient id="boltTwo" x1="60" y1="30" x2="334" y2="504" gradientUnits="userSpaceOnUse"><stop stopColor="#7f96ff" stopOpacity="0" /><stop offset=".45" stopColor="#7f96ff" /><stop offset="1" stopColor="#d6a5ff" stopOpacity="0" /></linearGradient></defs>
    </svg>
    <div className="thunder-flash thunder-flash-one" />
    <div className="thunder-flash thunder-flash-two" />
  </div>;
}
