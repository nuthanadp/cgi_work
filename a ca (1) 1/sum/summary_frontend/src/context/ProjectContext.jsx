import React, { createContext, useState, useEffect, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import { fetchWithToken } from '../api';

export const ProjectContext = createContext();

// --- Helper: Parse Error Messages ---
const parseErrorMessage = (error) => {
    const rawMessage = String(error?.message || error);

    if (rawMessage.includes("Quota exceeded")) {
        return "API Quota Exceeded: Please check your plan and billing details.";
    }
    if (rawMessage.includes("Connection error")) {
        return "Connection Error: Could not connect to the API. Please check your .env file and server logs.";
    }
    if (rawMessage.includes("Failed to fetch")) {
        return "Network Error: Could not reach the backend. Is the server running?";
    }
    if (rawMessage.includes("Incorrect current password")) {
        return "Incorrect current password. Please try again.";
    }
    
    return "An unexpected error occurred. Please try again.";
};


export const ProjectProvider = ({ children }) => {
    const [projects, setProjects] = useState({});
    const [isInitialLoad, setIsInitialLoad] = useState(true);
    const [loading, setLoading] = useState(false); // General loading for project actions
    const [error, setError] = useState(null);

    // Agent workspace state
    const [documentContent, setDocumentContent] = useState('');
    const [qaHistory, setQaHistory] = useState([]);
    const [refineHistory, setRefineHistory] = useState([]);
    const [isAgentRunning, setIsAgentRunning] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const [suggestionsLoading, setSuggestionsLoading] = useState(false); 

    const abortControllerRef = useRef(null);
    // ===========================================
    // NEW STATE FOR AST WORKSPACE
    // ===========================================
    const [documentAST, setDocumentAST] = useState(null);

    

    // --- fetchProjects ---
    const fetchProjects = useCallback(async () => {
        console.log("🚀 [ProjectContext] Attempting to fetch projects...");
        try {
            const response = await fetchWithToken('/projects');
            const data = await response.json();
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || `Failed to fetch projects (status ${response.status})`);
            }
            const projectsById = data.reduce((acc, proj) => {
                if (proj && proj.id) {
                    acc[proj.id] = proj;
                }
                return acc;
            }, {});
            setProjects(projectsById);
        } catch (err) {
            setError(err.message);
            toast.error(`Failed to load projects: ${parseErrorMessage(err)}`);
        } finally {
            setIsInitialLoad(false);
        }
    }, []);

    // --- useEffect for initial fetchProjects ---
    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);
     const loadDocumentIntoWorkspace = async (projectId, documentData) => {
        setIsAgentRunning(true);
        setDocumentAST(null);

        try {
            const response = await fetchWithToken(`/projects/${projectId}/load_ast`, {
                method: 'POST',
                body: JSON.stringify({ document: documentData })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "AST load failed");

            setDocumentAST(data.ast);
            setDocumentContent(data.markdown || "");
            toast.success("Document loaded into workspace!");

        } catch (err) {
            toast.error(`Load failed: ${parseErrorMessage(err)}`);
        } finally {
            setIsAgentRunning(false);
        }
    };


    // ==================================================
    // NEW: APPLY AST PATCHES LOCALLY
    // ==================================================
    const applyAstPatches = (ast, patches) => {
        let newAst = JSON.parse(JSON.stringify(ast));
        try {
            for (const patch of patches) {
                // PATCH FORMAT EXAMPLE:
                // { op: "replace", target: "/sections/1/title", value: "New Title" }
                const path = patch.target.split("/").slice(1);
                let ref = newAst;
                for (let i = 0; i < path.length - 1; i++) {
                    ref = ref[path[i]];
                }
                ref[path[path.length - 1]] = patch.value;
            }
        } catch (e) {
            console.error("AST patch error:", e);
        }
        return newAst;
    };


    // ==================================================
    // NEW: AST → MARKDOWN SERIALIZATION
    // ==================================================
    const astToMarkdown = (ast) => {
        try {
            let md = "";
            for (const sec of ast.sections || []) {
                md += `# ${sec.title}\n\n`;
                for (const p of sec.paragraphs || []) {
                    md += p.text + "\n\n";
                }
            }
            return md.trim();
        } catch {
            return documentContent;
        }
    };


    // ==================================================
    // NEW: EDIT USING AST (WORKSPACE MAIN ACTION)
    // ==================================================
    const editDocumentAST = async (projectId, instruction) => {
        if (!documentAST) {
            toast.error("No document loaded in workspace");
            return;
        }

        setIsAgentRunning(true);
        setRefineHistory(prev => [...prev, { role: 'user', content: instruction }]);

        try {
            const response = await fetchWithToken(`/projects/${projectId}/ast_edit`, {
                method: 'POST',
                body: JSON.stringify({
                    instruction,
                    ast: documentAST
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "AST edit failed");

            const patches = data.patches || [];

            const newAst = applyAstPatches(documentAST, patches);
            const newMd = astToMarkdown(newAst);

            setDocumentAST(newAst);
            setDocumentContent(newMd);

            setRefineHistory(prev => [...prev, { role: 'assistant', content: "(Updated)" }]);
            toast.success("Edit applied!");

        } catch (err) {
            toast.error(parseErrorMessage(err));
        } finally {
            setIsAgentRunning(false);
        }
    };
    
    // --- createProject ---
    const createProject = async (projectName) => {
        setLoading(true);
        try {
            const response = await fetchWithToken('/projects', {
                method: 'POST',
                body: JSON.stringify({ name: projectName }),
            });
            const newProject = await response.json();
            if (!response.ok) throw new Error(newProject.error || 'Failed to create project');

            setProjects(prev => ({ ...prev, [newProject.id]: newProject }));
            toast.success(`Project "${projectName}" created!`);
            return newProject.id;
        } catch (err) {
            setError(err.message);
            toast.error(parseErrorMessage(err));
            return null;
        } finally {
            setLoading(false);
        }
    };

    // --- removeProject ---
    const removeProject = async (projectId) => {
        setLoading(true);
        try {
            const response = await fetchWithToken(`/projects/${projectId}`, { method: 'DELETE' });
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to delete project');
            }
            setProjects(prev => {
                const newProjects = { ...prev };
                delete newProjects[projectId];
                return newProjects;
            });
            toast.success('Project deleted.');
        } catch (err) {
            setError(err.message);
            toast.error(parseErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    // --- analyzeAndAddFiles (UPDATED LOGIC) ---
    const analyzeAndAddFiles = async (projectId, files, fileType, skipAnalysis = false) => {
        const existingFileNames = new Set(
            projects[projectId]?.[fileType]?.map(f => f.fileName) || []
        );

        const newFiles = files.filter(file => {
            if (existingFileNames.has(file.name)) {
                toast.error(`Skipped duplicate file: ${file.name}`);
                return false;
            }
            return true;
        });

        if (newFiles.length === 0) {
            toast.success('No new files to upload.');
            return;
        }

        setLoading(true);
        // Update action name description
        const actionName = skipAnalysis ? "Uploading (Raw)" : "Analyzing";
        const toastId = toast.loading(`${actionName} ${newFiles.length} file(s)...`);

        const endpointMap = {
            documents: '/analyze_document',
            transcripts: '/analyze_transcript'
        };
        const addEndpointMap = {
            documents: `/projects/${projectId}/documents`,
            transcripts: `/projects/${projectId}/transcripts`
        };

        try {
            for (const file of newFiles) {
                // Detect if file might be a JIRA ticket
                const isLikelyJira = file.name.toLowerCase().includes('jira') || 
                                    file.name.toLowerCase().match(/\.(doc|docx)$/);
                
                // Update toast with enhancement status for JIRA files
                if (isLikelyJira && !skipAnalysis) {
                    toast.loading(`🤖 Enhancing JIRA ticket: ${file.name}...`, { id: toastId });
                }
                
                // 1. Extract Text
                const formData = new FormData();
                formData.append('file', file);
                
                // --- FIXED LOGIC HERE ---
                // If skipAnalysis is true, we want smart_format to be 'false'.
                // If skipAnalysis is false, we want smart_format to be 'true'.
                formData.append('smart_format', skipAnalysis ? 'false' : 'true');
                // ------------------------

                const textResponse = await fetchWithToken('/extract_text', { method: 'POST', body: formData });
                const textData = await textResponse.json();
                if (!textResponse.ok) throw new Error(textData.error || `Failed to extract text from ${file.name}`);

                // Update status after extraction/enhancement
                if (!skipAnalysis) {
                    toast.loading(`📊 Analyzing: ${file.name}...`, { id: toastId });
                }

                let analysisData = {};

                if (skipAnalysis) {
                    // --- OPTION A: Skip Categorization, save raw text and potential PDF URL ---
                    analysisData = {
                        extracted_content: textData.text, // This will be raw text
                        categorized_json: {},
                        summary: "Analysis skipped (Raw Content)",
                        is_raw: true,
                        // ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                        // IMPORTANT: Capture the PDF URL from the backend response
                        pdf_preview_url: textData.pdf_preview_url 
                        // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
                    };
                } else {
                    // --- OPTION B: Full AI Analysis (Categorization) ---
                    const analysisPayload = fileType === 'transcripts'
                        ? { transcript: textData.text }
                        : { text: textData.text };

                    const analysisResponse = await fetchWithToken(endpointMap[fileType], {
                        method: 'POST',
                        body: JSON.stringify(analysisPayload)
                    });
                    const apiData = await analysisResponse.json();
                    if (!analysisResponse.ok) throw new Error(apiData.error || `Failed to analyze ${file.name}`);
                    analysisData = apiData;
                }

                // 2. Save to Database
                // ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                // We must send the pdf_preview_url to be saved in the database
                const addResponse = await fetchWithToken(addEndpointMap[fileType], {
                    method: 'POST',
                    body: JSON.stringify({ 
                        fileName: file.name, 
                        analysis: analysisData,
                        // THIS IS THE CRITICAL MISSING LINE IN YOUR CODE:
                        pdf_preview_url: analysisData.pdf_preview_url 
                    })
                });
                // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
                
                const addedFileData = await addResponse.json();
                if (!addResponse.ok) throw new Error(addedFileData.error || 'Failed to save file');

                // 3. Update State
                setProjects(prev => ({
                    ...prev,
                    [projectId]: {
                        ...prev[projectId],
                        [fileType]: [...prev[projectId][fileType], addedFileData]
                    }
                }));
            }
            toast.success('File processed successfully!', { id: toastId });
        } catch (err) {
            setError(err.message);
            toast.error(parseErrorMessage(err), { id: toastId });
        } finally {
            setLoading(false);
        }
    };

    // --- executeAgentGoal ---
    const executeAgentGoal = async (projectId, goal) => {
        setIsAgentRunning(true);
        setError(null);
        setDocumentContent('');
        setQaHistory([]);
        setRefineHistory([]);
        setSuggestions([]); 

        const currentProject = projects[projectId];
        if (!currentProject) {
            toast.error("Project data not loaded yet.");
            setIsAgentRunning(false);
            return;
        }

        const project_files_data = {
            documents: currentProject.documents.map(d => ({ fileName: d.fileName, analysis: d.analysis })),
            transcripts: currentProject.transcripts.map(t => ({ fileName: t.fileName, analysis: t.analysis }))
        };

        try {
            const response = await fetchWithToken(`/projects/${projectId}/execute_goal`, {
                method: 'POST',
                body: JSON.stringify({ goal, project_files_data }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `Server error: ${response.status}`);
            setDocumentContent(data.content);
            toast.success("Document generated successfully!");
        } catch (err) {
            toast.error(parseErrorMessage(err));
            setError(err.message);
        } finally {
            setIsAgentRunning(false);
        }
    };

    // --- askQuestion ---
    const askQuestion = async (projectId, question, currentContent) => {
        setIsAgentRunning(true);
        setQaHistory(prev => [...prev, { 
            role: 'user', 
            content: question, 
            suggestion: null, 
            scrollToText: null 
        }]);

        try {
            const response = await fetchWithToken(`/projects/${projectId}/ask_question`, {
                method: 'POST',
                body: JSON.stringify({ question, current_document: currentContent }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || `Failed to get answer: ${response.status}`);
            }
            
            setQaHistory(prev => [...prev, { 
                role: 'assistant', 
                content: data.answer, 
                suggestion: data.suggestion,
                scrollToText: data.scrollToText 
            }]);
            
        } catch (error) {
            toast.error(`Q&A failed: ${parseErrorMessage(error)}`);
            setQaHistory(prev => [...prev, { 
                role: 'assistant', 
                content: `Error: ${parseErrorMessage(error)}`, 
                suggestion: null,
                scrollToText: null 
            }]);
        } finally {
            setIsAgentRunning(false);
        }
    };
    
    // --- refineDocument ---
    const refineDocument = async (projectId, instruction, currentContent) => {
        setIsAgentRunning(true);
        setRefineHistory(prev => [...prev, { role: 'user', content: instruction }]);
        setDocumentContent(currentContent); // Show current content while loading

        try {
            const response = await fetchWithToken(`/projects/${projectId}/refine_document`, {
                method: 'POST',
                body: JSON.stringify({ instruction, current_document: currentContent }),
            });

            const data = await response.json(); 
            
            if (!response.ok) {
                throw new Error(data.error || `Refinement failed: ${response.status}`);
            }

            // Success! Set the new content.
            setDocumentContent(data.content);
            return data.content; 

        } catch (error) {
            toast.error(`Refinement failed: ${parseErrorMessage(error)}`);
            setRefineHistory(prev => [...prev, { role: 'assistant', content: `Error: ${parseErrorMessage(error)}` }]);
            setDocumentContent(currentContent); // Revert to original content on error
            return null;
        } finally {
            setIsAgentRunning(false);
        }
    };
    
    // --- fetchSuggestions ---
    const fetchSuggestions = useCallback((projectId, currentContent) => {
        if (!currentContent || currentContent.trim().length < 20 || isAgentRunning) return;

        console.log("📡 [Suggestions] Sending request...");
        setSuggestionsLoading(true);

        fetchWithToken(`/projects/${projectId}/suggestions`, {
            method: 'POST',
            body: JSON.stringify({ current_document: currentContent }),
        })
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                setSuggestions(data);
                console.log("✅ Suggestions updated");
            } else {
                throw new Error("Invalid suggestions format from server");
            }
        })
        .catch(error => {
            toast.error(parseErrorMessage(error));
            console.error("❌ Suggestions error:", error.message);
            setSuggestions([]); 
        })
        .finally(() => {
            setSuggestionsLoading(false);
        });

    }, [isAgentRunning]);

    // --- clearSuggestions ---
    const clearSuggestions = () => {
        setSuggestions([]);
    };

    // --- downloadAnalysis ---
    const downloadAnalysis = async (analysisData, fileName, fileType) => {
        const toastId = toast.loading('Preparing download...');
        const endpoint = fileType === 'documents' ? '/download' : '/download_transcript';

        try {
            const response = await fetchWithToken(endpoint, {
                method: 'POST',
                body: JSON.stringify(analysisData)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${fileName.split('.')[0]}_analysis.json`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            toast.success('Download started!', { id: toastId });

        } catch (err) {
            toast.error(parseErrorMessage(err), { id: toastId });
        }
    };

    // --- removeFileFromProject ---
    const removeFileFromProject = async (projectId, fileType, fileId) => {
        const toastId = toast.loading('Deleting file...');
        try {
            const response = await fetchWithToken(`/projects/${projectId}/${fileType}/${fileId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Failed to delete file');
            }

            setProjects(prev => {
                const updatedProjects = { ...prev };
                const projectToUpdate = updatedProjects[projectId];
                if (projectToUpdate && projectToUpdate[fileType]) {
                    projectToUpdate[fileType] = projectToUpdate[fileType].filter(file => file.id !== fileId);
                }
                return updatedProjects;
            });

            toast.success('File deleted.', { id: toastId });

        } catch (err) {
            toast.error(parseErrorMessage(err), { id: toastId });
        }
    };

    // --- resetProjectWorkspace ---
    const resetProjectWorkspace = async (projectId) => {
        try {
            const response = await fetchWithToken(`/projects/${projectId}/versions`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to reset workspace.');
            }
            
            setQaHistory([]);
            setRefineHistory([]);
            setSuggestions([]); 

            toast.success("Workspace has been reset!");
            return true;
        } catch (error) {
            toast.error(parseErrorMessage(error));
            return false;
        }
    };
    
    // --- updateVersionDescription ---
    const updateVersionDescription = async (projectId, versionId, newDescription, setVersionHistory) => {
        let oldHistory = null;
        setVersionHistory(prev => {
            oldHistory = [...prev];
            return prev.map(v => 
                v.id === versionId ? { ...v, change_description: newDescription } : v
            );
        });

        try {
            const response = await fetchWithToken(`/projects/${projectId}/versions/${versionId}`, {
                method: 'PUT',
                body: JSON.stringify({ description: newDescription }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Failed to save update");
            }
            toast.success("Version name updated!");
        } catch (error) {
            setVersionHistory(oldHistory);
            toast.error(`Error: ${parseErrorMessage(error)}`);
        }
    };

    // --- Cleanup useEffect ---
    useEffect(() => {
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    // --- Context Value ---
    const value = {
        projects,
        loading,
        error,
        isInitialLoad,
        fetchProjects,
        createProject,
        removeProject,
        resetProjectWorkspace,
        analyzeAndAddFiles,
        documentContent,
        qaHistory,
        setQaHistory,
        refineHistory,
        setRefineHistory,
        isAgentRunning,
        executeAgentGoal,
        refineDocument,
        askQuestion, 
        downloadAnalysis,
        removeFileFromProject,
        setDocumentContent,
        suggestions,
        fetchSuggestions,
        suggestionsLoading,
        setSuggestions,
        clearSuggestions,
        updateVersionDescription
    };

    return (
        <ProjectContext.Provider value={value}>
            {children}
        </ProjectContext.Provider>
    );
};