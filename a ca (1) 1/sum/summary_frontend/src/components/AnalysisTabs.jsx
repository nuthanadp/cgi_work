import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { List, LayoutGrid } from 'lucide-react';
import CategorizedDisplay from './CategorizedDisplay'; 

const AnalysisTabs = ({ analysisResult }) => {
    // --- 1. ADD STATE for active tab ---
    const [activeTab, setActiveTab] = useState('extracted');
    const noExtractedDataMessage = "No extracted requirements found.";

    return (
        <div className="analysis-tabs-container">
            {/* --- 2. UPDATE tab buttons to use state --- */}
            <div className="tab-nav">
                <button
                    onClick={() => setActiveTab('extracted')}
                    className={`tab-btn ${activeTab === 'extracted' ? 'active' : ''}`}
                >
                    <List size={16} /> Extracted
                </button>
                <button
                    onClick={() => setActiveTab('categorized')}
                    className={`tab-btn ${activeTab === 'categorized' ? 'active' : ''}`}
                >
                    <LayoutGrid size={16} /> Categorized
                </button>
            </div>

            {/* --- 3. WRAP content in an animated container --- */}
            {/* We use the same CSS classes as AgentWorkspace for consistency */}
            <div className={`tab-content-container active-tab-${activeTab}`}>
                
                {/* --- Panel 1: Extracted --- */}
                <div className="tab-panel" id="extracted-panel">
                    <div className="scroll-box" style={{ maxHeight: '400px', margin: 0, padding: '15px' }}>
                        <div className="markdown-content">
                            <ReactMarkdown>
                                {analysisResult?.extracted_content || noExtractedDataMessage}
                            </ReactMarkdown>
                        </div>
                    </div>
                </div>

                {/* --- Panel 2: Categorized --- */}
                <div className="tab-panel" id="categorized-panel">
                     <div className="scroll-box" style={{ maxHeight: '400px', margin: 0, padding: '15px' }}>
                        <CategorizedDisplay data={analysisResult?.categorized_json} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalysisTabs;