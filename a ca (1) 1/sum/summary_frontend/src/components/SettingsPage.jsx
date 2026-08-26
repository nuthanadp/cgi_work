import React, { useState, useEffect, useContext, useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import { 
    AlertTriangle, 
    User, 
    Lock, 
    Save, 
    Database, 
    Package, 
    FileText, 
    Mic,
    DatabaseZap,
    Check,
    Trash2,
    Plus,
    Key,
    Shield,
    Edit2,
    Cpu,
    Zap,
    Brain,
    Cloud,
    X 
} from 'lucide-react';
import ConfirmationModal from './ConfirmationModal';
import { fetchWithToken } from '../api';
import toast from 'react-hot-toast';
import { ProjectContext } from '../context/ProjectContext';
import Breadcrumbs from './Breadcrumbs';

// --- NEW CHART COMPONENT IMPORT ---
import TokenUsageCharts from './TokenUsageCharts';

// --- CHART IMPORTS (Removed ChartJS imports as they are now in TokenUsageCharts) ---
// --- TokenLineChart Component (REMOVED: Now replaced by TokenUsageCharts) ---


// --- Edit Model Modal Component (unchanged) ---
const EditModelModal = ({ model, isOpen, onClose, onSave }) => {
    const [modelName, setModelName] = useState(model?.model_name || '');
    const [apiKey, setApiKey] = useState(''); 
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (model) {
            setModelName(model.model_name);
            setApiKey(''); 
        }
    }, [model]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        
        const updateData = { model_name: modelName };
        if (apiKey.trim()) {
            updateData.api_key = apiKey.trim();
        }

        await onSave(model.id, updateData);
        setIsLoading(false);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" style={{ maxWidth: '500px' }} onClick={(e) => e.stopPropagation()}>
                <button onClick={onClose} className="modal-close-btn" title="Close"><X size={20} /></button>
                <h2 style={{ marginTop: 0 }}>Edit Model</h2>
                <p style={{ color: '#888' }}>Editing: <strong>{model.provider} / {model.model_name}</strong></p>

                <form onSubmit={handleSubmit}>
                    <div className="form-input-group" style={{gap: '1rem'}}>
                        <div>
                            <label htmlFor="edit-model-name">Model Name</label>
                            <input
                                id="edit-model-name"
                                type="text"
                                value={modelName}
                                onChange={(e) => setModelName(e.target.value)}
                                className="text-input"
                                required
                            />
                        </div>
                        <div>
                            <label htmlFor="edit-api-key">New API Key</label>
                             <input
                                id="edit-api-key"
                                type="password"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Leave blank to keep existing key"
                                className="text-input"
                            />
                        </div>
                    </div>
                    <div className="confirm-actions" style={{borderTop: 'none', paddingTop: '1.5rem', paddingBottom: 0}}>
                        <button type="button" className="btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="btn-primary" disabled={isLoading}>
                            <Save size={16} style={{ marginRight: '8px' }}/>
                            {isLoading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};


const SettingsPage = ({ onLogout }) => {
    // --- State ---
    const [activeView, setActiveView] = useState('profile'); 
    const [isModalOpen, setIsModalOpen] = useState(false);
    
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [username, setUsername] = useState('');
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    // Token states are now managed within TokenUsageCharts, 
    // but we keep the profile fetch logic here.
    const [totalTokens, setTotalTokens] = useState(0); 
    const [isUsageLoading, setIsUsageLoading] = useState(false); // Only for initial Project Summary

    const [adminModels, setAdminModels] = useState([]);
    const [adminLoading, setAdminLoading] = useState(false);
    const [newProvider, setNewProvider] = useState("Google");
    const [newModelName, setNewModelName] = useState("");
    const [newApiKey, setNewApiKey] = useState("");
    const [newApiBase, setNewApiBase] = useState(""); // For Azure endpoint
    const [otherProviderName, setOtherProviderName] = useState("");

    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [modelToEdit, setModelToEdit] = useState(null);
    
    const { projects } = useContext(ProjectContext);

    // --- UPDATED FETCH USAGE (Kept simple for Project Summary) ---
    // This only fetches the total tokens for the Project Summary grid.
    const fetchSummaryUsage = useCallback(async () => {
        setIsUsageLoading(true); 
        try {
            const response = await fetchWithToken('/profile/usage');
            const data = await response.json();
            if (response.ok) {
                setTotalTokens(data.total_tokens || 0);
            } else {
                throw new Error(data.error || 'Failed to fetch usage.');
            }
        } catch (error) {
            console.error(error.message);
        } finally {
            setIsUsageLoading(false); 
        }
    }, []); 

    useEffect(() => {
        const fetchProfile = async () => {
            setLoading(true);
            try {
                const response = await fetchWithToken('/profile');
                const data = await response.json();
                if (response.ok) {
                    setUser(data);
                    setUsername(data.username || '');
                } else { throw new Error(data.error || 'Failed to fetch profile.'); }
            } catch (error) { toast.error(error.message); }
            finally { setLoading(false); }
        };

        fetchProfile();
        
    }, []); 

    const fetchAdminModels = useCallback(async () => {
        if (!user?.is_admin) return; 
        setAdminLoading(true);
        try {
            const response = await fetchWithToken('/api/admin/models'); 
            const data = await response.json();
            if (response.ok) {
                setAdminModels(data);
            } else {
                throw new Error(data.error || 'Failed to fetch models');
            }
        } catch (error) {
            toast.error(error.message);
        } finally {
            setAdminLoading(false);
        }
    }, [user]);

    useEffect(() => {
        // Fetch summary data immediately on mount or when user changes
        fetchSummaryUsage(); 
        
        if (activeView === 'admin' && user?.is_admin) {
            fetchAdminModels();
        }
    }, [activeView, user, fetchAdminModels, fetchSummaryUsage]);


    const handleAddModel = async (e) => {
        e.preventDefault();
        
        const providerToSend = newProvider === "Other" ? otherProviderName.trim() : newProvider;

        if (!providerToSend) {
            toast.error("Please select or enter a provider name.");
            return;
        }

        setAdminLoading(true);
        try {
            const response = await fetchWithToken('/api/admin/models', {
                method: 'POST',
                body: JSON.stringify({
                    provider: providerToSend,
                    model_name: newModelName,
                    api_key: newApiKey,
                    api_base: newApiBase || null  // Send Azure endpoint or null
                })
            });
            const data = await response.json();
            if (response.ok) {
                toast.success(`Model "${data.model_name}" added!`);
                setNewProvider("Google");
                setNewModelName("");
                setNewApiKey("");
                setNewApiBase("");  // Reset api_base field
                setOtherProviderName(""); 
                fetchAdminModels(); 
            } else {
                throw new Error(data.error || 'Failed to add model');
            }
        } catch (error) {
            toast.error(error.message);
        } finally {
            setAdminLoading(false);
        }
    };

    const handleUpdateModel = async (modelId, updateData) => {
        setAdminLoading(true);
        try {
            const response = await fetchWithToken(`/api/admin/models/${modelId}`, {
                method: 'PUT',
                body: JSON.stringify(updateData)
            });
            const data = await response.json();
            if (response.ok) {
                toast.success(`Model "${data.model_name}" updated!`);
                fetchAdminModels(); 
            } else {
                throw new Error(data.error || 'Failed to update model');
            }
        } catch (error) {
            toast.error(error.message);
        } finally {
            setAdminLoading(false);
        }
    };

    const handleDeleteModel = async (modelId) => {
        setAdminLoading(true);
        try {
            const response = await fetchWithToken(`/api/admin/models/${modelId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            if (response.ok) {
                toast.success(data.message || 'Model deleted!');
                fetchAdminModels();
            } else {
                throw new Error(data.error || 'Failed to delete model');
            }
        } catch (error) {
            toast.error(error.message);
        } finally {
            setAdminLoading(false);
        }
    };

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await fetchWithToken('/profile', { method: 'PUT', body: JSON.stringify({ username }) });
            const data = await response.json();
            if (response.ok) {
                toast.success('Profile updated successfully!');
                setUser(data.user);
            } else { throw new Error(data.error || 'Failed to update profile.'); }
        } catch (error) { toast.error(error.message); }
        finally { setLoading(false); }
    };

    const handleUpdatePassword = async (e) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) return toast.error("New passwords do not match.");
        setLoading(true);
        try {
            const response = await fetchWithToken('/profile', { method: 'PUT', body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) });
            const data = await response.json();
            if (response.ok) {
                toast.success('Password updated successfully!');
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
            } else { throw new Error(data.error || 'Failed to update password.'); }
        } catch (error) { toast.error(error.message); }
            finally { setLoading(false); }
    };
    
    const handleDeleteAccount = async () => {
        setLoading(true);
        setIsModalOpen(false);
        const toastId = toast.loading('Deleting account...');

        try {
            const response = await fetchWithToken('/profile', { method: 'DELETE' });
            const data = await response.json();
            if (response.ok) {
                toast.success('Account deleted successfully.', { id: toastId });
                onLogout();
            } else {
                throw new Error(data.error || 'Failed to delete account.');
            }
        } catch (error) {
            toast.error(error.message, { id: toastId });
            setLoading(false);
        }
    };

    // --- Render Functions ---

    const SettingsMenu = () => (
        <div className="settings-nav-menu">
            <button 
                className={`settings-nav-item ${activeView === 'profile' ? 'active' : ''}`}
                onClick={() => setActiveView('profile')}
            >
                <User size={16} /> Profile
            </button>
            <button 
                className={`settings-nav-item ${activeView === 'password' ? 'active' : ''}`}
                onClick={() => setActiveView('password')}
            >
                <Lock size={16} /> Password
            </button>
            <button 
                className={`settings-nav-item ${activeView === 'usage' ? 'active' : ''}`}
                onClick={() => setActiveView('usage')}
            >
                <Database size={16} /> Usage & Statistics
            </button>
            
            {user && user.is_admin && (
                <button 
                    className={`settings-nav-item ${activeView === 'admin' ? 'active' : ''}`}
                    onClick={() => setActiveView('admin')}
                >
                    <DatabaseZap size={16} /> Admin Panel
                </button>
            )}
            
            <button 
                className={`settings-nav-item danger ${activeView === 'danger' ? 'active' : ''}`}
                onClick={() => setActiveView('danger')}
            >
                <AlertTriangle size={16} /> Danger Zone
            </button>
        </div>
    );

    const renderUsageStats = () => {
        const projectList = Object.values(projects);
        const totalProjects = projectList.length;
        const totalDocuments = projectList.reduce((acc, p) => acc + p.documents.length, 0);
        const totalTranscripts = projectList.reduce((acc, p) => acc + p.transcripts.length, 0);
        
        // Use the totalTokens state from the fetched usage data
        const displayTokenCount = isUsageLoading ? '...' : totalTokens.toLocaleString();

        let accountCreated = "Loading...";
        if (user && user.created_at) {
            accountCreated = new Date(user.created_at).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } else if (!loading) {
            accountCreated = "N/A";
        }

        return (
            <>
                {/* --- Section 1: Project Summary & All-Time Total --- */}
                <div className="section-content" style={{padding: '2rem 2rem 1.5rem 2rem'}}>
                    <div className="form-section-header">
                        <h2><Database size={22} /> Usage & Statistics</h2>
                    </div>
                    <p style={{ color: '#888', marginTop: '1rem', marginBottom: '2rem' }}>
                        An overview of your project activity and all-time token consumption.
                    </p>
                    <div className="usage-stats-grid">
                        
                        {/* Project Cards (Unchanged) */}
                        <div className="stat-card">
                            <div className="stat-card-icon" style={{ backgroundColor: 'rgba(255, 59, 59, 0.15)', color: 'var(--button-bg)' }}>
                                <Package size={24} />
                            </div>
                            <div className="stat-card-text">
                                <h3>{totalProjects}</h3>
                                <p>Total Projects</p>
                            </div>
                        </div>
                        
                        {/* Documents Analyzed (Unchanged) */}
                        <div className="stat-card">
                            <div className="stat-card-icon" style={{ backgroundColor: 'rgba(23, 162, 184, 0.15)', color: '#17a2b8' }}>
                                <FileText size={24} />
                            </div>
                            <div className="stat-card-text">
                                <h3>{totalDocuments}</h3>
                                <p>Documents Analyzed</p>
                            </div>
                        </div>
                        
                        {/* Transcripts Analyzed (Unchanged) */}
                        <div className="stat-card">
                            <div className="stat-card-icon" style={{ backgroundColor: 'rgba(40, 167, 69, 0.15)', color: '#28a745' }}>
                                <Mic size={24} />
                            </div>
                            <div className="stat-card-text">
                                <h3>{totalTranscripts}</h3>
                                <p>Transcripts Analyzed</p>
                            </div>
                        </div>
                        
                        {/* All-Time Tokens (Using general fetch for all-time number) */}
                        <div className="stat-card">
                            <div className="stat-card-icon" style={{ backgroundColor: 'rgba(108, 117, 125, 0.15)', color: '#6c757d' }}>
                                <DatabaseZap size={24} />
                            </div>
                            <div className="stat-card-text">
                                <h3>{displayTokenCount}</h3>
                                <p>All-Time Tokens Used</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* --- Section 2: Token Usage Charts and Breakdown (NEW Component) --- */}
                <div style={{marginTop: '2rem'}}>
                    {/* Pass the active state to enable/disable real-time polling */}
                    <TokenUsageCharts isActive={activeView === 'usage'} />
                </div>

                <div className="section-content" style={{ marginTop: '2rem', padding: '1.5rem 2rem', color: '#888' }}>
                    <strong style={{ fontWeight: 600, color: 'var(--text-color)' }}>Account Created On:</strong> {accountCreated}
                </div>
            </>
        );
    };

    const renderProfileForm = () => (
        <form onSubmit={handleUpdateProfile} className="section-content">
            <div className="form-section-header">
                <h2><User size={22} /> Profile Information</h2>
            </div>
            <fieldset disabled={loading} style={{ border: 'none', padding: 0, margin: 0 }}>
                <div className="form-section">
                    <div className="form-label-group">
                        <label>Email Address</label>
                        <p>Your email is fixed and cannot be changed.</p>
                    </div>
                    <div className="form-input-group">
                        <input type="email" value={user?.email || ''} disabled className="text-input" />
                    </div>
                    <div className="form-label-group">
                        <label htmlFor="username">Username</label>
                        <p>This is your public display name.</p>
                    </div>
                    <div className="form-input-group">
                        <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="e.g., john.smith" className="text-input" />
                    </div>
                </div>
            </fieldset>
            <div style={{ borderTop: '1px solid var(--scroll-hover)', marginTop: '1.5rem', paddingTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                <button type="submit" disabled={loading}>
                    <Save size={16} style={{ marginRight: '8px' }}/>
                    {loading ? 'Saving...' : 'Save Profile'}
                </button>
            </div>
        </form>
    );

    const renderPasswordForm = () => (
        <form onSubmit={handleUpdatePassword} className="section-content">
            <div className="form-section-header">
                <h2><Lock size={22} /> Change Password</h2>
            </div>
            <fieldset disabled={loading} style={{ border: 'none', padding: 0, margin: 0 }}>
                <div className="form-section">
                    <div className="form-label-group">
                        <label>Your Password</label>
                        <p>Enter your current and new passwords.</p>
                    </div>
                    <div className="form-input-group">
                        <input id="current-password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required placeholder="Current Password" className="text-input" />
                        <input id="new-password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required placeholder="New Password" className="text-input" />
                        <input id="confirm-password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required placeholder="Confirm New Password" className="text-input" />
                    </div>
                </div>
            </fieldset>
            <div style={{ borderTop: '1px solid var(--scroll-hover)', marginTop: '1.5rem', paddingTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                <button type="submit" disabled={loading}>
                    {loading ? 'Updating...' : 'Update Password'}
                </button>
            </div>
        </form>
    );
    
    
    const renderDangerZone = () => (
        <div className="section-content" style={{ borderColor: 'var(--button-bg)', border: '2px solid var(--button-bg)' }}>
            <div className="form-section-header" style={{ borderColor: 'rgba(255, 59, 59, 0.3)' }}>
                <h2 style={{ color: 'var(--button-bg)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <AlertTriangle size={22} /> Danger Zone
                </h2>
            </div>
            <p style={{ color: '#888', marginTop: '1rem' }}>
                These actions are irreversible. Please be certain before proceeding.
            </p>
            <div style={{ marginTop: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h4 style={{ margin: 0, fontSize: '1.1rem' }}>Delete This Account</h4>
                        <p style={{ color: '#888', margin: '4px 0 0 0' }}>Permanently delete your account and all associated data.</p>
                    </div>
                    <button className="btn-danger" onClick={() => setIsModalOpen(true)} disabled={loading}>
                        {loading ? 'Deleting...' : 'Delete Account'}
                    </button>
                </div>
            </div>
        </div>
    );

    const ProviderSelector = () => {
        const providers = [
            { name: "Google", icon: Cpu },
            { name: "OpenAI", icon: Brain },
            { name: "Groq", icon: Zap },
            { name: "Anthropic", icon: Brain },
            { name: "Azure", icon: Cloud },
            { name: "Other", icon: Plus },
        ];
        return (
            <div className="provider-selector-grid">
                {providers.map(p => (
                    <button
                        type="button"
                        key={p.name}
                        className={`provider-card ${newProvider === p.name ? 'active' : ''}`}
                        onClick={() => setNewProvider(p.name)}
                    >
                        <p.icon size={24} />
                        <span>{p.name}</span>
                    </button>
                ))}
            </div>
        );
    };

    const renderAdminPanel = () => (
        <div className="section-content">
            <div className="form-section-header">
                <h2><DatabaseZap size={22} /> AI Model Configuration</h2>
            </div>
            <p style={{ color: '#888', marginTop: '1rem', marginBottom: '2rem' }}>
                Add, remove, and manage the AI models available to the application. The "Active" model will be used for all AI tasks.
            </p>
            
            <form onSubmit={handleAddModel} className="admin-add-model-form">
                <h3 style={{ marginTop: 0 }}>Add New Model</h3>
                
                <div className="form-input-group" style={{marginBottom: '1rem'}}>
                    <label>Provider</label>
                    <ProviderSelector />
                </div>
                
                {newProvider === "Other" && (
                    <div className="form-input-group" style={{marginBottom: '1rem'}}>
                        <label htmlFor="other-provider-name">Custom Provider Name</label>
                        <input 
                            id="other-provider-name" 
                            type="text" 
                            value={otherProviderName} 
                            onChange={(e) => setOtherProviderName(e.target.value)} 
                            placeholder="e.g., Cohere, Mistral" 
                            className="text-input" 
                            required 
                        />
                    </div>
                )}

                <div className="admin-form-grid">
                    <div className="form-input-group">
                        <label htmlFor="model_name">Model Name</label>
                        <input 
                            id="model_name" 
                            type="text" 
                            value={newModelName} 
                            onChange={(e) => setNewModelName(e.target.value)} 
                            placeholder={newProvider === "Azure" ? "e.g., gpt-4 (deployment name)" : "e.g., gemini/gemini-2.0-flash-exp"}
                            className="text-input" 
                            required 
                        />
                    </div>
                    <div className="form-input-group">
                        <label htmlFor="api_key">API Key</label>
                        <input 
                            id="api_key" 
                            type="password" 
                            value={newApiKey} 
                            onChange={(e) => setNewApiKey(e.target.value)} 
                            placeholder="Enter the secret API key" 
                            className="text-input" 
                            required 
                        />
                    </div>
                </div>
                
                {(newProvider === "Azure" || newProvider === "Other") && (
                    <div className="form-input-group" style={{marginTop: '1rem'}}>
                        <label htmlFor="api_base">API Base URL {newProvider === "Azure" && "(Azure Endpoint)"}</label>
                        <input 
                            id="api_base" 
                            type="text" 
                            value={newApiBase} 
                            onChange={(e) => setNewApiBase(e.target.value)} 
                            placeholder={newProvider === "Azure" ? "e.g., https://agent-framework.openai.azure.com/" : "e.g., https://api.custom-provider.com/"}
                            className="text-input" 
                            required={newProvider === "Azure"}
                        />
                    </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                    <button 
                        type="submit" 
                        disabled={
                            adminLoading || 
                            !newModelName || 
                            !newApiKey ||
                            (newProvider === "Other" && !otherProviderName.trim())
                        }
                    >
                        <Plus size={16} style={{ marginRight: '8px' }}/>
                        {adminLoading ? 'Adding...' : 'Add Model'}
                    </button>
                </div>
            </form>

            <div className="admin-model-list">
                <h3 style={{ marginTop: '2rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--scroll-hover)' }}>
                    Configured Models ({adminModels.length})
                </h3>
                {adminLoading && adminModels.length === 0 && <div className="loader"></div>}
                
                {adminModels.map(model => (
                    <div key={model.id} className="admin-model-item">
                        <div className="admin-model-info">
                            <Shield size={16} style={{flexShrink: 0}} />
                            <div style={{overflow: 'hidden'}}>
                                <strong>{model.provider}</strong>
                                <p>{model.model_name}</p>
                                {model.api_base && (
                                    <p style={{fontSize: '0.85em', color: '#999', marginTop: '4px'}}>
                                        Endpoint: {model.api_base}
                                    </p>
                                )}
                            </div>
                        </div>
                        <div className="admin-model-info" style={{flexGrow: 0.5, color: '#888'}}>
                            <Key size={14} style={{marginRight: '8px'}} />
                            <span>{model.api_key_hint}</span>
                        </div>
                        <div className="admin-model-actions">
                            {model.is_active ? (
                                <span className="admin-model-badge-active">
                                    <Check size={16} style={{ marginRight: '4px' }}/>
                                    Active
                                </span>
                            ) : (
                                <button 
                                    onClick={() => handleUpdateModel(model.id, { is_active: true })} 
                                    disabled={adminLoading}
                                    className="btn-secondary"
                                    title="Set this model as active"
                                >
                                    Set Active
                                </button>
                            )}
                             <button 
                                onClick={() => {
                                    setModelToEdit(model);
                                    setIsEditModalOpen(true);
                                }} 
                                disabled={adminLoading}
                                title="Edit model"
                                className="action-btn"
                            >
                                <Edit2 size={18} />
                            </button>
                            <button 
                                onClick={() => handleDeleteModel(model.id)} 
                                disabled={adminLoading || model.is_active}
                                title={model.is_active ? "Cannot delete an active model" : "Delete model"}
                                className="action-btn"
                            >
                                <Trash2 color="#ff3b3b" size={18} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    return (
        <div className="page-wrapper" style={{ maxWidth: '1300px', margin: '0 auto', paddingBottom: '2rem' }}>
            <ConfirmationModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onConfirm={handleDeleteAccount}
                title="Delete Your Account?"
                message="This is permanent. All your projects, documents, and transcripts will be deleted. This action cannot be undone."
            />
            
            <EditModelModal
                model={modelToEdit}
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
                onSave={handleUpdateModel}
            />

            <div style={{ marginBottom: '0rem' }}>
                <Breadcrumbs />
                <h1 style={{ marginTop: '0rem' }}>Settings</h1>
            </div>

            <div className="settings-page-grid">
                <div className="settings-grid-nav">
                    <SettingsMenu />
                </div>

                <div className={`tab-content-container settings-content active-tab-${activeView}`}>
                    <div className="tab-panel" id="profile-panel">
                        {renderProfileForm()}
                    </div>
                    <div className="tab-panel" id="password-panel">
                        {renderPasswordForm()}
                    </div>
                    <div className="tab-panel" id="usage-panel">
                        {renderUsageStats()}
                    </div>
                    <div className="tab-panel" id="admin-panel">
                        {user?.is_admin && renderAdminPanel()}
                    </div>
                    <div className="tab-panel" id="danger-panel">
                        {renderDangerZone()}
                    </div>
                </div>
            </div>
            
        </div>
    );
};

export default SettingsPage;