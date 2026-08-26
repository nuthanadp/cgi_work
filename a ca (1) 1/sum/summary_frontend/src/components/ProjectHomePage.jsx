import React, { useState, useContext, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { ProjectContext } from '../context/ProjectContext';
import ConfirmationModal from './ConfirmationModal';
import { 
    FolderPlus, Search, Trash2, ChevronRight, 
    FileText, Mic, Users, Folder, Inbox,
    ChevronLeft, ChevronsLeft, ChevronsRight 
} from 'lucide-react';

const ProjectHomePage = () => {
    const { projects, createProject, removeProject, loading } = useContext(ProjectContext);
    
    // --- State Management ---
    const [newProjectName, setNewProjectName] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
    const [projectToDelete, setProjectToDelete] = useState(null);

    const ITEMS_PER_PAGE = 5; 
    const MAX_NAME_LENGTH = 50;

    // --- Handlers ---
    const handleCreate = async () => {
        if (!newProjectName.trim()) return;
        await createProject(newProjectName.trim());
        setNewProjectName("");
    };

    const handleDeleteClick = (e, project) => {
        e.preventDefault(); 
        e.stopPropagation();
        setProjectToDelete(project);
        setIsConfirmModalOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (projectToDelete) {
            await removeProject(projectToDelete.id);
        }
        setIsConfirmModalOpen(false);
        setProjectToDelete(null);
    };

    // --- Data Logic ---
    const projectList = Object.values(projects || {});
    
    const filteredProjects = useMemo(() => {
        return projectList.filter(p => 
            p.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [projectList, searchQuery]);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery]);

    const totalPages = Math.ceil(filteredProjects.length / ITEMS_PER_PAGE);
    const currentProjects = filteredProjects.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    return (
        <div className="page-wrapper" style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: '2rem' }}>
            <ConfirmationModal
                isOpen={isConfirmModalOpen}
                onClose={() => setIsConfirmModalOpen(false)}
                onConfirm={handleConfirmDelete}
                title={`Delete Project "${projectToDelete?.name}"?`}
                message="This will permanently delete the project and all associated documents. This action cannot be undone."
            />

            {/* Header Section */}
            <div style={{ marginBottom: '1.5rem', textAlign: 'center', paddingTop: '0' }}> {/* Reduced margins/padding */}
                <h1 style={{ marginTop: '0rem', fontSize: '2.5rem', fontWeight: '800', marginBottom: '0.5rem' }}>Welcome Back</h1>
                <p style={{ color: '#888', marginTop: '0', fontSize: '1.1rem' }}>Manage your requirements and analysis projects.</p>
            </div>

            {/* Single Column Layout Wrapper */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}> {/* Reduced gap from 2rem to 1rem */}
                
                {/* 1. Create New Project Section */}
                <div className="section-content">
                    <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <FolderPlus size={24} /> Create New Project
                    </h2>
                    <div style={{ display: 'flex', gap: '10px', marginTop: '1rem' }}> {/* Reduced marginTop */}
                        
                        {/* Input Wrapper for Counter */}
                        <div style={{ position: 'relative', flexGrow: 1 }}>
                            <input 
                                type="text" 
                                className="text-input" 
                                placeholder="Enter project name..." 
                                value={newProjectName}
                                onChange={(e) => {
                                    if (e.target.value.length <= MAX_NAME_LENGTH) {
                                        setNewProjectName(e.target.value);
                                    }
                                }}
                                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                                disabled={loading}
                                maxLength={MAX_NAME_LENGTH} 
                                style={{ width: '100%', paddingRight: '60px', boxSizing: 'border-box' }} 
                            />
                            {/* Character Counter */}
                            <span style={{ 
                                position: 'absolute', 
                                right: '12px', 
                                top: '50%', 
                                transform: 'translateY(-50%)',
                                fontSize: '0.8rem',
                                fontWeight: '600',
                                color: newProjectName.length === MAX_NAME_LENGTH ? '#ff3b3b' : '#ccc',
                                pointerEvents: 'none'
                            }}>
                                {newProjectName.length}/{MAX_NAME_LENGTH}
                            </span>
                        </div>

                        <button 
                            className="btn-primary" 
                            onClick={handleCreate} 
                            disabled={!newProjectName.trim() || loading}
                            style={{ minWidth: '120px' }}
                        >
                            {loading ? '...' : 'Create'}
                        </button>
                    </div>
                </div>

                {/* 2. Existing Projects List Section */}
                <div className="section-content">
                    {/* Header with Search */}
                    <div className="results-header" style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        width: '100%',
                        maxWidth: '100%', 
                        marginBottom: '1rem', /* Reduced margin */
                        flexWrap: 'wrap',
                        gap: '1rem'
                    }}>
                        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Folder size={24} /> Existing Projects ({filteredProjects.length})
                        </h2>
                        <div className="search-input-container" style={{ width: '300px', margin: 0 }}>
                            <Search className="search-input-icon" size={16} />
                            <input 
                                type="text" 
                                placeholder="Search projects..." 
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="text-input"
                                style={{ paddingLeft: '35px', fontSize: '0.9rem', width: '100%' }}
                            />
                        </div>
                    </div>

                    {/* List Container */}
                    <div className="project-list-container" style={{ maxHeight: 'none', overflow: 'visible', height: 'auto', width: '100%' }}>
                        {currentProjects.length > 0 ? (
                            <div key={currentPage + searchQuery} className="animate-list-items">
                                {currentProjects.map((project, index) => (
                                    <Link 
                                        to={`/projects/${project.id}`} 
                                        key={project.id} 
                                        style={{ textDecoration: 'none', color: 'inherit', display: 'block', marginBottom: '12px' }}
                                    >
                                        <div 
                                            className="project-list-item"
                                            style={{ animationDelay: `${index * 0.05}s` }}
                                        >
                                            <div className="project-info">
                                                <h3>{project.name}</h3>
                                                <div className="project-stats">
                                                    <span className="stat-item"><FileText size={14} /> {project.documents?.length || 0} Docs</span>
                                                    <span className="stat-item"><Mic size={14} /> {project.transcripts?.length || 0} Transcripts</span>
                                                    <span className="stat-item"><Users size={14} /> {1 + (project.members?.length || 0)} Member{project.members?.length !== 0 ? 's' : ''}</span>
                                                </div>
                                            </div>
                                            <div className="project-actions">
                                                <button 
                                                    className="action-btn" 
                                                    onClick={(e) => handleDeleteClick(e, project)}
                                                    title="Delete Project"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                                <div className="project-arrow-bg">
                                                    <ChevronRight size={20} />
                                                </div>
                                            </div>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <div className="project-empty-state animate-list-items">
                                <Inbox size={48} opacity={0.5} />
                                <h3>{searchQuery ? "No Matches Found" : "No Projects Yet"}</h3>
                                <p>{searchQuery ? "Try a different search term." : "Create a new project to get started."}</p>
                            </div>
                        )}
                    </div>

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div className="pagination-container">
                            <button 
                                className="pagination-btn" 
                                disabled={currentPage === 1} 
                                onClick={() => setCurrentPage(1)}
                                title="First Page"
                            >
                                <ChevronsLeft size={20} />
                            </button>
                            <button 
                                className="pagination-btn" 
                                disabled={currentPage === 1} 
                                onClick={() => setCurrentPage(prev => prev - 1)}
                                title="Previous"
                            >
                                <ChevronLeft size={20} />
                            </button>
                            
                            <span className="pagination-info">Page {currentPage} of {totalPages}</span>
                            
                            <button 
                                className="pagination-btn" 
                                disabled={currentPage === totalPages} 
                                onClick={() => setCurrentPage(prev => prev + 1)}
                                title="Next"
                            >
                                <ChevronRight size={20} />
                            </button>
                            <button 
                                className="pagination-btn" 
                                disabled={currentPage === totalPages} 
                                onClick={() => setCurrentPage(totalPages)}
                                title="Last Page"
                            >
                                <ChevronsRight size={20} />
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProjectHomePage;