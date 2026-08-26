import React, { useState, useContext, useEffect, useRef, useCallback, useMemo, memo } from 'react';
import { useParams } from 'react-router-dom';
import { ProjectContext } from '../context/ProjectContext';
import ConfirmationModal from './ConfirmationModal';
import ImportDrawer from './ImportDrawer';
import SuggestionsDrawer from './SuggestionsDrawer';
import SmartUpdateDrawer from './SmartUpdateDrawer';
import RichTextEditor from './RichTextEditor'; 
import {
    Send, Bot, RefreshCcw, Wand2, History, X, Edit3, Edit2, 
    Maximize, Minimize, LocateFixed, MoreVertical, FileDown, 
    List, Sparkles, HelpCircle, FileClock, FileText, DownloadCloud, Save, Pencil, Eye
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { fetchWithToken } from '../api';
import toast from 'react-hot-toast';
import pdfMake from 'pdfmake/build/pdfmake';
import 'pdfmake/build/vfs_fonts.js';
import Breadcrumbs from './Breadcrumbs';

// --- CONFIGURATION ---
const BACKEND_URL = "http://127.0.0.1:5000"; 

// --- Helper Functions ---
const formatImportedText = (text) => {
    if (!text) return "";
    let formatted = text;
    formatted = formatted.replace(/\r\n/g, '\n');
    formatted = formatted.replace(/Page \d+ of \d+/gi, '');
    formatted = formatted.replace(/\]\[/g, '] [');
    return formatted.trim();
};

const preprocessContentForEditor = (content) => {
    if (!content) return "";
    // Keep string replacement for the Editor mode, as it needs raw text
    let processed = content.replace(/!\[([^\]]*)\]\((\/static\/[^)]+)\)/g, (match, alt, path) => {
        return `![${alt}](${BACKEND_URL}${path})`;
    });
    processed = processed.replace(/src="(\/static\/[^"]+)"/g, (match, path) => {
        return `src="${BACKEND_URL}${path}"`;
    });
    return processed;
};

// --- VIEW PROCESSOR: Creates <citation> tags ---
const preprocessContentForView = (content) => {
    if (!content) return "";
    let processed = content;

    // Convert [Source: filename] -> <citation data-filename="filename"></citation>
    const citationRegex = /\[(Source|Edit):\s*([^\]]+)\]/g;
    processed = processed.replace(citationRegex, (match, type, label) => {
        // We capture both "Source" and "Edit" types now
        const fullLabel = `${type}: ${label.trim()}`;
        const encodedLabel = encodeURIComponent(fullLabel);
        return `<citation data-filename="${encodedLabel}"></citation>`;
    });

    return processed;
};

const preprocessChatMarkdown = (markdown) => {
    if (!markdown) return '';
    let processed = markdown;
    processed = processed.replace(/<br\s*\/?>/gi, '\n');
    processed = processed.replace(/<p(\s+[^>]*)?>\s*(&nbsp;)*\s*<\/p>/gi, '');
    processed = processed.replace(/(\r?\n){3,}/g, '\n\n');
    return processed;
};

// --- SourceViewerModal ---
const SourceViewerModal = ({ isOpen, onClose, fileName, content }) => {
    const [isAnimatingOut, setIsAnimatingOut] = useState(false);
    useEffect(() => { if (isOpen) setIsAnimatingOut(false); }, [isOpen]);
    const handleClose = () => {
        setIsAnimatingOut(true);
        setTimeout(() => { onClose(); setIsAnimatingOut(false); }, 300);
    };
    if (!isOpen && !isAnimatingOut) return null;
    
    // Try to parse as analysis JSON to show categorized view
    let displayContent = null;
    let isAnalysis = false;
    
    try {
        const parsed = JSON.parse(content);
        if (parsed.summary && parsed.categorized_json) {
            // This is an analyzed document - show categorized view
            isAnalysis = true;
            displayContent = parsed;
        } else {
            // Regular JSON - just format it
            displayContent = JSON.stringify(parsed, null, 2);
        }
    } catch (e) { 
        // Raw text content
        displayContent = content; 
    }
    
    const modalClass = isAnimatingOut ? 'animating-out' : '';
    return (
        <div className={`modal-overlay ${modalClass}`} onClick={handleClose}>
            <div className={`modal-content detail-modal-content ${modalClass}`} onClick={(e) => e.stopPropagation()}>
                <div className="detail-modal-header">
                     <h3 className="source-modal-title" style={{margin: 0, border: 'none'}}>Source: {fileName}</h3>
                     <button onClick={handleClose} className="detail-modal-close-btn" title="Close"><X size={24} /></button>
                </div>
                <div className="detail-modal-body" style={{padding: 0}}>
                    {isAnalysis ? (
                        <div className="scroll-box source-modal-body" style={{border: 'none', borderRadius: 0, padding: '1rem'}}>
                            <div style={{marginBottom: '1.5rem'}}>
                                <h4 style={{color: 'var(--button-bg)', marginBottom: '0.5rem'}}>📋 Summary</h4>
                                <div style={{whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: '1rem', borderRadius: '4px'}}>
                                    {displayContent.summary}
                                </div>
                            </div>
                            {displayContent.categorized_json && (
                                <div>
                                    <h4 style={{color: 'var(--button-bg)', marginBottom: '0.5rem'}}>📊 Categorized Requirements</h4>
                                    {Object.entries(displayContent.categorized_json).map(([category, items]) => (
                                        <div key={category} style={{marginBottom: '1rem'}}>
                                            <h5 style={{color: '#555', marginBottom: '0.5rem'}}>{category}</h5>
                                            {Array.isArray(items) && items.length > 0 ? (
                                                <ul style={{paddingLeft: '1.5rem', margin: 0}}>
                                                    {items.map((item, idx) => (
                                                        <li key={idx} style={{marginBottom: '0.25rem'}}>{item}</li>
                                                    ))}
                                                </ul>
                                            ) : (
                                                <p style={{color: '#999', fontStyle: 'italic', margin: 0}}>No items</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ) : (
                        <pre className="scroll-box source-modal-body" style={{border: 'none', borderRadius: 0}}>
                            {typeof displayContent === 'string' ? displayContent : JSON.stringify(displayContent, null, 2)}
                        </pre>
                    )}
                </div>
            </div>
        </div>
    );
};

// --- Citation Component ---
const Citation = ({ node, onClick, ...props }) => {
    const encodedLabel = node?.properties?.dataFilename || '';
    if (!encodedLabel) return null;
    
    const label = decodeURIComponent(encodedLabel);
    
    // Distinguish between file sources and user edits visually
    const isUserEdit = label.startsWith("Edit:");
    
    // Extract filename from complex citation formats:
    // Format 1: "Source: filename.ext" -> "filename.ext"
    // Format 2: "Edit: description | Source: filename.ext" -> "filename.ext"
    let fileName = null;
    let displayLabel = label;
    
    if (isUserEdit) {
        // Complex format: "Edit: description | Source: filename.ext"
        const sourceMatch = label.match(/\|\s*Source:\s*(.+?)$/i);
        if (sourceMatch) {
            fileName = sourceMatch[1].trim();
            // Display just the edit description
            displayLabel = label.replace(/^Edit:\s*/, '').replace(/\s*\|\s*Source:.*$/, '');
        } else {
            // User edit without source file
            displayLabel = label.replace(/^Edit:\s*/, '');
        }
    } else {
        // Simple format: "Source: filename.ext"
        fileName = label.replace(/^Source:\s*/i, '').trim();
        displayLabel = fileName;
    }
    
    const icon = isUserEdit ? "✍️" : "📄";
    const bg = isUserEdit ? "#fff3e0" : "#e3f2fd";
    const border = isUserEdit ? "#ffe0b2" : "#bbdefb";
    const color = isUserEdit ? "#e65100" : "#1565c0";
    
    const canClick = fileName !== null;
    
    // Build display text: show both description and source filename when available
    let displayText = displayLabel;
    if (isUserEdit && fileName) {
        // For edits with source: "Edit description | filename.ext"
        displayText = `${displayLabel} | ${fileName}`;
    }

    return (
        <button 
            className="citation-link" 
            onClick={(e) => {
                e.stopPropagation(); 
                if (canClick && fileName) onClick(fileName);
            }} 
            title={canClick ? `View source: ${fileName}` : "User-requested change"}
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 8px',
                margin: '0 4px',
                backgroundColor: bg,
                color: color,
                border: `1px solid ${border}`,
                borderRadius: '4px',
                fontSize: '0.85em',
                cursor: canClick ? 'pointer' : 'default',
                fontWeight: 500
            }}
        >
            {icon} {displayText}
        </button>
    );
};

// --- THE RENDERER (Original View Mode) ---
const MemoizedMarkdown = memo(({ content, handleCitationClick }) => {
    return (
        <div className="markdown-content">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]} 
                rehypePlugins={[rehypeRaw]} 
                components={{ 
                    citation: (props) => <Citation {...props} onClick={handleCitationClick} />,
                    // Custom rendering for <em> tags that contain "Last edit:" 
                    // to make them look like metadata instead of emphasized text
                    em: ({node, children, ...props}) => {
                        const text = String(children);
                        if (text.startsWith('Last edit:')) {
                            return (
                                <div style={{
                                    fontSize: '0.85em',
                                    color: '#888',
                                    fontStyle: 'italic',
                                    marginTop: '0.5rem',
                                    marginBottom: '1rem',
                                    paddingLeft: '0.5rem',
                                    borderLeft: '3px solid #e0e0e0'
                                }}>
                                    {children}
                                </div>
                            );
                        }
                        return <em {...props}>{children}</em>;
                    },
                    img: ({node, ...props}) => {
                        let imgUrl = props.src;
                        if (imgUrl) {
                            if (imgUrl.startsWith('/static/')) {
                                imgUrl = `${BACKEND_URL}${imgUrl}`;
                            } 
                            else if (imgUrl.startsWith('static/')) {
                                imgUrl = `${BACKEND_URL}/${imgUrl}`;
                            }
                        }
                        return (
                            <img 
                                {...props} 
                                src={imgUrl}
                                style={{ 
                                    maxWidth: '100%', 
                                    height: 'auto', 
                                    display: 'block', 
                                    margin: '1.5rem auto', 
                                    border: '1px solid #eee', 
                                    borderRadius: '8px',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                                    backgroundColor: '#fff'
                                }} 
                                alt={props.alt || 'Document Image'}
                                onError={(e) => {
                                    e.currentTarget.style.border = '1px dashed #ffcccc';
                                    e.currentTarget.style.padding = '10px';
                                    e.currentTarget.style.backgroundColor = '#fff0f0';
                                }}
                            />
                        );
                    }
                }}
            >
                {content || "*Document loading...*"}
            </ReactMarkdown>
        </div>
    );
});

const AgentWorkspace = () => {
    const { projectId } = useParams();
    const {
        projects, isAgentRunning, refineDocument, executeAgentGoal,
        qaHistory, setQaHistory,
        refineHistory, setRefineHistory,
        documentContent, setDocumentContent,
        resetProjectWorkspace,
        suggestions, fetchSuggestions, suggestionsLoading, setSuggestions,
        askQuestion, updateVersionDescription 
    } = useContext(ProjectContext);

    const project = projects[projectId];
    
    // --- State ---
    const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);
    const [sourceModalFileName, setSourceModalFileName] = useState('');
    const [sourceModalContent, setSourceModalContent] = useState('');
    const [isResetModalOpen, setIsResetModalOpen] = useState(false);
    const [isHistoryLoading, setIsHistoryLoading] = useState(true);
    const [isDownloading, setIsDownloading] = useState(false);
    const [initialGoal, setInitialGoal] = useState("Create a full technical specification document for this project...");
    const [chatInput, setChatInput] = useState("");
    const [versionHistory, setVersionHistory] = useState([]);
    
    const [activeTab, setActiveTab] = useState('toc');
    const [activeVersionInfo, setActiveVersionInfo] = useState(null);
    
    const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
    const [showImportDrawer, setShowImportDrawer] = useState(false);
    const [showSuggestionsDrawer, setShowSuggestionsDrawer] = useState(false); 
    const [showUpdateDrawer, setShowUpdateDrawer] = useState(false); 
    const [showActionsDropdown, setShowActionsDropdown] = useState(false);

    const [isManualEditMode, setIsManualEditMode] = useState(false);

    const qaChatContainerRef = useRef(null);
    const refineChatContainerRef = useRef(null);
    const actionsDropdownRef = useRef(null);
    const documentScrollRef = useRef(null);

    const [editingVersionId, setEditingVersionId] = useState(null);
    const [editingVersionText, setEditingVersionText] = useState("");
    const [isSavingVersion, setIsSavingVersion] = useState(false);
    const [isFocusMode, setIsFocusMode] = useState(false);
    const [toc, setToc] = useState([]);
    const [scrollToTextOnLoad, setScrollToTextOnLoad] = useState(null);

    const [generatedSuggestion, setGeneratedSuggestion] = useState("");
    const [isCheckingForUpdates, setIsCheckingForUpdates] = useState(false);
    const [updatesFromFiles, setUpdatesFromFiles] = useState([]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (actionsDropdownRef.current && !actionsDropdownRef.current.contains(event.target)) {
                setShowActionsDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleHistoryDrawer = () => {
        if (!showHistoryDrawer) setShowImportDrawer(false); 
        setShowHistoryDrawer(!showHistoryDrawer);
    };

    const toggleImportDrawer = () => {
        if (!showImportDrawer) setShowHistoryDrawer(false); 
        setShowImportDrawer(!showImportDrawer);
        setShowActionsDropdown(false); 
    };

    const handleOpenSuggestions = () => {
        setShowUpdateDrawer(false);
        setShowSuggestionsDrawer(true);
        if (documentContent && !suggestionsLoading) {
            fetchSuggestions(projectId, documentContent);
        }
    };

    const fetchHistory = useCallback(async (isInitialLoad = false) => {
        setIsHistoryLoading(true);
        if (setSuggestions) setSuggestions([]); 
        try {
            const response = await fetchWithToken(`/projects/${projectId}/versions`);
            const data = await response.json();
            if (response.ok) {
                setVersionHistory(data);
                const latestContent = data.length > 0 ? data[0].content : "";
                setDocumentContent(latestContent);
                setActiveVersionInfo(null);
                
                if (isInitialLoad) {
                    setQaHistory([]);
                    setRefineHistory([]);
                }
            } else {
                throw new Error(data.error || 'Failed to fetch history');
            }
        } catch (error) {
            toast.error(`Error loading workspace: ${error.message}`);
            setDocumentContent("");
            setVersionHistory([]);
        } finally {
            setIsHistoryLoading(false);
        }
    }, [projectId, setDocumentContent, setSuggestions, setQaHistory, setRefineHistory]);

    useEffect(() => { if (projectId) fetchHistory(true); }, [projectId, fetchHistory]);

    useEffect(() => {
        const scrollToBottom = (ref) => {
            if (ref.current) setTimeout(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, 0);
        };
        if (activeTab === 'qa') scrollToBottom(qaChatContainerRef);
        else if (activeTab === 'refine') scrollToBottom(refineChatContainerRef);
    }, [qaHistory, refineHistory, activeTab, isAgentRunning]);
    
    useEffect(() => {
        if (!documentContent) { setToc([]); return; }
        const newToc = [];
        const headingRegex = /^(#{1,3})\s+(.*)/gm;
        let match;
        while ((match = headingRegex.exec(documentContent)) !== null) {
            newToc.push({ level: match[1].length, text: match[2].trim() });
        }
        setToc(newToc);
    }, [documentContent]);

    // --- ROBUST SCROLL POLLING ---
    // Instead of a single timeout, we poll for the element because 
    // large markdown documents render asynchronously.
    useEffect(() => {
        if (scrollToTextOnLoad && documentScrollRef.current) {
            let attempts = 0;
            const maxAttempts = 20; // Try for 2 seconds (20 * 100ms)
            
            const pollInterval = setInterval(() => {
                attempts++;
                const found = handleScrollToText(scrollToTextOnLoad);
                
                if (found || attempts >= maxAttempts) {
                    clearInterval(pollInterval);
                    setScrollToTextOnLoad(null);
                }
            }, 100);

            return () => clearInterval(pollInterval);
        }
    }, [scrollToTextOnLoad, documentContent]);

    const handleManualContentUpdate = useCallback((newContent) => {
        setDocumentContent(newContent);
    }, [setDocumentContent]);

    const handleSaveManualChanges = async () => {
        const toastId = toast.loading("Saving manual changes...");
        try {
            const response = await fetchWithToken(`/projects/${projectId}/versions`, {
                method: 'POST',
                body: JSON.stringify({ 
                    content: documentContent, 
                    change_description: `Manual edits by user` 
                })
            });
            if (!response.ok) throw new Error("Failed to save version");
            
            await fetchHistory(false);
            toast.success("Changes saved!", { id: toastId });
        } catch (error) {
            toast.error(`Save failed: ${error.message}`, { id: toastId });
        } finally {
            setIsManualEditMode(false); 
            setActiveVersionInfo(null);
        }
    };

    const handleInitialGeneration = async () => {
        await executeAgentGoal(projectId, initialGoal);
        await fetchHistory(true);
        setActiveTab('toc');
    };

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!chatInput.trim() || isAgentRunning) return;
        const instruction = chatInput;
        setChatInput("");
        if (activeTab === 'qa') await handleQASubmit(instruction);
        else if (activeTab === 'refine') {
            await sendRefinementInstruction(instruction);
        }
    };

    const handleQASubmit = async (question) => {
        if (isAgentRunning) return;
        const liveContentBase = (versionHistory.length > 0) ? versionHistory[0].content : documentContent;
        if (activeVersionInfo !== null) {
            setDocumentContent(liveContentBase);
            setActiveVersionInfo(null);
            toast.success("Switched to Live Document for Q&A");
        }
        await askQuestion(projectId, question, liveContentBase);
    };

    const handleQaSuggestionClick = (suggestionPrompt) => {
        setActiveTab('refine');
        setChatInput(suggestionPrompt);
        toast.success("Refine prompt added! Press Send to update the document.");
    };

    const sendRefinementInstruction = async (instruction) => {
        if (isAgentRunning) return;
        setShowSuggestionsDrawer(false); 
        
        const viewingContentSnapshot = documentContent;
        const liveContentBase = documentContent; 
        
        setActiveVersionInfo("UNSAVED");
        const result = await refineDocument(projectId, instruction, liveContentBase);
        if (result === null) {
            setDocumentContent(viewingContentSnapshot);
            setActiveVersionInfo(activeVersionInfo);
            return; 
        }
        
        // Handle response (can be direct content string or object with content + scroll_target)
        let refinedContent = result;
        let scrollTarget = null;
        
        if (typeof result === 'object' && result.content) {
            refinedContent = result.content;
            scrollTarget = result.scroll_target; // Backend provides the scroll target
        }
        
        await fetchHistory(false);
        
        // Use backend-provided scroll target, or extract from instruction as fallback
        if (!scrollTarget) {
            // Fallback: Extract from instruction
            const sectionMatch = instruction.match(/Section\s+([\d.]+)/i);
            if (sectionMatch) {
                scrollTarget = sectionMatch[0];
            } else {
                // Try to extract heading text from instruction
                const afterAction = instruction.match(/(?:UPDATE|ADD|INSERT)\s+([^:]+):/i);
                if (afterAction) {
                    scrollTarget = afterAction[1].trim();
                }
            }
        }
        
        if (scrollTarget) {
            console.log('🎯 Auto-scrolling to:', scrollTarget);
            setScrollToTextOnLoad(scrollTarget); 
        }

        setRefineHistory(prev => [...prev, { role: 'assistant', content: "Done. The document has been updated." }]);
        setActiveVersionInfo(null);
        toast.success("Document updated!");
    };
    
    const handleCheckForUpdates = async () => {
        if (isAgentRunning) return;
        setShowSuggestionsDrawer(false);
        setShowUpdateDrawer(true);
        setIsCheckingForUpdates(true);
        setGeneratedSuggestion(""); 
        setUpdatesFromFiles([]); 
        try {
            const contentToCheck = (versionHistory.length > 0) ? versionHistory[0].content : documentContent;
            const response = await fetchWithToken(`/projects/${projectId}/detect_changes`, {
                method: 'POST',
                body: JSON.stringify({ current_document: contentToCheck }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Failed to analyze changes");
            if (data.new_files && Array.isArray(data.new_files)) setUpdatesFromFiles(data.new_files);
            if (data.suggestion) setGeneratedSuggestion(data.suggestion);
            else setGeneratedSuggestion("The document appears to be up to date with all project files.");
        } catch (error) {
            toast.error(`Analysis failed: ${error.message}`);
            setShowUpdateDrawer(false); 
        } finally {
            setIsCheckingForUpdates(false); 
        }
    };

    const handleApplyUpdate = (finalPrompt) => {
        setShowUpdateDrawer(false);
        
        // Extract first section number from the update instructions for auto-scroll
        const firstSectionMatch = finalPrompt.match(/(?:UPDATE|ADD|INSERT)\s+(?:to\s+)?Section\s+([\d.]+)/i);
        if (firstSectionMatch) {
            const targetSection = `Section ${firstSectionMatch[1]}`;
            console.log('🎯 Will scroll to first updated section:', targetSection);
            // Set scroll target before applying the update
            setTimeout(() => setScrollToTextOnLoad(targetSection), 500);
        }
        
        sendRefinementInstruction(finalPrompt);
    };

    const handleImportDocument = async (doc) => {
        if (!doc) return;
        let rawContent = doc.markdown_content || doc.analysis?.extracted_content || "";
        if (typeof doc.analysis === 'string' && !rawContent) rawContent = doc.analysis;
        if (!rawContent || rawContent.trim().length === 0) {
            toast.error("Import failed: No content found in this file.");
            return;
        }
        const cleanContent = formatImportedText(rawContent);
        const toastId = toast.loading(`Importing "${doc.fileName}"...`);
        setShowImportDrawer(false); 
        try {
            const response = await fetchWithToken(`/projects/${projectId}/versions`, {
                method: 'POST',
                body: JSON.stringify({ 
                    content: cleanContent, 
                    change_description: `Imported from: ${doc.fileName}` 
                })
            });
            if (!response.ok) throw new Error("Failed to save imported document");
            await fetchHistory(false);
            setScrollToTextOnLoad(null);
            toast.success("Document imported & formatted!", { id: toastId });
        } catch (error) {
            console.error(error);
            toast.error("Import failed: " + error.message, { id: toastId });
        }
    };

    const handleRevertVersion = async () => {
        if (!activeVersionInfo || isAgentRunning) return;
        const versionToRestore = versionHistory.find(v => v.timestamp === activeVersionInfo.timestamp);
        if (!versionToRestore) { toast.error("Could not find version to restore."); return; }
        const toastId = toast.loading("Restoring version...");
        try {
            const response = await fetchWithToken(`/projects/${projectId}/versions`, {
                method: 'POST',
                body: JSON.stringify({ 
                    content: versionToRestore.content, 
                    change_description: `Restored version from ${new Date(versionToRestore.timestamp).toLocaleString()}` 
                })
            });
            const newVersion = await response.json();
            if (!response.ok) throw new Error(newVersion.error || 'Failed to save restored version');
            await fetchHistory(false);
            setShowHistoryDrawer(false);
            toast.success("Version restored successfully!", { id: toastId });
        } catch (error) {
            toast.error(`Restore failed: ${error.message}`, { id: toastId });
        }
    };

    const handleDownloadWithPdfmake = async () => {
        if (!documentContent) return toast.error("Document is empty.");
        setIsDownloading(true);
        const toastId = toast.loading("Generating PDF...");
        setShowActionsDropdown(false);
        try {
             const pdfContent = [];
            const lines = documentContent.split('\n');
            let tableMode = false;
            let tableRows = [];
            const allTokensRegex = /(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|\[Source:[^\]]+\]|`[^`]+`)/g;
            const parseLine = (line) => {
                const styledParts = [];
                let lastIndex = 0;
                let match;
                const indentMatch = line.match(/^(\s*)/);
                const indent = indentMatch ? indentMatch[0] : '';
                if (indent) { styledParts.push({ text: indent }); }
                const content = line.slice(indent.length);
                while ((match = allTokensRegex.exec(content)) !== null) {
                    if (match.index > lastIndex) { styledParts.push({ text: content.slice(lastIndex, match.index) }); }
                    const token = match[0];
                    if (token.startsWith('***')) { styledParts.push({ text: token.slice(3, -3), bold: true, italics: true }); }
                    else if (token.startsWith('**')) { styledParts.push({ text: token.slice(2, -2), bold: true }); }
                    else if (token.startsWith('*')) { styledParts.push({ text: token.slice(1, -1), italics: true }); }
                    else if (token.startsWith('[Source:')) { styledParts.push({ text: token, style: 'citation' }); }
                    else if (token.startsWith('`')) { styledParts.push({ text: token.slice(1, -1), style: 'code' }); }
                    lastIndex = match.index + token.length;
                }
                if (lastIndex < content.length) { styledParts.push({ text: content.slice(lastIndex) }); }
                return styledParts.length > 0 ? styledParts : { text: line };
            };
            let listStack = [];
            const flushListStack = () => {
                if (listStack.length > 0) { pdfContent.push(listStack[0]); listStack = []; }
            };
            lines.forEach(line => {
                if (line.startsWith('|') && line.endsWith('|')) {
                    flushListStack();
                    const cells = line.split('|').filter((c, i, arr) => i > 0 && i < arr.length - 1).map(c => ({ text: parseLine(c.trim()), style: 'tableCell' }));
                    if (!/^[-:]+$/.test(line.split('|')[1].trim())) { tableRows.push(cells); tableMode = true; }
                    return; 
                }
                if (tableMode) {
                    if (tableRows.length > 0) {
                        pdfContent.push({
                            table: {
                                headerRows: 1,
                                widths: Array(tableRows[0].length).fill('*'),
                                body: [ tableRows[0].map(h => ({ ...h, style: 'tableHeader' })), ...tableRows.slice(1) ]
                            },
                            layout: { hLineWidth: () => 0.5, vLineWidth: () => 0.5, hLineColor: () => '#bbb', vLineColor: () => '#bbb', },
                            margin: [0, 5, 0, 10]
                        });
                    }
                    tableRows = [];
                    tableMode = false;
                }
                const listMatch = line.match(/^(\s*)[-*•]\s+(.*)/);
                if (listMatch) {
                    const indent = listMatch[1].length;
                    const level = Math.floor(indent / 4);
                    const itemText = listMatch[2];
                    const styledItem = { text: parseLine(itemText) };
                    if (listStack.length === 0) {
                        listStack.push({ ul: [styledItem], margin: [level * 20, 4, 0, 4], level: level });
                    } else {
                        let currentLevel = listStack[listStack.length - 1].level;
                        let currentList = listStack[listStack.length - 1];
                        if (level > currentLevel) {
                            const newList = { ul: [styledItem], margin: [0, 4, 0, 0], level: level };
                            const lastItem = currentList.ul[currentList.ul.length - 1];
                            if (typeof lastItem === 'object' && !Array.isArray(lastItem) && lastItem.ul) { lastItem.ul.push(newList); }
                            else { const prevItem = currentList.ul.pop(); currentList.ul.push({ ...prevItem, ul: [newList] }); }
                            listStack.push(newList);
                        } else if (level < currentLevel) {
                            while (listStack.length > 1 && listStack[listStack.length - 1].level > level) { listStack.pop(); }
                            listStack[listStack.length - 1].ul.push(styledItem);
                        } else { currentList.ul.push(styledItem); }
                    }
                    return; 
                }
                flushListStack();
                if (line.trim() === '') { pdfContent.push({ text: '', margin: [0, 5, 0, 5] }); }
                else if (line.startsWith('>')) { const bqText = line.replace(/^>\s*/, ''); pdfContent.push({ text: parseLine(bqText), style: 'blockquote' }); }
                else if (line.startsWith('### ')) { pdfContent.push({ text: parseLine(line.replace(/^###\s*/, '')), style: 'h3' }); }
                else if (line.startsWith('## ')) { pdfContent.push({ text: parseLine(line.replace(/^##\s*/, '')), style: 'h2' }); }
                else if (line.startsWith('# ')) { pdfContent.push({ text: parseLine(line.replace(/^#\s*/, '')), style: 'h1' }); }
                else { pdfContent.push({ text: parseLine(line), style: 'paragraph' }); }
            });
            flushListStack();
            if (tableRows.length > 0) {
                pdfContent.push({
                    table: {
                        headerRows: 1,
                        widths: Array(tableRows[0].length).fill('*'),
                        body: [ tableRows[0].map(h => ({ ...h, style: 'tableHeader' })), ...tableRows.slice(1) ]
                    },
                    layout: { hLineWidth: () => 0.5, vLineWidth: () => 0.5, hLineColor: () => '#bbb', vLineColor: () => '#bbb', },
                    margin: [0, 5, 0, 10]
                });
            }
            const docDefinition = {
                content: pdfContent,
                styles: {
                    h1: { fontSize: 24, bold: true, margin: [0, 10, 0, 8] },
                    h2: { fontSize: 18, bold: true, margin: [0, 8, 0, 6] },
                    h3: { fontSize: 14, bold: true, margin: [0, 5, 0, 5] },
                    paragraph: { fontSize: 10, lineHeight: 1.4, margin: [0, 2, 0, 2] },
                    blockquote: { italics: true, color: '#444444', margin: [10, 5, 10, 5], fillColor: '#f0f0f0' },
                    citation: { color: '#990000', fontSize: 9, background: '#fde0e0' },
                    code: { background: '#f4f4f4', color: '#333', },
                    tableHeader: { bold: true, fillColor: '#f2f2f2', fontSize: 10, margin: [2, 4, 2, 4] },
                    tableCell: { fontSize: 9, margin: [2, 4, 2, 4] }
                },
                footer: (currentPage, pageCount) => ({ text: `${currentPage} of ${pageCount}`, alignment: 'center', fontSize: 8, margin: [0, 10, 0, 0] }),
                pageMargins: [40, 60, 40, 60]
            };
            const pdfDocGenerator = pdfMake.createPdf(docDefinition);
            const pdfBlob = await new Promise((resolve, reject) => { pdfDocGenerator.getBlob((blob) => { if (blob) { resolve(blob); } else { reject(new Error("Failed to generate PDF blob.")); } }); });
            const url = URL.createObjectURL(pdfBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${project?.name || 'Live Document'}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast.success("PDF downloaded!", { id: toastId });
        } catch (error) {
            console.error("Markdown download error:", error);
            toast.error("Failed to download Markdown file.");
        } finally {
            setIsDownloading(false);
        }
    };
    
    // --- MARKDOWN DOWNLOAD HANDLER ---
    const handleDownloadMarkdown = () => {
        if (!documentContent) return toast.error("Document is empty.");
        setShowActionsDropdown(false);
        try {
            const blob = new Blob([documentContent], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${project?.name || 'document'}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast.success("Markdown file downloaded!");
        } catch (error) {
            console.error("Markdown download error:", error);
            toast.error("Failed to download Markdown file.");
        }
    };

    const handleConfirmReset = async () => {
        if (resetProjectWorkspace) {
            const success = await resetProjectWorkspace(projectId);
            if (success) {
                setVersionHistory([]);
                setDocumentContent("");
                setActiveVersionInfo(null);
                setQaHistory([]);
                setRefineHistory([]);
            }
        }
        setIsResetModalOpen(false);
    };

    // ...existing code...

const handleCitationClick = (fileName) => {
    if (!project) return toast.error("Project data not loaded yet.");
    
    // The fileName parameter is the actual filename extracted by the Citation component
    const cleanedFileName = fileName.trim();
    let foundContent = null;

    console.log('🔍 Searching for citation:', cleanedFileName); // Debug log
    console.log('📁 Available documents:', project.documents.map(d => d.fileName)); // Debug log
    console.log('🎙️ Available transcripts:', project.transcripts.map(t => t.fileName)); // Debug log

    // 1. Search in Documents (using camelCase 'fileName' from to_dict())
    const doc = project.documents.find(d => d.fileName === cleanedFileName);
    
    if (doc) {
        console.log('✅ Found in documents:', doc); // Debug log
        
        try {
            const analysis = typeof doc.analysis === 'string' 
                ? JSON.parse(doc.analysis) 
                : doc.analysis;
            
            // PRIORITY 1: Show full analysis (summary + categorized_json) if available
            if (analysis && (analysis.summary || analysis.categorized_json)) {
                foundContent = JSON.stringify(analysis, null, 2);
            }
            // PRIORITY 2: Show extracted_content if available
            else if (analysis?.extracted_content) {
                foundContent = analysis.extracted_content;
            }
            // PRIORITY 3: Show raw content field
            else if (doc.content) {
                foundContent = doc.content;
            }
            // FALLBACK: Show whole analysis as JSON
            else {
                foundContent = JSON.stringify(analysis || {}, null, 2);
            }
        } catch (e) {
            console.error('Error parsing document analysis:', e);
            // Fallback to raw content if JSON parsing fails
            foundContent = doc.content || "Error: Could not parse document content.";
        }
    } else {
        // 2. Search in Transcripts (using camelCase 'fileName')
        const transcript = project.transcripts.find(t => t.fileName === cleanedFileName);
        if (transcript) {
            console.log('✅ Found in transcripts:', transcript); // Debug log
            try {
                const analysis = typeof transcript.analysis === 'string' 
                    ? JSON.parse(transcript.analysis) 
                    : transcript.analysis;
                
                // For transcripts, show full analysis or summary
                foundContent = JSON.stringify(analysis, null, 2);
            } catch (e) {
                console.error('Error parsing transcript analysis:', e);
                foundContent = "Error: Could not parse transcript content.";
            }
        }
    }

    if (foundContent) {
        setSourceModalFileName(cleanedFileName);
        setSourceModalContent(foundContent);
        setIsSourceModalOpen(true);
    } else {
        console.error('❌ Citation not found:', cleanedFileName); // Debug log
        toast.error(`Source file "${cleanedFileName}" not found in project.`);
    }
};


    const handleScrollToText = (text, event) => {
        if (!documentScrollRef.current) return false;
        const container = documentScrollRef.current;
        
        // PRIORITY 1: Check for LATEST_CHANGE marker (most reliable for finding actual changes)
        if (text === 'LATEST_CHANGE') {
            // Find the marker comment in the markdown content
            const markerRegex = /<!--\s*LATEST_CHANGE\s*-->/;
            if (documentContent && markerRegex.test(documentContent)) {
                // Find element right before where marker was (the changed content)
                const markerIndex = documentContent.indexOf('<!-- LATEST_CHANGE -->');
                const contentBeforeMarker = documentContent.substring(0, markerIndex);
                
                // Find the last meaningful line before the marker (skip "Last edit" lines)
                const lines = contentBeforeMarker.trim().split('\n');
                let searchLine = '';
                for (let i = lines.length - 1; i >= 0; i--) {
                    const line = lines[i].trim();
                    // Skip "Last edit" lines and empty lines
                    if (line && !line.startsWith('_Last edit:') && !line.includes('Last edit:')) {
                        searchLine = line;
                        break;
                    }
                }
                
                if (searchLine) {
                    // Remove markdown syntax and citation tags for better matching
                    const searchText = searchLine
                        .replace(/\*\*\[Edit:[^\]]+\]\*\*/g, '')  // Remove citations
                        .replace(/[*#\[\]_]/g, '')  // Remove markdown syntax
                        .trim();
                    
                    console.log('🔍 Auto-scroll searching for:', searchText.substring(0, 100));
                    
                    const allElements = container.querySelectorAll('h1, h2, h3, h4, h5, h6, p, strong, li, blockquote, div');
                    for (const el of allElements) {
                        const elText = el.textContent.trim();
                        // Match if element contains the search text (partial match for flexibility)
                        if (searchText.length > 10 && elText.includes(searchText.substring(0, 60))) {
                            console.log('✅ Found match, scrolling to:', el.textContent.substring(0, 100));
                            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            el.classList.add('highlight-scroll');
                            setTimeout(() => el.classList.remove('highlight-scroll'), 2000);
                            return true;
                        }
                    }
                    console.log('❌ No matching element found for auto-scroll');
                }
            }
        }
        
        // PRIORITY 2: Try to extract section number from text (e.g., "2.4.1" from "Section 2.4.1" or just "2.4.1")
        const sectionNumMatch = text.match(/([\d.]+(?:\.[\d]+)*)/);
        
        // Query all potential target elements
        const elements = container.querySelectorAll('h1, h2, h3, h4, h5, h6, strong, p, blockquote, .citation-link');
        
        let targetElement = null;
        for (const el of elements) {
            const elText = el.textContent;
            
            // First: Try exact section number match (e.g., "2.4.1" matches "## 2.4.1 Title")
            if (sectionNumMatch) {
                const sectionNum = sectionNumMatch[1];
                // Match headings that START with the section number
                if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(el.tagName)) {
                    // Match "2.4.1" in "2.4.1 Other Scenarios" or "## 2.4.1 Title"
                    const headingNumMatch = elText.match(/^[#\s]*(\d+(?:\.\d+)*)/);
                    if (headingNumMatch && headingNumMatch[1] === sectionNum) {
                        targetElement = el;
                        break;
                    }
                }
            }
            
            // Second: Try case-insensitive keyword match for headings (e.g., "DateTime validation")
            if (!targetElement && ['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(el.tagName)) {
                const cleanText = text.toLowerCase().replace(/\s+(section|subsection|heading|paragraph)\s*$/i, '');
                if (elText.toLowerCase().includes(cleanText)) {
                    targetElement = el;
                    break;
                }
            }
            
            // Third: Fallback to text contains match
            if (!targetElement && elText.includes(text)) {
                targetElement = el;
                if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(el.tagName)) break;
            }
        }
        
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetElement.classList.add('highlight-scroll');
            setTimeout(() => targetElement.classList.remove('highlight-scroll'), 2000);
            return true; // Return true to stop polling
        }
        return false; 
    };

    const handleUpdateVersionDescription = async (e) => {
        if (e) e.preventDefault();
        if (!editingVersionId || !editingVersionText.trim()) return;
        const originalVersion = versionHistory.find(v => v.id === editingVersionId);
        if (originalVersion && originalVersion.change_description === editingVersionText.trim()) {
            setEditingVersionId(null);
            setEditingVersionText("");
            return;
        }
        setIsSavingVersion(true);
        await updateVersionDescription(projectId, editingVersionId, editingVersionText.trim(), setVersionHistory);
        setIsSavingVersion(false);
        setEditingVersionId(null);
        setEditingVersionText("");
    };

    // --- MEMOIZE DOCUMENT ---
    // Restore the processedContent variable name for compatibility if needed
    const processedDocumentContent = useMemo(() => {
        return preprocessContentForEditor(documentContent);
    }, [documentContent]);

    const memoizedDocument = useMemo(() => {
        const content = preprocessContentForView(documentContent);
        return <MemoizedMarkdown content={content} handleCitationClick={handleCitationClick} />;
    }, [documentContent]);

    const hasVersions = versionHistory.length > 0;

    // --- RENDER CONTENT ---
    const renderContent = () => {
        if (isHistoryLoading) return <div className="loader" style={{ margin: '4rem auto' }}></div>;
        
        if (!hasVersions) {
            return (
                <div className="section-content initial-generation-prompt">
                    <div className="item-icon-wrapper" style={{ width: '60px', height: '60px', borderRadius: '16px' }}>
                        <Wand2 size={32} />
                    </div>
                    <h2>Run Initial Analysis</h2>
                    <p style={{ maxWidth: '600px', color: '#888' }}>
                        Provide an initial goal for the AI agent to generate the first version of your document.
                    </p>
                    <textarea value={initialGoal} onChange={(e) => setInitialGoal(e.target.value)} rows={5} className="text-input prompt-input-area" />
                    <p className="prompt-helper-text">Tip: Be specific. Ask for a PDR, a technical spec, or a list of user stories.</p>
                    <button onClick={handleInitialGeneration} disabled={isAgentRunning}>
                        <Wand2 size={16} style={{ marginRight: '8px' }} /> {isAgentRunning ? "Generating..." : "Generate Initial Document"}
                    </button>
                    {isAgentRunning && ( <div className="loader" style={{ marginTop: '1rem' }}></div> )}
                </div>
            );
        }
        
        let title = "Live Document";
        let subtitle = null;
        if(activeVersionInfo === "UNSAVED") {
            title = "Live Document (Unsaved Changes)";
        } else if (activeVersionInfo) {
            title = "Viewing History";
            subtitle = (
                <p className="version-indicator">
                    <strong>{activeVersionInfo.description}</strong> ({new Date(activeVersionInfo.timestamp).toLocaleString()})
                </p>
            );
        }
        
        const placeholderText = activeTab === 'qa' ? "Ask a question about the document..." : "Describe the edit you want to make...";

        return (
            <div className={`workspace-grid ${isFocusMode ? 'focus-mode' : ''}`}>
                
                {/* LEFT PANEL */}
                <div className="section-content workspace-panel" style={{ padding: '0.5rem 0.5rem 0 0.5rem' }}> 
                    
                    <div className="pill-nav-container" style={{ padding: '0 0.5rem 0.5rem 0.5rem' }}>
                        <div className="pill-nav" style={{ width: '100%', maxWidth: '100%', flexWrap: 'nowrap' }}>
                             <button onClick={() => setActiveTab('toc')} className={`pill-tab-btn ${activeTab === 'toc' ? 'active' : ''}`} title="Table of Contents" style={{ flex: 1 }}>
                                <List size={16} /> Contents
                            </button>
                            <button onClick={() => setActiveTab('qa')} className={`pill-tab-btn ${activeTab === 'qa' ? 'active' : ''}`} style={{ flex: 1 }}> 
                                <HelpCircle size={16} /> Q&A 
                            </button>
                            <button onClick={() => setActiveTab('refine')} className={`pill-tab-btn ${activeTab === 'refine' ? 'active' : ''}`} style={{ flex: 1 }}> 
                                <Edit3 size={16} /> Edit
                            </button>
                        </div>
                    </div>
                    
                    {/* Position Relative wrapper to constrain the Left Drawer */}
                    <div className={`tab-content-container active-tab-${activeTab}`} style={{position: 'relative'}}>

                        {/* --- DRAWER: Suggestions (Left Side) --- */}
                        <SuggestionsDrawer 
                            isOpen={showSuggestionsDrawer}
                            onClose={() => setShowSuggestionsDrawer(false)}
                            suggestions={suggestions}
                            isLoading={suggestionsLoading}
                            onSelectSuggestion={(s) => {
                                // CHANGED: Directly refine instead of just filling input
                                sendRefinementInstruction(s);
                            }}
                            onRefresh={() => fetchSuggestions(projectId, documentContent)}
                        />

                        {/* --- DRAWER: Smart Update (Left Side) --- */}
                        <SmartUpdateDrawer 
                            isOpen={showUpdateDrawer}
                            onClose={() => setShowUpdateDrawer(false)}
                            isAnalyzing={isCheckingForUpdates}
                            suggestion={generatedSuggestion}
                            newFiles={updatesFromFiles}
                            onConfirm={handleApplyUpdate}
                        />

                        {/* --- Tab 1: Table of Contents --- */}
                         <div className="tab-panel" id="toc-panel" style={{ minHeight: 0 }}>
                            <div className="toc-list" style={{ minHeight: 0, padding: '0.5rem' }}>
                                {toc.length === 0 ? (
                                    <div className="chat-welcome">
                                        <div className="chat-welcome-icon"><List size={24} /></div>
                                        <h4>Table of Contents</h4>
                                        <p style={{color: '#888'}}>This document has no headings to display.</p>
                                    </div>
                                ) : (
                                    toc.map((item, index) => (
                                        <button key={index} className={`toc-item toc-level-${item.level}`} onClick={(e) => handleScrollToText(item.text, e)}>
                                            {item.text}
                                        </button>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* --- Tab 2: Q&A --- */}
                        <div className="tab-panel" id="qa-panel" style={{ minHeight: 0 }}>
                            <div ref={qaChatContainerRef} className="chat-window" style={{ minHeight: 0, padding: '0.5rem 0.5rem 0 0.5rem' }}>
                                {qaHistory.length === 0 && (
                                    <div className="chat-welcome">
                                        <div className="chat-welcome-icon"> <HelpCircle size={24} /> </div>
                                        <h4>Q&A Mode</h4>
                                        <p>Ask any question about the document. The agent will answer without modifying it.</p>
                                    </div>
                                )}
                                {qaHistory.map((msg, index) => (
                                    <div key={index} className={`chat-message ${msg.role === 'user' ? 'user' : 'agent'}`}>
                                        <strong>{msg.role === 'user' ? 'You' : 'Agent'}</strong>
                                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                                            {msg.content}
                                        </ReactMarkdown>
                                        {msg.suggestion && (
                                            <button className="prompt-suggestion-btn qa-suggestion-btn" onClick={() => handleQaSuggestionClick(msg.suggestion)}>
                                                <span>{msg.suggestion}</span>
                                            </button>
                                        )}
                                        {msg.scrollToText && (
                                            <button className="prompt-suggestion-btn scroll-to-btn" onClick={(e) => handleScrollToText(msg.scrollToText, e)}>
                                                <LocateFixed size={14} /> <span>Go to section</span>
                                            </button>
                                        )}
                                    </div>
                                ))}
                                {isAgentRunning && ( <div className="loader-bubble"> <div className="loader"></div> </div> )}
                            </div>
                            <form onSubmit={handleChatSubmit} className="chat-form" style={{ padding: '0.5rem' }}>
                                <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder={placeholderText} className="text-input" disabled={isAgentRunning || !documentContent} spellCheck="false" />
                                <button type="submit" disabled={isAgentRunning || !chatInput.trim() || !documentContent} className="action-btn"> <Send size={16} /> </button>
                            </form>
                        </div>

                        {/* --- Tab 3: Refine (Edit) --- */}
                        <div className="tab-panel" id="refine-panel" style={{ minHeight: 0 }}>
                            <div ref={refineChatContainerRef} className="chat-window" style={{ minHeight: 0, padding: '0.5rem 0.5rem 0 0.5rem' }}>
                                
                                {/* --- UPDATED: New Action Cards --- */}
                                {refineHistory.length === 0 && (
                                     <div className="chat-welcome" style={{ justifyContent: 'flex-start', paddingTop: '20px' }}>
                                        <div className="chat-welcome-icon" style={{ backgroundColor: 'transparent', color: 'var(--text-color)', marginBottom: 0 }}> 
                                            <Edit3 size={28} /> 
                                        </div>
                                        <h4 style={{ marginBottom: '25px', marginTop: '10px' }}>What would you like to edit?</h4>
                                        
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', padding: '0 10px' }}>
                                            
                                            {/* Action Card 1: Suggestions */}
                                            <button 
                                                onClick={handleOpenSuggestions}
                                                disabled={isAgentRunning}
                                                className="action-card-btn"
                                            >
                                                <div className="action-card-icon" style={{backgroundColor: 'rgba(255, 193, 7, 0.1)', color: '#ffc107'}}>
                                                    <Sparkles size={20} />
                                                </div>
                                                <div className="action-card-text">
                                                    <strong>Get AI Suggestions</strong>
                                                    <span>Analyze live document for improvements</span>
                                                </div>
                                                <div className="action-card-arrow"><List size={16}/></div>
                                            </button>

                                            {/* Action Card 2: Check Updates */}
                                            <button 
                                                onClick={handleCheckForUpdates} 
                                                disabled={isAgentRunning}
                                                className="action-card-btn"
                                            >
                                                 <div className="action-card-icon" style={{backgroundColor: 'rgba(23, 162, 184, 0.1)', color: '#17a2b8'}}>
                                                    <Bot size={20} />
                                                </div>
                                                <div className="action-card-text">
                                                    <strong>Check Project Updates</strong>
                                                    <span>Sync new files into this document</span>
                                                </div>
                                                <div className="action-card-arrow"><RefreshCcw size={16}/></div>
                                            </button>
                                        </div>
                                    </div>
                                )}
                                
                                {refineHistory.map((msg, index) => (
                                    <div key={index} className={`chat-message ${msg.role === 'user' ? 'user' : 'agent'}`}>
                                        <strong>{msg.role === 'user' ? 'You' : 'Agent'}</strong>
                                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                ))}
                                {isAgentRunning && ( <div className="loader-bubble"> <div className="loader"></div> </div> )}
                            </div>
                            
                            <form onSubmit={handleChatSubmit} className="chat-form" style={{ padding: '0.5rem' }}>
                                <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder={placeholderText} className="text-input" disabled={isAgentRunning || !documentContent} spellCheck="false" />
                                <button type="submit" disabled={isAgentRunning || !chatInput.trim() || !documentContent} className="action-btn"> <Send size={16} /> </button>
                            </form>
                        </div>
                    </div>
                </div>

                {/* RIGHT PANEL (Document) - UNCHANGED logic, just re-rendered */}
                <div className="section-content workspace-panel document-panel" style={{ padding: '10px', display: 'flex', flexDirection: 'column' }}>
                    {/* Header */}
                    <div className="panel-header" style={{ gap: '10px', marginBottom: '0.5rem', paddingBottom: '0.5rem' }}>
                        <div>
                            <h2>{title}</h2>
                            {subtitle}
                        </div>
                        <div className="actions-group" style={{ display: 'flex', gap: '10px', alignItems: 'center', position: 'relative' }}>
                            
                            {/* Toggle Edit Mode Button - ONLY visible when not unsaved */}
                            {activeVersionInfo === null && (
                                <button 
                                    onClick={() => {
                                        setIsManualEditMode(true);
                                        // When entering edit mode, set as unsaved immediately so we can save back
                                        setActiveVersionInfo("UNSAVED"); 
                                    }} 
                                    className="btn-secondary"
                                    title="Edit Document"
                                >
                                    <Pencil size={16} style={{marginRight: '6px'}} /> Edit
                                </button>
                            )}

                            {activeVersionInfo === "UNSAVED" && (
                                <>
                                    {/* Cancel Button */}
                                    <button 
                                        onClick={() => {
                                            setIsManualEditMode(false);
                                            setActiveVersionInfo(null);
                                            // Revert content to last saved version
                                            if (versionHistory.length > 0) {
                                                setDocumentContent(versionHistory[0].content);
                                            }
                                        }} 
                                        className="btn-secondary"
                                        title="Cancel editing"
                                    >
                                        <X size={16} style={{marginRight: '6px'}} /> Cancel
                                    </button>

                                    {/* Save Button */}
                                    <button onClick={handleSaveManualChanges} className="btn-primary" title="Save changes">
                                        <Save size={16} style={{ marginRight: '6px' }} /> Save Edits
                                    </button>
                                </>
                            )}
                            
                            {activeVersionInfo && activeVersionInfo !== "UNSAVED" && (
                                <button onClick={handleRevertVersion} className="btn-secondary" title="Restore this version" disabled={isAgentRunning}>
                                    <RefreshCcw size={16} style={{ marginRight: '8px' }} /> Restore
                                </button>
                            )}
                            {!isFocusMode && (
                                <button onClick={toggleHistoryDrawer} className={`btn-secondary ${showHistoryDrawer ? 'active' : ''}`} title="Toggle Version History">
                                    <History size={16} style={{ marginRight: '6px' }}/> History
                                </button>
                            )}
                            {isFocusMode ? (
                                <>
                                    <button onClick={() => handleDownloadMarkdown()} className="btn-secondary" title="Download Markdown"> <FileDown size={16} /> </button>
                                    <button onClick={() => handleDownloadWithPdfmake()} className="btn-secondary" title="Download PDF"> <FileText size={16} /> </button>
                                    <button onClick={() => setIsFocusMode(false)} className="btn-secondary" title="Exit Focus"> <Minimize size={16} style={{ marginRight: '6px' }} /> Exit Focus </button>
                                </>
                            ) : (
                                <div className="dropdown-container" ref={actionsDropdownRef}>
                                    <button onClick={() => setShowActionsDropdown(!showActionsDropdown)} className={`btn-icon-only ${showActionsDropdown ? 'active' : ''}`} title="Document Actions" style={{ padding: '8px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <MoreVertical size={20} />
                                    </button>
                                    <div className={`action-dropdown ${showActionsDropdown ? 'show' : ''}`}>
                                        <div className="dropdown-menu-item" onClick={(e) => { setIsFocusMode(!isFocusMode); setShowActionsDropdown(false); e.stopPropagation(); }}>
                                            <Maximize size={16} /> <span>Enter Focus Mode</span>
                                        </div>
                                        <div className="dropdown-menu-item" onClick={() => handleDownloadMarkdown()}>
                                            <FileDown size={16} /> <span>Download Markdown</span>
                                        </div>
                                        <div className="dropdown-menu-item" onClick={() => handleDownloadWithPdfmake()}>
                                            <FileText size={16} /> <span>Download PDF</span>
                                        </div>
                                        <div className="dropdown-divider"></div>
                                        <div className="dropdown-menu-item" onClick={(e) => { toggleImportDrawer(); e.stopPropagation(); }} style={{ color: 'var(--button-bg)' }}>
                                            <DownloadCloud size={16} /> <span>Import from Docs</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Loading Overlay */}
                    {isAgentRunning && activeTab === 'refine' && (
                        <div className="document-overlay-container">
                            <div className="loader"></div>
                            <p>Refining Document...</p>
                        </div>
                    )}
                    
                    {/* Document Content - CONDITIONAL RENDERING */}
                    {/* IMPORTANT: Edit Mode gets overflow:hidden (editor handles scrolling), View Mode gets auto */}
                    <div ref={documentScrollRef} className="editor-wrapper" style={{ flexGrow: 1, minHeight: 0, position: 'relative', overflowY: isManualEditMode ? 'hidden' : 'auto' }}>
                       {isManualEditMode ? (
                           <RichTextEditor 
                               content={processedDocumentContent} 
                               onChange={handleManualContentUpdate}
                               editable={true}
                           />
                       ) : (
                           /* VIEW MODE: Uses Original Renderer for perfect style matching */
                           <div className=" markdown-content" style={{ padding: '2rem !important' }}>
                               {memoizedDocument}
                           </div>
                       )}
                    </div>

                    {/* HISTORY DRAWER */}
                    <div className={`history-drawer ${showHistoryDrawer ? 'open' : ''}`}>
                         <div className="history-drawer-header">
                            <h3>Version History</h3>
                            <button onClick={() => setShowHistoryDrawer(false)} className="detail-modal-close-btn" style={{position: 'static'}}><X size={20} /></button>
                         </div>
                         <div className="history-list" style={{padding: '0.5rem', gap: '0.8rem'}}>
                                <div className={`history-item history-item-live ${activeVersionInfo === null ? 'history-item-active' : ''}`} onClick={() => { if (versionHistory.length > 0) { setDocumentContent(versionHistory[0].content); } setActiveVersionInfo(null); toast.success("Loaded Live Version"); }} style={{ borderRadius: '8px', border: '2px solid var(--button-bg)', background: 'rgba(var(--button-bg-rgb), 0.05)' }}>
                                    <div className="history-item-icon" style={{ color: 'var(--button-bg)' }}><RefreshCcw size={20} /></div>
                                    <div className="history-item-details">
                                        <strong style={{ fontSize: '1rem', color: 'var(--button-bg)' }}>Current Version</strong>
                                        <div className="history-item-meta"> <span>Editing now...</span> </div>
                                    </div>
                                </div>
                                {versionHistory.map((v, i) => (
                                    <div key={v.id} className={`history-item ${activeVersionInfo?.timestamp === v.timestamp ? 'history-item-active' : ''} ${editingVersionId === v.id ? 'history-item-editing' : ''}`} style={{ animationDelay: `${i * 0.05}s`, opacity: 0, animation: 'fadeIn 0.3s forwards', padding: '12px', borderBottom: '1px solid var(--scroll-hover)' }}>
                                        {editingVersionId === v.id ? (
                                            <form className="history-edit-form" onSubmit={handleUpdateVersionDescription}>
                                                <label htmlFor="version-edit-input" style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#888' }}>Update Version Note</label>
                                                <div style={{ position: 'relative', width: '100%' }}>
                                                    <textarea id="version-edit-input" className="history-edit-input text-input" value={editingVersionText} onChange={(e) => { if (e.target.value.length <= 50) { setEditingVersionText(e.target.value); } }} maxLength={50} autoFocus onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleUpdateVersionDescription(); } }} disabled={isSavingVersion} rows={2} style={{ fontSize: '0.9rem', padding: '8px', paddingBottom: '20px', width: '100%', resize: 'none' }} />
                                                    <span style={{ position: 'absolute', right: '8px', bottom: '4px', fontSize: '0.7rem', color: editingVersionText.length === 50 ? 'var(--button-bg)' : '#ccc', pointerEvents: 'none' }}>{editingVersionText.length}/50</span>
                                                </div>
                                                <div className="history-edit-actions">
                                                    <button type="button" className="btn-secondary" onClick={() => setEditingVersionId(null)} disabled={isSavingVersion} title="Cancel" style={{ fontSize: '0.8rem', padding: '4px 8px' }}>Cancel</button>
                                                    <button type="submit" className="btn-primary" disabled={isSavingVersion || !editingVersionText.trim()} title="Save" style={{ fontSize: '0.8rem', padding: '4px 8px' }}>{isSavingVersion ? "Saving..." : "Save"}</button>
                                                </div>
                                            </form>
                                        ) : (
                                            <>
                                                <div className="history-item-icon" onClick={() => { setDocumentContent(v.content); setActiveVersionInfo({ timestamp: v.timestamp, description: v.change_description }); toast.success(`Viewing version: ${new Date(v.timestamp).toLocaleTimeString()}`); setScrollToTextOnLoad(v.change_description); }}><FileClock size={18} /></div>
                                                <div className="history-item-details" onClick={() => { setDocumentContent(v.content); setActiveVersionInfo({ timestamp: v.timestamp, description: v.change_description }); toast.success(`Viewing version: ${new Date(v.timestamp).toLocaleTimeString()}`); setScrollToTextOnLoad(v.change_description); }}>
                                                    <strong style={{ fontSize: '0.95rem', marginBottom: '4px', display: 'block' }}>{v.change_description}</strong>
                                                    <div className="history-item-meta" style={{ fontSize: '0.75rem', color: '#999' }}><span>{new Date(v.timestamp).toLocaleString(undefined, {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</span><span>•</span><span>{v.user_email?.split('@')[0]}</span></div>
                                                </div>
                                                <div className="history-item-actions">
                                                    <button className="history-edit-btn" title="Edit note" onClick={(e) => { e.stopPropagation(); setEditingVersionId(v.id); setEditingVersionText(v.change_description); }}><Edit2 size={14} /></button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                ))}
                         </div>
                    </div>

                    {/* IMPORT DRAWER */}
                    <ImportDrawer 
                        isOpen={showImportDrawer}
                        onClose={() => setShowImportDrawer(false)}
                        documents={project?.documents || []}
                        onImport={handleImportDocument}
                    />

                </div>
            </div>
        );
    };

    return (
        <div className="workspace-container">
            <SourceViewerModal isOpen={isSourceModalOpen} onClose={() => setIsSourceModalOpen(false)} fileName={sourceModalFileName} content={sourceModalContent} />
            <ConfirmationModal isOpen={isResetModalOpen} onClose={() => setIsResetModalOpen(false)} onConfirm={handleConfirmReset} title="Reset Workspace?" message="All generated document versions will be lost. Continue?" />

            <div style={{ marginBottom: '0rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '-8px' }}>
                    <Breadcrumbs />
                    {hasVersions && (
                        <button onClick={() => setIsResetModalOpen(true)} className="btn-danger-outline"> <RefreshCcw size={14} style={{ marginRight: '8px' }} /> Reset Workspace </button>
                    )}
                </div>
                <h1 style={{ marginTop: '0rem', marginBottom: '0rem', fontSize: '2.2rem' }}>Agent Workspace</h1>
                <p style={{ color: '#888', marginTop: '0', marginBottom: '10px' }}>Project: {project?.name || 'Loading...'}</p>
            </div>
            {renderContent()}
            
            <style>{`
                /* Added Highlight Animation for Scrolling */
                @keyframes highlight-fade {
                    0% { 
                        background-color: #ffeb3b; 
                        box-shadow: 0 0 0 4px rgba(255, 235, 59, 0.3);
                    }
                    100% { 
                        background-color: transparent; 
                        box-shadow: none;
                    }
                }
                .highlight-scroll {
                    animation: highlight-fade 2s ease-out;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: -4px -8px;
                }

                .action-card-btn {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 15px;
                    background-color: var(--bg-color); /* Neutral background */
                    border: 1px solid var(--scroll-hover);
                    border-radius: 12px;
                    cursor: pointer;
                    text-align: left;
                    transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
                    width: 100%;
                }
                
                /* CLEANER HOVER EFFECT (NEUTRAL) */
                .action-card-btn:hover {
                    background-color: #ffffff; 
                    border-color: #b0b0b0; /* Neutral darker grey border */
                    transform: translateY(-3px) scale(1.01); 
                    box-shadow: 0 8px 20px rgba(0,0,0,0.1); 
                }

                .action-card-icon {
                    width: 42px;
                    height: 42px;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                    transition: transform 0.2s ease;
                }
                
                /* Animate Icon on Hover */
                .action-card-btn:hover .action-card-icon {
                    transform: scale(1.1) rotate(5deg);
                }

                .action-card-text {
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                }
                .action-card-text strong {
                    font-size: 0.95rem;
                    margin-bottom: 3px;
                    color: var(--text-color);
                }
                .action-card-text span {
                    font-size: 0.8rem;
                    color: #888;
                }
                
                .action-card-arrow {
                    color: #ccc;
                    transition: all 0.2s ease;
                    opacity: 0.5;
                }
                
                /* Animate Arrow on Hover */
                .action-card-btn:hover .action-card-arrow {
                    color: var(--button-bg); /* Use theme color only for arrow */
                    opacity: 1;
                    transform: translateX(4px);
                }

                /* AI Diagram Block Styles (New) */
                .ai-diagram-block {
                    margin: 1.5rem 0;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    overflow: hidden;
                    background-color: #fafafa;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }
                .ai-diagram-header {
                    padding: 8px 12px;
                    background-color: #f1f1f1;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 0.85rem;
                    color: #555;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .ai-diagram-header::before {
                    content: "⚡"; 
                }
                .ai-diagram-img {
                    display: block;
                    width: 100%;
                    height: auto;
                }

                /* Live Document View Mode Padding (RESTORED) */
                .markdown-content {
                    padding:  0.5rem !important; 
                }

                .history-item-details {
    /* These lines force text to stay inside the box */
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    max-width: 100%; /* Ensure it respects the drawer width */
}

.history-item-details strong {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

/* Optional: Make the current version item also safe */
.history-item-live .history-item-details {
    white-space: normal; /* Live version can wrap text */
}
            `}</style>
        </div>
    );
};

export default AgentWorkspace;