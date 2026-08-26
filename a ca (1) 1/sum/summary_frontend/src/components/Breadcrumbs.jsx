import React, { useContext } from 'react';
import { Link, useParams, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { ProjectContext } from '../context/ProjectContext';
import '../styles/theme.css'; // We will add styles to theme.css

const Breadcrumbs = () => {
    const location = useLocation();
    const params = useParams();
    const { projects } = useContext(ProjectContext);

    const paths = location.pathname.split('/').filter(p => p);
    
    let currentLink = '';
    const crumbs = paths.map((crumb, index) => {
        currentLink += `/${crumb}`;
        let crumbText = crumb.charAt(0).toUpperCase() + crumb.slice(1);

        // --- Smart text replacement ---
        if (crumb === 'projects' && params.projectId) {
            // This is the "Projects" link, but we are on a specific project page
            // We'll skip this one and let the next crumb handle it.
            return null; 
        }
        if (params.projectId && crumb === params.projectId) {
            const project = projects[params.projectId];
            crumbText = project ? `Project: ${project.name}` : 'Project';
        }

        const isLast = index === paths.length - 1;

        return (
            <React.Fragment key={crumb}>
                <ChevronRight size={16} className="breadcrumb-separator" />
                {isLast ? (
                    <span className="breadcrumb-item active">{crumbText}</span>
                ) : (
                    <Link to={currentLink} className="breadcrumb-item">
                        {crumbText}
                    </Link>
                )}
            </React.Fragment>
        );
    });

    return (
        <nav className="breadcrumb-nav">
            <Link to="/" className="breadcrumb-item home">
                <Home size={16} />
                <span>Home</span>
            </Link>
            {crumbs}
        </nav>
    );
};

export default Breadcrumbs;