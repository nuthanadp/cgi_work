import React from 'react';
import { X, Sparkles, ArrowRight, RefreshCw, Lightbulb } from 'lucide-react';

const SuggestionsDrawer = ({ isOpen, onClose, suggestions, isLoading, onSelectSuggestion, onRefresh }) => {
    
    return (
        // REFACTOR: Use 'history-drawer' class to match SmartUpdateDrawer exactly
        <div className={`history-drawer ${isOpen ? 'open' : ''}`} style={{ zIndex: 60 }}>
            
            {/* Header */}
            <div className="history-drawer-header" style={{ backgroundColor: '#fff' }}>
                <h3 style={{ margin: 0, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--button-bg)' }}>
                    <Sparkles size={18} />
                    AI Suggestions
                </h3>
                <button 
                    onClick={onClose} 
                    className="detail-modal-close-btn"
                    style={{ position: 'static' }}
                >
                    <X size={20} />
                </button>
            </div>

            {/* Content Area */}
            <div className="history-list" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
                
                {isLoading ? (
                    <div style={{ textAlign: 'center', marginTop: '60px', color: '#888' }}>
                        <div className="loader" style={{ margin: '0 auto 20px' }}></div>
                        <p style={{ fontSize: '0.9rem' }}>Analyzing document context...</p>
                    </div>
                ) : suggestions.length > 0 ? (
                    suggestions.map((suggestion, index) => (
                        <div
                            key={index}
                            onClick={() => {
                                onSelectSuggestion(suggestion);
                                // Optional: onClose(); 
                            }}
                            className="suggestion-item"
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '12px 14px',
                                backgroundColor: 'var(--bg-color)',
                                border: '1px solid var(--scroll-hover)',
                                borderRadius: '10px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease'
                            }}
                        >
                            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                <Lightbulb size={18} color="var(--button-bg)" style={{ marginTop: '2px', flexShrink: 0 }} />
                                <span style={{ fontSize: '0.9rem', color: 'var(--text-color)', lineHeight: '1.4' }}>{suggestion}</span>
                            </div>
                            <ArrowRight size={16} className="arrow-icon" style={{ color: '#ccc', flexShrink: 0, opacity: 0, transition: 'opacity 0.2s' }} />
                        </div>
                    ))
                ) : (
                    <div style={{ textAlign: 'center', marginTop: '60px', color: '#aaa' }}>
                        <Sparkles size={40} style={{ marginBottom: '15px', opacity: 0.3 }} />
                        <p style={{ maxWidth: '80%', margin: '0 auto', fontSize: '0.95rem' }}>
                            No suggestions yet. Click regenerate to get ideas for your document.
                        </p>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div style={{ padding: '15px', borderTop: '1px solid var(--scroll-hover)', backgroundColor: '#fff', marginTop: 'auto' }}>
                <button 
                    onClick={onRefresh} 
                    disabled={isLoading}
                    className="btn-secondary" 
                    style={{ 
                        width: '100%', 
                        justifyContent: 'center', 
                        padding: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}
                >
                    <RefreshCw size={16} className={isLoading ? "spin" : ""} />
                    Regenerate Suggestions
                </button>
            </div>

            <style>{`
                .suggestion-item:hover {
                    background-color: #fff !important;
                    border-color: var(--button-bg) !important;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                }
                .suggestion-item:hover .arrow-icon {
                    opacity: 1 !important;
                    color: var(--button-bg) !important;
                }
                .spin {
                    animation: spin 1s linear infinite;
                }
                @keyframes spin { 100% { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};

export default SuggestionsDrawer;