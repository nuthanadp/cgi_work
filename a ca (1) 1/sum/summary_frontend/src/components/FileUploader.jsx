import React, { useState, useCallback } from 'react';
import { UploadCloud } from 'lucide-react';
import "./../styles/theme.css";

const FileUploader = ({ onUpload, acceptedFileTypes, title, supportedText }) => {
    const [isActive, setIsActive] = useState(false);

    // Handles drag events
    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setIsActive(true);
        } else if (e.type === "dragleave") {
            setIsActive(false);
        }
    };

    // Handles dropped files
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onUpload(Array.from(e.dataTransfer.files));
        }
    }, [onUpload]);

    // Handles file selection via click
    const handleFileChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files.length > 0) {
            onUpload(Array.from(e.target.files));
        }
    };

    // Create a unique ID for the input to avoid conflicts
    const inputId = `file-input-${title.replace(/\s+/g, '-').toLowerCase()}`;

    return (
        <form
            className={`file-drop-zone ${isActive ? 'is-active' : ''}`}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById(inputId).click()}
        >
            <input
                type="file"
                id={inputId}
                multiple
                onChange={handleFileChange}
                accept={acceptedFileTypes}
                style={{ display: 'none' }}
            />
            <UploadCloud size={40} opacity={0.8} />
            <h4>{title}</h4>
            <p>or click to select files</p>
            <p style={{ fontSize: '12px', marginTop: '15px' }}>{supportedText}</p>
        </form>
    );
};

export default FileUploader;