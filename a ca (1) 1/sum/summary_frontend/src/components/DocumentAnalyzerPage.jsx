import React, { useState, useContext, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { ProjectContext } from '../context/ProjectContext';
import AnalysisTabs from '../components/AnalysisTabs';
import FileUploader from '../components/FileUploader';
import ConfirmationModal from '../components/ConfirmationModal'; 
import { Trash2, Download, FileText, UploadCloud, Inbox, Search, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, X, ToggleLeft, ToggleRight, File, LayoutList, FileJson } from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs';

// ---- CONFIG (backend base needed for PDF absolute URLs) ----
const BACKEND_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

// --- LIGHTWEIGHT TEXT CLEANER ---
const cleanText = (text) => {
    if (!text) return "";
    let formatted = text;
    formatted = formatted.replace(/\r\n/g, '\n');
    formatted = formatted.replace(/Page \d+ of \d+/gi, '');
    formatted = formatted.replace(/--- PAGE \d+ ---/gi, '');
    formatted = formatted.replace(/\]\[/g, '] [');
    return formatted.trim();
};

const DocumentDetailModal = ({ isOpen, onClose, document, onDownload }) => {
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

    const isRaw = document?.analysis?.is_raw === true;

    // Build absolute PDF url if exists
    const pdfUrl = document?.pdf_preview_url 
        ? `${BACKEND_BASE}${document.pdf_preview_url}`
        : null;

    const rawText = isRaw ? cleanText(document?.analysis?.extracted_content) : "";

    // Header icon
    let HeaderIcon = pdfUrl ? FileText : File;

    // MAIN PRIORITY RENDER
    let modalContent;
    if (pdfUrl) {
        // PRIORITY 1 → PDF
        modalContent = (
            <iframe
                src={pdfUrl}
                title="PDF Preview"
                width="100%"
                height="100%"
                style={{ border: 'none' }}
            />
        );
    } else if (isRaw) {
        // PRIORITY 2 → Raw (txt/docx)
        modalContent = (
            <div style={{ padding: '2rem 3rem', height: '100%', overflowY: 'auto' }}>
                <p style={{ color: '#666', fontStyle: 'italic', margin: 0, borderBottom: '1px solid #eee', marginBottom: '1rem', paddingBottom: '10px' }}>
                    Raw Extracted Text
                </p>
                <div style={{
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.55',
                    fontSize: '1rem'
                }}>
                    {rawText || "No text content found."}
                </div>
            </div>
        );
    } else {
        // PRIORITY 3 → Analysis
        modalContent = (
            <div style={{ height: '100%', overflowY: 'auto', padding: '1rem' }}>
                <AnalysisTabs analysisResult={document.analysis} />
            </div>
        );
    }

    return (
        <div className={`modal-overlay ${modalClass}`} onClick={handleClose}>
            <div
                className={`modal-content detail-modal-content ${modalClass}`}
                style={{ maxWidth: '900px', width: '90vw' }}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="detail-modal-header">
                    <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <HeaderIcon size={28} color="var(--button-bg)" />
                        {document?.fileName}
                    </h2>
                    <button onClick={handleClose} className="detail-modal-close-btn">
                        <X size={24} />
                    </button>
                </div>

                <div className="detail-modal-body" style={{ height: 'calc(85vh - 120px)', overflow: 'hidden' }}>
                    {modalContent}
                </div>

                <div style={{ padding: '1rem', borderTop: '1px solid var(--scroll-hover)', display: 'flex', justifyContent: 'flex-end' }}>
                    {pdfUrl && (
                        <button
                            onClick={() => window.open(pdfUrl, "_blank")}
                            className="btn-primary"
                            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                        >
                            <Download size={18} /> Download Original PDF
                        </button>
                    )}
                    {!pdfUrl && !isRaw && (
                        <button
                            onClick={() => onDownload(document)}
                            className="btn-primary"
                            style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '10px' }}
                        >
                            <Download size={18} /> Download Analysis
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

const DocumentAnalyzerPage = () => {
    const { projectId } = useParams();
    const { projects, analyzeAndAddFiles, removeFileFromProject, downloadAnalysis } = useContext(ProjectContext);
    const project = projects[projectId];

    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('analyzed');
    const [skipAnalysis, setSkipAnalysis] = useState(false);
    const [selectedDoc, setSelectedDoc] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
    const [fileToDelete, setFileToDelete] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const ITEMS_PER_PAGE = 5;

    if (!project) return <p>Loading project...</p>;

    const filteredDocuments = useMemo(() => {
        return project.documents.filter(doc => {
            const matchesSearch = doc.fileName.toLowerCase().includes(searchQuery.toLowerCase());
            const isRaw = doc.analysis?.is_raw === true;
            const matchesTab = activeTab === 'raw' ? isRaw : !isRaw;
            return matchesSearch && matchesTab;
        });
    }, [project.documents, searchQuery, activeTab]);

    const totalPages = Math.ceil(filteredDocuments.length / ITEMS_PER_PAGE);
    const currentDocuments = filteredDocuments.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    useEffect(() => { setCurrentPage(1); }, [searchQuery, activeTab]);

    const openModal = (doc) => {
        const normalized = {
            ...doc,
            pdf_preview_url:
                doc.pdf_preview_url ||
                doc.analysis?.pdf_preview_url ||
                null,
        };
        setSelectedDoc(normalized);
        setIsModalOpen(true);
    };

    const handleDeleteClick = (e, doc) => {
        e.stopPropagation();
        setFileToDelete(doc);
        setIsConfirmModalOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (fileToDelete) {
            await removeFileFromProject(projectId, 'documents', fileToDelete.id);
        }
        setIsConfirmModalOpen(false);
        setFileToDelete(null);
    };

    const handleUpload = (files) => {
        analyzeAndAddFiles(projectId, files, 'documents', skipAnalysis);
    };

    return (
        <div className="page-wrapper">
            <ConfirmationModal
                isOpen={isConfirmModalOpen}
                onClose={() => setIsConfirmModalOpen(false)}
                onConfirm={handleConfirmDelete}
                title={`Delete "${fileToDelete?.fileName}"?`}
                message="This document will be permanently removed from the project."
            />

            <div style={{ marginBottom: '0rem' }}>
                <Breadcrumbs />
                <h1 style={{ marginTop: '0rem', fontSize: '2.5rem' }}>Documents for: {project.name}</h1>
            </div>

            <div className="page-grid-layout">
                <div className="grid-col-uploader">
                    <div className="section-content">
                        <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <UploadCloud size={24} /> Upload Documents
                        </h2>

                        <FileUploader
                            onUpload={handleUpload}
                            acceptedFileTypes=".pdf,.docx,.txt"
                            title="Drag & drop documents"
                            supportedText="Supported: PDF, DOCX, TXT"
                        />

                        <div style={{
                            marginTop: '1.5rem',
                            padding: '10px',
                            backgroundColor: 'var(--scroll-bg)',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px'
                        }}>
                            <div onClick={() => setSkipAnalysis(!skipAnalysis)} style={{
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center'
                            }}>
                                {skipAnalysis ? <ToggleRight size={32} color="var(--button-bg)" /> : <ToggleLeft size={32} color="#888" />}
                            </div>
                            <div>
                                <label style={{ fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' }} onClick={() => setSkipAnalysis(!skipAnalysis)}>
                                    Skip AI Analysis & Enhancement
                                </label>
                                <p style={{ margin: 0, fontSize: '0.8rem', color: '#666' }}>
                                    Just extract text (Faster)
                                </p>
                            </div>
                        </div>
                        
                        {/* JIRA Enhancement Info */}
                        <div style={{
                            marginTop: '1rem',
                            padding: '12px',
                            backgroundColor: '#e8f4fd',
                            borderLeft: '4px solid #17a2b8',
                            borderRadius: '6px',
                            fontSize: '0.85rem',
                            lineHeight: '1.5'
                        }}>
                            <strong style={{ display: 'block', marginBottom: '5px', color: '#0c5460' }}>
                                🎫 JIRA Ticket Enhancement
                            </strong>
                            <span style={{ color: '#0c5460' }}>
                                JIRA tickets are automatically enhanced during upload to remove metadata and noise, 
                                keeping only relevant requirements for better BSOL document analysis.
                            </span>
                        </div>
                    </div>
                </div>

                <div className="grid-col-results">
                    <div className="section-content">
                        <div className="results-header" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <FileText size={24} /> Documents
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

                        <div className="pill-nav-container" style={{ margin: '1rem 0 1.5rem 0' }}>
                            <div className="pill-nav" style={{ display: 'inline-flex' }}>
                                <button className={`pill-tab-btn ${activeTab === 'analyzed' ? 'active' : ''}`} onClick={() => setActiveTab('analyzed')}>
                                    <LayoutList size={16} /> Analyzed Reports
                                </button>
                                <button className={`pill-tab-btn ${activeTab === 'raw' ? 'active' : ''}`} onClick={() => setActiveTab('raw')}>
                                    <FileJson size={16} /> Extracted Text (Preview)
                                </button>
                            </div>
                        </div>

                        {currentDocuments.length > 0 ? (
                            <>
                                <div className="analyzed-item-list animate-list-items">
                                    {currentDocuments.map((doc) => {
                                        const isRaw = doc.analysis?.is_raw === true;
                                        const isPdf =
                                            doc.pdf_preview_url ||
                                            doc.analysis?.pdf_preview_url ||
                                            false;

                                        const cats = doc.analysis?.categorized_json || {};
                                        const stats = {
                                            func: cats.Functional?.length || 0,
                                            nonFunc: cats.NonFunctional?.length || 0,
                                            const: cats.Constraints?.length || 0,
                                        };

                                        let ListIcon = isPdf ? FileText : File;

                                        const borderLeftColor = isPdf ? 'var(--button-bg)' : isRaw ? '#888' : 'var(--button-bg)';
                                        const iconBg = isPdf ? 'rgba(255, 59, 59, 0.1)' : '#f0f0f0';
                                        const iconColor = isPdf ? 'var(--button-bg)' : '#666';

                                        return (
                                            <div
                                                key={doc.id}
                                                className="analyzed-item"
                                                onClick={() => openModal(doc)}
                                                style={{ cursor: 'pointer', borderLeft: `4px solid ${borderLeftColor}` }}
                                            >
                                                <div className="analyzed-item-header">
                                                    <div className="item-icon-wrapper" style={{ backgroundColor: iconBg }}>
                                                        <ListIcon size={20} color={iconColor} />
                                                    </div>

                                                    <div className="analyzed-item-info">
                                                        <h4>{doc.fileName}</h4>
                                                        <p style={{ fontSize: '0.8rem', color: '#aaa', marginBottom: '6px' }}>
                                                            Uploaded: {doc.created_at ? new Date(doc.created_at).toLocaleString() : 'Just now'}
                                                        </p>

                                                        {isRaw ? (
                                                            <div className="item-preview-stats">
                                                                <span style={{ backgroundColor: '#e0e0e0', color: '#555' }}>
                                                                    {isPdf ? "PDF View Available" : "Raw Text Only"}
                                                                </span>
                                                                <span style={{ backgroundColor: '#e0f7fa', color: '#006064' }}>Ready for Import</span>
                                                            </div>
                                                        ) : (
                                                            <div className="item-preview-stats">
                                                                {isPdf && (
                                                                    <span style={{ backgroundColor: '#e0e0e0', color: '#555' }}>PDF View</span>
                                                                )}
                                                                <span>{stats.func} Functional</span>
                                                                <span>{stats.nonFunc} Non-Functional</span>
                                                                <span>{stats.const} Constraints</span>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <div className="analyzed-item-actions">
                                                        <button onClick={(e) => handleDeleteClick(e, doc)} className="action-btn">
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
                                        <button className="pagination-btn" disabled={currentPage === 1} onClick={() => setCurrentPage(1)}>
                                            <ChevronsLeft size={20} />
                                        </button>
                                        <button className="pagination-btn" disabled={currentPage === 1} onClick={() => setCurrentPage((prev) => prev - 1)}>
                                            <ChevronLeft size={20} />
                                        </button>
                                        <span className="pagination-info">Page {currentPage} of {totalPages}</span>
                                        <button className="pagination-btn" disabled={currentPage === totalPages} onClick={() => setCurrentPage((prev) => prev + 1)}>
                                            <ChevronRight size={20} />
                                        </button>
                                        <button className="pagination-btn" disabled={currentPage === totalPages} onClick={() => setCurrentPage(totalPages)}>
                                            <ChevronsRight size={20} />
                                        </button>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="empty-state animate-list-items">
                                <Inbox size={48} opacity={0.5} />
                                <h3>No Documents Found</h3>
                                <p>
                                    {searchQuery
                                        ? "No results match your search."
                                        : activeTab === 'raw'
                                        ? "No extracted documents. Toggle 'Skip AI Analysis' when uploading."
                                        : "No analyzed reports yet."}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {selectedDoc && (
                <DocumentDetailModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    document={selectedDoc}
                    onDownload={(doc) => downloadAnalysis(doc.analysis?.categorized_json, doc.fileName, 'documents')}
                />
            )}
        </div>
    );
};

export default DocumentAnalyzerPage;
