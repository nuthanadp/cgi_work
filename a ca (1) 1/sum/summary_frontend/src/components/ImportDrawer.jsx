import React, { useState, useEffect } from 'react';
import { X, Search, FileJson, Check, DownloadCloud, AlertTriangle } from 'lucide-react';

const ImportDrawer = ({ isOpen, onClose, documents, onImport }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedDoc, setSelectedDoc] = useState(null);

    // 1. Filter: Only show "Raw" files (Skip Analysis files)
    const rawFiles = documents.filter(doc => doc.analysis?.is_raw);
    
    // 2. Filter: Apply Search
    const filteredFiles = rawFiles.filter(doc => 
        doc.fileName.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Reset state when opened
    useEffect(() => {
        if (isOpen) {
            setSearchQuery('');
            setSelectedDoc(null);
        }
    }, [isOpen]);

    return (
        // Reuse 'history-drawer' class for the exact same slide-in animation and style
        <div className={`history-drawer ${isOpen ? 'open' : ''}`} style={{ zIndex: 60 }}>
            
            {/* Header */}
            <div className="history-drawer-header">
                <h3>
                    <DownloadCloud size={18} style={{marginRight: '8px'}}/> 
                    Import Document
                </h3>
                <button onClick={onClose} className="detail-modal-close-btn" style={{position: 'static'}}>
                    <X size={20} />
                </button>
            </div>

            {/* Warning Alert (Compact) */}
            <div style={{ padding: '12px 15px', borderBottom: '1px solid var(--scroll-hover)', backgroundColor: '#fff3cd', color: '#856404', fontSize: '0.8rem', lineHeight: '1.4' }}>
                <div style={{display: 'flex', gap: '8px', alignItems: 'start'}}>
                    <AlertTriangle size={14} style={{flexShrink: 0, marginTop: '2px'}}/>
                    <span><strong>Warning:</strong> Importing will overwrite the current live document content.</span>
                </div>
            </div>

            {/* Search Bar */}
            <div style={{ padding: '15px', borderBottom: '1px solid var(--scroll-hover)' }}>
                <div className="search-input-container" style={{marginBottom: 0, width: '100%'}}>
                    <Search className="search-input-icon" size={14} style={{top: '50%', transform: 'translateY(-50%)'}} />
                    <input 
                        type="text" 
                        placeholder="Search raw files..." 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="text-input"
                        style={{ 
                            width: '100%', 
                            fontSize: '0.9rem', 
                            padding: '8px 12px 8px 32px',
                            boxSizing: 'border-box' 
                        }}
                    />
                </div>
            </div>

            {/* File List */}
            <div className="history-list" style={{ padding: '10px' }}>
                {filteredFiles.length > 0 ? (
                    filteredFiles.map(doc => (
                        <div 
                            key={doc.id}
                            onClick={() => setSelectedDoc(doc)}
                            className={`history-item ${selectedDoc?.id === doc.id ? 'history-item-active' : ''}`}
                            style={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '10px', 
                                padding: '10px',
                                cursor: 'pointer',
                                border: selectedDoc?.id === doc.id ? '1px solid var(--button-bg)' : '1px solid transparent',
                                marginBottom: '8px'
                            }}
                        >
                            <div style={{
                                width: '32px', height: '32px', borderRadius: '6px', 
                                background: 'var(--scroll-bg)', display: 'flex', 
                                alignItems: 'center', justifyContent: 'center', flexShrink: 0
                            }}>
                                <FileJson size={16} color="#666" />
                            </div>
                            
                            <div style={{ flexGrow: 1, minWidth: 0 }}>
                                <div style={{ 
                                    fontWeight: 600, 
                                    fontSize: '0.85rem', 
                                    whiteSpace: 'nowrap', 
                                    overflow: 'hidden', 
                                    textOverflow: 'ellipsis',
                                    marginBottom: '2px'
                                }}>
                                    {doc.fileName}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: '#888' }}>
                                    {new Date(doc.created_at).toLocaleDateString()}
                                </div>
                            </div>
                            
                            {selectedDoc?.id === doc.id && (
                                <Check size={16} color="var(--button-bg)" />
                            )}
                        </div>
                    ))
                ) : (
                    <div style={{ padding: '30px 10px', textAlign: 'center', color: '#888', fontSize: '0.9rem' }}>
                        {rawFiles.length === 0 ? "No raw documents available." : "No matches found."}
                    </div>
                )}
            </div>

            {/* Footer Action Button */}
            <div style={{ padding: '15px', borderTop: '1px solid var(--scroll-hover)', backgroundColor: 'var(--bg-color)', marginTop: 'auto' }}>
                <button 
                    onClick={() => {
                        if(selectedDoc) {
                            onImport(selectedDoc);
                            // Do not close immediately if you want to show success, but usually better UX to close
                            // onClose(); is handled by parent if needed, usually we close on success.
                        }
                    }}
                    className="btn-primary" 
                    disabled={!selectedDoc}
                    style={{ width: '100%', justifyContent: 'center', padding: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                    <DownloadCloud size={16} />
                    Import Selected File
                </button>
            </div>
        </div>
    );
};

export default ImportDrawer;