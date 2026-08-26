import React, { useState, useEffect } from 'react';
import { Check, X, Sparkles, Edit3, FileText } from 'lucide-react';

const UpdateProposalModal = ({ isOpen, onClose, onConfirm, suggestion, isAnalyzing, newFiles = [] }) => {
    const [editedPrompt, setEditedPrompt] = useState('');
    const [isAnimatingOut, setIsAnimatingOut] = useState(false);

    useEffect(() => {
        if (suggestion) {
            setEditedPrompt(suggestion);
        }
    }, [suggestion]);

    useEffect(() => {
        if (isOpen) setIsAnimatingOut(false);
    }, [isOpen]);

    const handleClose = () => {
        setIsAnimatingOut(true);
        setTimeout(() => {
            onClose();
            setIsAnimatingOut(false);
        }, 300);
    };

    const handleConfirm = () => {
        setIsAnimatingOut(true);
        setTimeout(() => {
            onConfirm(editedPrompt);
            setIsAnimatingOut(false);
        }, 300);
    };

    if (!isOpen && !isAnimatingOut) return null;

    const modalClass = isAnimatingOut ? 'animating-out' : '';
    
    // Check if the suggestion indicates no updates are needed
    const isUpToDate = editedPrompt.toLowerCase().includes("up to date");

    return (
        <div className={`modal-overlay ${modalClass}`} onClick={handleClose} style={{zIndex: 1100}}>
            <div 
                className={`modal-content ${modalClass}`} 
                style={{ 
                    maxWidth: '650px',
                    width: '90%', 
                    padding: '0', 
                    overflow: 'hidden',
                    borderRadius: '12px',
                    boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--scroll-hover)', backgroundColor: 'var(--section-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-color)' }}>
                        <Sparkles size={20} color="var(--button-bg)" />
                        Smart Update Proposal
                    </h2>
                    <button onClick={handleClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#888', display: 'flex' }}>
                        <X size={24} />
                    </button>
                </div>

                {/* Body */}
                <div style={{ padding: '24px', backgroundColor: 'var(--bg-color)' }}>
                    {isAnalyzing ? (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <div className="loader" style={{ margin: '0 auto 1rem auto' }}></div>
                            <p style={{ color: 'var(--text-color)', fontWeight: 600 }}>Analyzing new files...</p>
                            <p style={{ color: '#888', fontSize: '0.9rem', marginTop: '5px' }}>Comparing latest uploads against your document version.</p>
                        </div>
                    ) : (
                        <>  
                            {/* --- NEW: File List Section --- */}
                            {newFiles.length > 0 && (
                                <div style={{ marginBottom: '1.5rem', padding: '12px 16px', backgroundColor: 'rgba(23, 162, 184, 0.08)', borderRadius: '8px', border: '1px solid rgba(23, 162, 184, 0.2)' }}>
                                    <p style={{ margin: '0 0 8px 0', fontSize: '0.85rem', fontWeight: 600, color: '#0c5460' }}>
                                        Updates found in {newFiles.length} new file{newFiles.length > 1 ? 's' : ''}:
                                    </p>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                        {newFiles.map((fileName, idx) => (
                                            <div key={idx} style={{ 
                                                display: 'flex', alignItems: 'center', gap: '6px',
                                                backgroundColor: '#fff', padding: '4px 10px', borderRadius: '20px',
                                                border: '1px solid rgba(23, 162, 184, 0.3)', fontSize: '0.8rem', color: '#0c5460', fontWeight: 500
                                            }}>
                                                <FileText size={12} />
                                                {fileName}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <label style={{ fontWeight: 600, color: 'var(--text-color)', fontSize: '0.95rem' }}>
                                    {isUpToDate ? "Status:" : "Suggested Actions:"}
                                </label>
                                {!isUpToDate && (
                                    <span style={{ fontSize: '0.8rem', color: '#888', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                        <Edit3 size={12} /> Editable
                                    </span>
                                )}
                            </div>
                            
                            <textarea
                                value={editedPrompt}
                                onChange={(e) => setEditedPrompt(e.target.value)}
                                className="text-input"
                                rows={8}
                                style={{ 
                                    width: '100%', 
                                    resize: 'vertical', 
                                    lineHeight: '1.6',
                                    padding: '16px',
                                    fontSize: '0.95rem',
                                    fontFamily: 'inherit',
                                    backgroundColor: 'var(--section-bg)',
                                    borderRadius: '8px',
                                    border: '1px solid var(--scroll-hover)',
                                    boxSizing: 'border-box'
                                }}
                                spellCheck={false}
                                readOnly={isUpToDate}
                            />
                        </>
                    )}
                </div>

                {/* Footer */}
                {!isAnalyzing && (
                    <div style={{ padding: '20px 24px', borderTop: '1px solid var(--scroll-hover)', backgroundColor: 'var(--section-bg)', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                        {!isUpToDate && (
                            <button onClick={handleClose} className="btn-secondary" style={{padding: '10px 20px'}}>
                                Cancel
                            </button>
                        )}
                        
                        <button 
                            onClick={isUpToDate ? handleClose : handleConfirm} 
                            className="btn-primary"
                            disabled={!editedPrompt.trim()} 
                            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px' }}
                        >
                            {isUpToDate ? <X size={18} /> : <Check size={18} />}
                            {isUpToDate ? "Close" : "Apply Updates"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default UpdateProposalModal;