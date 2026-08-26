import React from 'react';

const CategorizedDisplay = ({ data }) => {
    // If there's no data or the data is not an object, show a message.
    if (!data || typeof data !== 'object') {
        return <p>No categorized data available.</p>;
    }

    // Get the keys from the data object (e.g., "Functional", "NonFunctional", "Constraints")
    const categories = Object.keys(data);

    // If there are no categories or all categories are empty, show a message.
    const isEmpty = categories.every(cat => !data[cat] || data[cat].length === 0);
    if (isEmpty) {
        return <p>No requirements were categorized.</p>;
    }

    return (
        <div className="categorized-display">
            {categories.map(category => {
                const requirements = data[category];
                // Skip non-array fields (like Note fields from spike stories)
                if (!Array.isArray(requirements)) {
                    return null;
                }
                // Only render the section if there are requirements in it
                if (requirements && requirements.length > 0) {
                    return (
                        <div key={category} style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{ marginTop: 0, marginBottom: '0.5rem', borderBottom: '1px solid var(--scroll-hover)', paddingBottom: '0.5rem' }}>
                                {category.replace(/([A-Z])/g, ' $1').trim()} {/* Adds space before uppercase letters */}
                            </h4>
                            <ul style={{ margin: 0, paddingLeft: '20px' }}>
                                {requirements.map((req, index) => (
                                    <li key={index} style={{ marginBottom: '0.5rem' }}>
                                        {req.requirement ? `${req.requirement} (${req.speaker || 'Unknown'})` : req}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    );
                }
                return null; // Don't render anything for empty categories
            })}
        </div>
    );
};

export default CategorizedDisplay;