import React, { useState, useContext, useMemo, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ProjectContext } from '../context/ProjectContext';
import Preview from '../components/Preview';
import FileUploader from '../components/FileUploader';
import ConfirmationModal from '../components/ConfirmationModal'; 
import { Trash2, Download, Mic, UploadCloud, Inbox, Search, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, X } from 'lucide-react';
import CategorizedDisplay from '../components/CategorizedDisplay';
import Breadcrumbs from '../components/Breadcrumbs'; 

const TranscriptDetailModal = ({ isOpen, onClose, transcript, onDownload }) => {
    const [isAnimatingOut, setIsAnimatingOut] = useState(false);

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

    if (!isOpen && !isAnimatingOut) return null;
    const modalClass = isAnimatingOut ? 'animating-out' : '';

    return (
         <div className={`modal-overlay ${modalClass}`} onClick={handleClose}>
            <div className={`modal-content detail-modal-content ${modalClass}`} onClick={e => e.stopPropagation()}>
                <div className="detail-modal-header">
                    <h2><Mic size={28} color="var(--button-bg)" /> {transcript?.fileName}</h2>
                    <button onClick={handleClose} className="detail-modal-close-btn" title="Close">
                        <X size={24} />
                    </button>
                </div>
                <div className="detail-modal-body">
                     {transcript && (
                        <>
                            <h3>Summary</h3>
                            <div style={{ marginBottom: '2rem', lineHeight: '1.6' }}>
                                <Preview text={transcript.analysis.summary} />
                            </div>
                            
                            <h3>Extracted Requirements</h3>
                            <div className="scroll-box">
                                <CategorizedDisplay data={transcript.analysis.requirements} />
                            </div>
                        </>
                     )}
                </div>
                 <div style={{ padding: '1rem', borderTop: '1px solid var(--scroll-hover)', display: 'flex', justifyContent: 'flex-end' }}>
                     <button 
                        onClick={() => onDownload(transcript)} 
                        className="btn-primary"
                        style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', borderRadius: '6px', background: 'var(--button-bg)', color: 'white', border: 'none', cursor: 'pointer' }}
                    >
                        <Download size={18} /> Download Analysis
                    </button>
                </div>
            </div>
        </div>
    );
}

const TranscriptAnalyzerPage = () => {
    const { projectId } = useParams();
    const { projects, analyzeAndAddFiles, removeFileFromProject, downloadAnalysis } = useContext(ProjectContext);
    const project = projects[projectId];

    const [searchQuery, setSearchQuery] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const ITEMS_PER_PAGE = 5;

    const [selectedTranscript, setSelectedTranscript] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Confirmation Modal State
    const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
    const [fileToDelete, setFileToDelete] = useState(null);

    if (!project) return <p>Loading project...</p>;

    const filteredTranscripts = useMemo(() => {
        return project.transcripts.filter(t => 
            t.fileName.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [project.transcripts, searchQuery]);

    const totalPages = Math.ceil(filteredTranscripts.length / ITEMS_PER_PAGE);
    const currentTranscripts = filteredTranscripts.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery]);

    const openModal = (transcript) => {
        setSelectedTranscript(transcript);
        setIsModalOpen(true);
    };

    const handleDeleteClick = (e, transcript) => {
        e.stopPropagation();
        setFileToDelete(transcript);
        setIsConfirmModalOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (fileToDelete) {
            await removeFileFromProject(projectId, 'transcripts', fileToDelete.id);
        }
        setIsConfirmModalOpen(false);
        setFileToDelete(null);
    };

    return (
        <div className="page-wrapper">
             <ConfirmationModal
                isOpen={isConfirmModalOpen}
                onClose={() => setIsConfirmModalOpen(false)}
                onConfirm={handleConfirmDelete}
                title={`Delete "${fileToDelete?.fileName}"?`}
                message="This transcript and its analysis will be permanently removed from the project."
            />

            <div style={{ marginBottom: '0rem' }}>
                <Breadcrumbs />
                <h1 style={{ marginTop: '0rem', fontSize: '2.5rem' }}>Transcripts for: {project.name}</h1>
            </div>
            
            <div className="page-grid-layout">
                <div className="grid-col-uploader">
                    <div className="section-content">
                        <h2 style={{marginTop: 0, display: 'flex', alignItems: 'center', gap: '10px'}}><UploadCloud size={24} /> Upload Transcripts</h2>
                        <FileUploader 
                            onUpload={(files) => analyzeAndAddFiles(projectId, files, 'transcripts')} 
                            acceptedFileTypes=".txt,.json"
                            title="Drag & drop transcripts"
                            supportedText="Supported: TXT, JSON"
                        />
                    </div>
                </div>

                <div className="grid-col-results">
                    <div className="section-content">
                        <div className="results-header">
                            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <Mic size={24} /> Analyzed Transcripts ({filteredTranscripts.length})
                            </h2>
                             <div className="search-input-container">
                                <Search className="search-input-icon" size={16} />
                                <input 
                                    type="text" 
                                    placeholder="Search..." 
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="text-input"
                                    style={{ paddingLeft: '35px', fontSize: '0.9rem' }}
                                />
                            </div>
                        </div>

                        {currentTranscripts.length > 0 ? (
                            <>
                                <div className="analyzed-item-list animate-list-items" key={currentPage + searchQuery}>
                                    {currentTranscripts.map((transcript) => {
                                        const summary = transcript.analysis?.summary || "No summary available.";
                                        const summarySnippet = summary.length > 120 ? summary.substring(0, 120) + '...' : summary;

                                        return (
                                            <div 
                                                key={transcript.id} 
                                                className="analyzed-item"
                                                onClick={() => openModal(transcript)}
                                                style={{ cursor: 'pointer' }}
                                            >
                                                <div className="analyzed-item-header">
                                                    <div className="item-icon-wrapper">
                                                        <Mic size={20} />
                                                    </div>
                                                    <div className="analyzed-item-info">
                                                        <h4>{transcript.fileName}</h4>
                                                        {/* --- NEW: Date Display --- */}
                                                        <p style={{ fontSize: '0.8rem', color: '#aaa', marginBottom: '4px' }}>
                                                            Uploaded: {transcript.created_at ? new Date(transcript.created_at).toLocaleString() : 'Just now'}
                                                        </p>
                                                        <p className="item-summary-snippet">
                                                            {summarySnippet}
                                                        </p>
                                                    </div>
                                                    <div className="analyzed-item-actions">
                                                        <button 
                                                            onClick={(e) => handleDeleteClick(e, transcript)} 
                                                            title="Remove File" 
                                                            className="action-btn"
                                                        >
                                                            <Trash2 color="#ff3b3b" size={18} />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                                
                                {totalPages > 1 && (
                                    <div className="pagination-container">
                                        <button className="pagination-btn" disabled={currentPage === 1} onClick={() => setCurrentPage(1)}><ChevronsLeft size={20} /></button>
                                        <button className="pagination-btn" disabled={currentPage === 1} onClick={() => setCurrentPage(prev => prev - 1)}><ChevronLeft size={20} /></button>
                                        
                                        <span className="pagination-info">Page {currentPage} of {totalPages}</span>
                                        
                                        <button className="pagination-btn" disabled={currentPage === totalPages} onClick={() => setCurrentPage(prev => prev + 1)}><ChevronRight size={20} /></button>
                                        <button className="pagination-btn" disabled={currentPage === totalPages} onClick={() => setCurrentPage(totalPages)}><ChevronsRight size={20} /></button>
                                    </div>
                                )}
                            </>
                        ) : (
                             <div className="empty-state animate-list-items">
                                <Inbox size={48} opacity={0.5} />
                                <h3>{searchQuery ? "No Matches Found" : "No Transcripts Analyzed"}</h3>
                                <p>{searchQuery ? "Try adjusting your search term." : "Upload a transcript file to begin the analysis process."}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <TranscriptDetailModal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                transcript={selectedTranscript}
                onDownload={(t) => downloadAnalysis(t.analysis, t.fileName, 'transcripts')}
            />
        </div>
    );
};

export default TranscriptAnalyzerPage;