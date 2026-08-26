import React, { useContext, useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ProjectContext } from '../context/ProjectContext';
import ConfirmationModal from './ConfirmationModal';
import Breadcrumbs from './Breadcrumbs';
import { Users, UserCheck, UserPlus, X, Search, FileText, Mic, Bot, Trash2, ChevronRight } from 'lucide-react';
import { fetchWithToken } from '../api';
import toast from 'react-hot-toast';
import { jwtDecode } from 'jwt-decode';

// ===================== ManageTeamModal =====================
const ManageTeamModal = ({ project, isOpen, onClose, onTeamUpdate }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState(null);
  
  // --- Animation State ---
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);

  useEffect(() => {
    if (isOpen) {
        setIsAnimatingOut(false);
    }
  }, [isOpen]);

  // --- Search Logic ---
  useEffect(() => {
    if (!project?.id || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    const handler = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await fetchWithToken(
          `/projects/${project.id}/search_users?q=${searchQuery}`
        );
        const data = await response.json();
        if (response.ok) {
          setSearchResults(data);
        }
      } catch (error) {
        console.error('Search failed:', error);
      } finally {
        setLoading(false);
      }
    }, 500); 

    return () => clearTimeout(handler);
  }, [searchQuery, project?.id]);

  // --- Animation Handler ---
  const handleClose = () => {
    setIsAnimatingOut(true);
    setTimeout(() => {
        onClose();
        setIsAnimatingOut(false);
    }, 300);
  };

  const handleAddMember = async (email) => {
    if (!project?.id) return;
    setLoading(true);
    setSearchQuery('');
    setSearchResults([]);
    try {
      const response = await fetchWithToken(`/projects/${project.id}/members`, {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to add member');
      toast.success(data.message);
      onTeamUpdate(); 
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (userId) => {
    setLoading(true);
    try {
      const response = await fetchWithToken(
        `/projects/${project.id}/members/${userId}`,
        { method: 'DELETE' }
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to remove member');
      toast.success(data.message);
      onTeamUpdate(); 
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveClick = (member) => {
    setMemberToRemove(member);
    setIsConfirmModalOpen(true);
  };

  const handleConfirmRemove = () => {
    if (memberToRemove) {
      handleRemoveMember(memberToRemove.id);
    }
    setIsConfirmModalOpen(false);
    setMemberToRemove(null);
  };

  if (!isOpen && !isAnimatingOut) return null;

  const modalClass = isAnimatingOut ? 'animating-out' : '';

  return (
    <div className={`modal-overlay ${modalClass}`} onClick={handleClose}>
        <ConfirmationModal
            isOpen={isConfirmModalOpen}
            onClose={() => setIsConfirmModalOpen(false)}
            onConfirm={handleConfirmRemove}
            title={`Remove ${memberToRemove?.email}?`}
            message="This will revoke their access to the project. They can be added back later by the project owner."
        />
      
      {/* Used 'detail-modal-content' class for consistent sizing/animation */}
      <div 
        className={`modal-content detail-modal-content ${modalClass}`} 
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '500px', height: 'auto', maxHeight: '85vh' }} 
      >
        <div className="detail-modal-header">
           <h2>Manage Team for "{project.name}"</h2>
           <button onClick={handleClose} className="detail-modal-close-btn" title="Close">
              <X size={24} />
           </button>
        </div>

        <div className="detail-modal-body">
            <div className="search-input-container">
              <Search size={18} className="search-input-icon" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by email to add user..."
                className="text-input"
              />
              {searchResults.length > 0 && (
                <div className="search-results-list">
                  {searchResults.map((user) => (
                    <div key={user.id} onClick={() => handleAddMember(user.email)} className="search-result-item">
                      {user.email}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <h4 style={{marginTop: '1.5rem'}}>Current Team</h4>
            <div className="team-list">
              <div className="team-list-item">
                <div className="team-member-info">
                  <UserCheck size={16} />
                  <span>{project.owner_email}</span>
                  <span className="role-tag owner">Owner</span>
                </div>
              </div>
              {project.members.map((member) => (
                <div key={member.id} className="team-list-item">
                  <div className="team-member-info">
                    <span>{member.email}</span>
                  </div>
                  <button onClick={() => handleRemoveClick(member)} disabled={loading} title={`Remove ${member.email}`} className="action-btn">
                    <Trash2 color="#ff3b3b" size={18} />
                  </button>
                </div>
              ))}
            </div>
        </div>
      </div>
    </div>
  );
};

const getInitials = (email) => {
    if (!email) return 'U';
    const emailParts = email.split('@')[0];
    const names = emailParts.split('.');
    if (names.length > 1 && names[0][0] && names[1][0]) { return (names[0][0] + names[1][0]).toUpperCase(); }
    else if (emailParts.length > 1) { return (emailParts[0] + emailParts[1]).toUpperCase(); }
    else if (emailParts.length > 0) { return emailParts[0].toUpperCase(); }
    return 'U';
};


// ===================== ProjectDashboard =====================
const ProjectDashboard = () => {
  const { projectId } = useParams();
  const { projects, isInitialLoad, loading, fetchProjects } = useContext(ProjectContext);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentUserEmail, setCurrentUserEmail] = useState('');

  const project = projects[projectId];

  useEffect(() => {
    try {
        const token = localStorage.getItem('jwtToken');
        if (token) {
            const decoded = jwtDecode(token);
            setCurrentUserEmail(decoded.email);
        }
    } catch (e) {
        console.error("Failed to decode token", e);
    }
  }, []);

  useEffect(() => {
    if (Object.keys(projects).length === 0) {
      fetchProjects();
    }
  }, [projects, fetchProjects]);

  const isOwner = project && currentUserEmail === project.owner_email;

  if (isInitialLoad || loading || !project) {
    return <div className="global-loader"><div className="loader"></div></div>;
  }

  if (!project) {
    return (
      <div className="page-wrapper">
        <h1 style={{textAlign: 'center'}}>Project Not Found</h1>
        <Link to="/">&larr; Back to All Projects</Link>
      </div>
    );
  }
  
  const navCards = [
      { title: 'Documents Analyzer', icon: FileText, desc: `${project.documents.length} document(s)`, link: 'documents', className: 'documents' },
      { title: 'Transcript Analyzer', icon: Mic, desc: `${project.transcripts.length} transcript(s)`, link: 'transcripts', className: 'transcripts' },
      { title: 'Agent Workspace', icon: Bot, desc: 'Collaborate and build the final document', link: 'workspace', className: 'workspace' },
  ];

  return (
    <div className="page-wrapper"> 
      {isModalOpen && (
        <ManageTeamModal
            project={project}
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onTeamUpdate={fetchProjects}
        />
      )}

      <div style={{ marginBottom: '1rem' }}> 
        <Breadcrumbs />
        
        <div style={{ textAlign: 'center', marginTop: '-10px' }}>
            <h1 style={{ fontSize: '3rem', margin: 0, fontWeight: 800 }}>
            {project.name}
            </h1>
            <p style={{color: '#888', fontSize: '1.1rem', marginTop: '0', marginBottom: '5px'}}>
                Project Dashboard
            </p>
        </div>
      </div>

      <div className="section-content" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Users size={24} /> Team
          </h2>
          {isOwner && (
            <button onClick={() => setIsModalOpen(true)} className="btn-secondary">
              <UserPlus size={16} style={{ marginRight: '5px' }} /> Manage Team
            </button>
          )}
        </div>
        
        <div className="dashboard-team-list">
            <div className="dashboard-team-item">
                <div className="team-item-avatar owner-avatar">
                    {getInitials(project.owner_email)}
                </div>
                <div className="team-item-info">
                    <strong>{project.owner_email.split('@')[0]}</strong>
                    <p>{project.owner_email}</p>
                </div>
                <div className="team-item-role owner-role">
                    <UserCheck size={14} />
                    <span>Owner</span>
                </div>
            </div>

            {project.members.map((member) => (
                <div key={member.id} className="dashboard-team-item">
                    <div className="team-item-avatar">
                        {getInitials(member.email)}
                    </div>
                    <div className="team-item-info">
                        <strong>{member.email.split('@')[0]}</strong>
                        <p>{member.email}</p>
                    </div>
                    <div className="team-item-role">
                        <span>Member</span>
                    </div>
                </div>
            ))}
        </div>

      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        {navCards.map((card, index) => (
          <Link
            to={`/projects/${projectId}/${card.link}`}
            key={card.title}
            className={`dashboard-card ${card.className}`}
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="dashboard-card-icon">
                <card.icon size={28} /> 
            </div>
            <h2 style={{ marginTop: '1rem', fontSize: '1.5rem' }}>{card.title}</h2>
            <p style={{ color: '#888', marginBottom: 0 }}>{card.desc}</p>
            <div className="dashboard-card-arrow">
                <ChevronRight size={20} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default ProjectDashboard;