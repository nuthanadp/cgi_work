import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';

// FIX: Use Named Imports to prevent "does not provide export named default" error
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableCell } from '@tiptap/extension-table-cell';
import { TableHeader } from '@tiptap/extension-table-header';

import { Markdown } from 'tiptap-markdown'; 
import { 
    Bold, Italic, List, ListOrdered, 
    Heading1, Heading2, Heading3, 
    Quote, Undo, Redo, Table as TableIcon 
} from 'lucide-react';
import '../styles/theme.css';

const MenuBar = ({ editor }) => {
    if (!editor) return null;

    const isActive = (type, opts) => editor.isActive(type, opts) ? 'is-active' : '';

    return (
        <div className="editor-toolbar">
            <button onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} className={isActive('heading', { level: 1 })} title="Heading 1">
                <Heading1 size={18} />
            </button>
            <button onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} className={isActive('heading', { level: 2 })} title="Heading 2">
                <Heading2 size={18} />
            </button>
            <button onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} className={isActive('heading', { level: 3 })} title="Heading 3">
                <Heading3 size={18} />
            </button>
            <div className="divider" />
            <button onClick={() => editor.chain().focus().toggleBold().run()} className={isActive('bold')} title="Bold">
                <Bold size={18} />
            </button>
            <button onClick={() => editor.chain().focus().toggleItalic().run()} className={isActive('italic')} title="Italic">
                <Italic size={18} />
            </button>
            <div className="divider" />
            <button onClick={() => editor.chain().focus().toggleBulletList().run()} className={isActive('bulletList')} title="Bullet List">
                <List size={18} />
            </button>
            <button onClick={() => editor.chain().focus().toggleOrderedList().run()} className={isActive('orderedList')} title="Numbered List">
                <ListOrdered size={18} />
            </button>
            <button onClick={() => editor.chain().focus().toggleBlockquote().run()} className={isActive('blockquote')} title="Quote">
                <Quote size={18} />
            </button>
             <div className="divider" />
            {/* Table Button */}
            <button 
                onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()} 
                title="Insert Table"
            >
                <TableIcon size={18} />
            </button>
            <div className="divider" />
            <button onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()} title="Undo">
                <Undo size={18} />
            </button>
            <button onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()} title="Redo">
                <Redo size={18} />
            </button>
        </div>
    );
};

const RichTextEditor = ({ content, onChange, editable = true }) => {
    const editor = useEditor({
        extensions: [
            StarterKit,
            Link.configure({ openOnClick: false }),
            Image.configure({ inline: true }),
            // Table Extensions must be registered here
            Table.configure({ resizable: true }),
            TableRow,
            TableHeader,
            TableCell,
            Markdown.configure({
                html: true,                  
                transformPastedText: true,
                transformCopiedText: true,
            })
        ],
        content: content,
        editable: editable,
        editorProps: {
            attributes: {
                class: 'prose focus:outline-none', 
            },
        },
        onUpdate: ({ editor }) => {
            const markdownOutput = editor.storage.markdown.getMarkdown();
            onChange(markdownOutput);
        },
    });

    // --- CRITICAL FIX FOR LOOP ---
    useEffect(() => {
        if (editor && content !== editor.storage.markdown.getMarkdown()) {
            // The 'false' argument prevents the 'onUpdate' event from firing
            // This stops the infinite loop where saving triggers a new "edit"
            editor.commands.setContent(content, false);
        }
    }, [content, editor]);

    // Handle Editable Toggle
    useEffect(() => {
        if (editor) {
            editor.setEditable(editable);
        }
    }, [editable, editor]);

    return (
        <div className={`rich-text-editor-container ${editable ? 'edit-mode' : 'read-mode'}`}>
            {/* INJECTED STYLES FOR CLASSIC LOOK */}
            <style>{`
                /* 1. Smaller, sharper font matching original video */
                .ProseMirror {
                    font-size: 0.9rem !important; 
                    line-height: 1.5 !important;
                    color: #222;
                }
                
                .ProseMirror p { margin-bottom: 0.75em; }

                /* 2. TABLE STYLING - Restoring Borders & Headers */
                .ProseMirror table {
                    border-collapse: collapse;
                    margin: 1rem 0;
                    width: 100%;
                    table-layout: fixed;
                    font-size: 0.85rem;
                }
                
                .ProseMirror td, 
                .ProseMirror th {
                    border: 1px solid #c0c0c0 !important; /* Force visible border */
                    padding: 6px 10px;
                    vertical-align: top;
                    box-sizing: border-box;
                    position: relative;
                }
                
                .ProseMirror th {
                    background-color: #f0f0f0 !important; /* Grey header background */
                    font-weight: 700;
                    text-align: left;
                }

                /* 3. Image Styling */
                .ProseMirror img {
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin: 10px auto;
                    display: block;
                }
                
                /* 4. Headings */
                .ProseMirror h1 { font-size: 1.7em; font-weight: 700; margin-top: 1em; color: #111; }
                .ProseMirror h2 { font-size: 1.3em; font-weight: 600; margin-top: 1em; padding-bottom: 5px; border-bottom: 1px solid #eee; }
                .ProseMirror h3 { font-size: 1.1em; font-weight: 600; margin-top: 1em; }
            `}</style>

            {editable && <MenuBar editor={editor} />}
            <div className="editor-content-scroll">
                <EditorContent editor={editor} />
            </div>
        </div>
    );
};

export default RichTextEditor;