import React, { useState, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';

const ConfirmationModal = ({ isOpen, onClose, onConfirm, title, message }) => {
    const [isAnimatingOut, setIsAnimatingOut] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setIsAnimatingOut(false);
        }
    }, [isOpen]);

    const handleClose = () => {
        setIsAnimatingOut(true); 
        setTimeout(() => {
            onClose(); 
        }, 300); 
    };

    const handleConfirm = () => {
        setIsAnimatingOut(true); 
        setTimeout(() => {
            onConfirm(); 
        }, 300); 
    };

    if (!isOpen) {
        return null;
    }

    return (
        <div 
            className={`modal-overlay ${isAnimatingOut ? 'animating-out' : ''}`} 
            onClick={handleClose}
        >
            <div 
                className={`modal-content ${isAnimatingOut ? 'animating-out' : ''}`} 
                style={{ maxWidth: '500px', width: '90%' }} 
                onClick={(e) => e.stopPropagation()}
            >
                {/* Updated Layout for Long Titles */}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1.25rem' }}>
                    <div className="confirm-icon-wrapper" style={{ flexShrink: 0, marginTop: '4px' }}>
                        <AlertTriangle size={24} color="var(--button-bg)" />
                    </div>
                    
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <h2 style={{ 
                            marginTop: 0, 
                            marginBottom: '0.5rem', 
                            fontSize: '1.25rem',
                            lineHeight: '1.4',
                            wordBreak: 'break-word', // Forces long filenames to wrap
                            hyphens: 'auto'
                        }}>
                            {title}
                        </h2>
                        <p style={{ margin: 0, color: '#888', lineHeight: '1.5', fontSize: '0.95rem' }}>
                            {message}
                        </p>
                    </div>
                </div>

                <div className="confirm-actions">
                    <button onClick={handleClose} className="btn-secondary">
                        Cancel
                    </button>
                    <button onClick={handleConfirm} className="btn-danger">
                        Confirm
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationModal;