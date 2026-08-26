import React from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import "../styles/theme.css";

// --- CONFIG ---
const BACKEND_URL = "http://127.0.0.1:5000"; 

const Preview = ({ text, pdfUrl }) => {

  if (pdfUrl) {
      return (
          <div className="scroll-box" style={{ padding: 0, height: '100%', minHeight: '500px' }}>
              <iframe 
                  src={pdfUrl} 
                  title="Document PDF Preview"
                  width="100%" 
                  height="100%" 
                  style={{ border: 'none', display: 'block' }}
              >
                  <p style={{ padding: '2rem', textAlign: 'center' }}>
                      Your browser does not support inline PDFs. 
                      <a href={pdfUrl} target="_blank" rel="noopener noreferrer">Download the PDF</a>.
                  </p>
              </iframe>
          </div>
      );
  }

  if (!text) return <div className="scroll-box">No content available.</div>;

  return (
    <div className="scroll-box">
      <div className="markdown-content">
        <ReactMarkdown 
            remarkPlugins={[remarkGfm]} 
            rehypePlugins={[rehypeRaw]} // 🟢 Enable HTML tables/images
            components={{
                img: ({node, ...props}) => {
                    let src = props.src;
                    if (src && src.startsWith('/static')) {
                        src = `${BACKEND_URL}${src}`;
                    }
                    return (
                        <img 
                            {...props} 
                            src={src}
                            style={{maxWidth: '100%', height: 'auto', borderRadius: '4px', border: '1px solid #ddd'}} 
                            alt={props.alt || 'Document Image'}
                        />
                    );
                }
            }}
        >
            {text}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default Preview;