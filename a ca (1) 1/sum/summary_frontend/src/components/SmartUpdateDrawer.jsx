import React from 'react';
import { X, Bot, FileText, Check, ArrowRight, AlertCircle, Sparkles } from 'lucide-react';

const SmartUpdateDrawer = ({ isOpen, onClose, isAnalyzing, suggestion, newFiles, onConfirm }) => {
    
    // Auto-close handler
    const handleApply = () => {
        onConfirm(suggestion);
        onClose();
    };

    return (
        <div className={`history-drawer ${isOpen ? 'open' : ''}`} style={{ zIndex: 60 }}>
            {/* Header */}
            <div className="history-drawer-header" style={{backgroundColor: '#fff'}}>
                <h3>
                    <Bot size={18} style={{ marginRight: '8px', color: 'var(--button-bg)' }} />
                    Smart Project Update
                </h3>
                <button onClick={onClose} className="detail-modal-close-btn" style={{ position: 'static' }}>
                    <X size={20} />
                </button>
            </div>

            {/* Content Area */}
            <div className="history-list" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                
                {/* 1. Analyzing State */}
                {isAnalyzing && (
                    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                        <div className="loader" style={{ margin: '0 auto 20px' }}></div>
                        <h4 style={{ margin: '0 0 8px 0' }}>Analyzing Project Files...</h4>
                        <p style={{ color: '#888', fontSize: '0.9rem', margin: 0 }}>
                            Checking for new transcripts or documents uploaded since the last version.
                        </p>
                    </div>
                )}

                {/* 2. Result State (Not Analyzing) */}
                {!isAnalyzing && (
                    <>
                        {/* Section A: New Files Found */}
                        <div style={{ backgroundColor: 'var(--bg-color)', borderRadius: '12px', padding: '15px', border: '1px solid var(--scroll-hover)' }}>
                            <h5 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <FileText size={16} color="#888"/> 
                                New Files Detected
                            </h5>
                            
                            {newFiles && newFiles.length > 0 ? (
                                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem', color: 'var(--text-color)' }}>
                                    {newFiles.map((file, i) => (
                                        <li key={i} style={{marginBottom: '4px'}}>{file}</li>
                                    ))}
                                </ul>
                            ) : (
                                <div style={{ fontSize: '0.85rem', color: '#888', fontStyle: 'italic' }}>
                                    No new files found since last save.
                                </div>
                            )}
                        </div>

                        {/* Section B: The Proposal */}
                        <div>
                            <h5 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Sparkles size={16} color="var(--button-bg)"/> 
                                AI Recommendation
                            </h5>
                            
                            <div className="scroll-box" style={{ 
                                maxHeight: '300px', 
                                padding: '15px', 
                                border: '1px solid var(--button-bg)', 
                                backgroundColor: 'rgba(var(--button-bg-rgb), 0.02)',
                                fontSize: '0.95rem',
                                lineHeight: '1.6'
                            }}>
                                {suggestion || "Your document is up to date."}
                            </div>
                        </div>

                        {/* Visual Helper */}
                        <div style={{ display: 'flex', gap: '10px', fontSize: '0.8rem', color: '#888', backgroundColor: '#f9f9f9', padding: '10px', borderRadius: '8px' }}>
                            <AlertCircle size={16} style={{ flexShrink: 0 }} />
                            <span>
                                This will generate an edit instruction. You can review the changes in the document history after applying.
                            </span>
                        </div>
                    </>
                )}
            </div>

            {/* Footer Actions */}
            {!isAnalyzing && (
                <div style={{ padding: '15px', borderTop: '1px solid var(--scroll-hover)', backgroundColor: '#fff', marginTop: 'auto' }}>
                    <button 
                        onClick={handleApply}
                        className="btn-primary" 
                        disabled={!suggestion || suggestion.includes("up to date")}
                        style={{ width: '100%', justifyContent: 'center', padding: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                        Apply Update <ArrowRight size={16} />
                    </button>
                </div>
            )}
        </div>
    );
};

export default SmartUpdateDrawer;