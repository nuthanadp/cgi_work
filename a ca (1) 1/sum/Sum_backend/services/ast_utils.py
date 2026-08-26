import uuid
import copy

def generate_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def create_ast_document(title="Untitled Document"):
    return {
        "id": generate_id("doc"),
        "title": title,
        "sections": [],
        "meta": {
            "type": "document",
            "version": 1,
            "format": "AST-H2",
            "numbering": "N2",
        }
    }

def add_ast_section(ast, number="", title=""):
    section = {
        "id": generate_id("sec"),
        "number": number,
        "title": title,
        "level": number.count(".") + 1 if number else 1,
        "content": [],
        "meta": {
            "type": "section"
        }
    }
    ast["sections"].append(section)
    return section

def add_ast_paragraph(ast, section, text):
    if not text.strip():
        return
    node = {
        "id": generate_id("p"),
        "type": "paragraph",
        "text": text,
    }
    section["content"].append(node)
    return node

def add_ast_table(ast, section, headers, rows=None):
    node = {
        "id": generate_id("tbl"),
        "type": "table",
        "headers": headers,
        "rows": rows or [],
        "meta": {
            "type": "table"
        }
    }
    section["content"].append(node)
    return node

def add_ast_image(ast, section, src, caption=""):
    node = {
        "id": generate_id("img"),
        "type": "image",
        "src": src,
        "caption": caption,
        "meta": {"type": "image"}
    }
    section["content"].append(node)
    return node

def finalize_ast(ast):
    # Normalize empty sections
    ast["sections"] = [s for s in ast["sections"] if s["content"]]
    return ast


# ============================
# AST Patch & Merge Utilities
# ============================

def apply_patch(ast, patch):
    """
    Generic patch structure:
    {
        "op": "update",
        "target": node_id,
        "path": ["rows", 2, 1],
        "value": "High Priority"
    }
    """
    op = patch.get("op")
    node_id = patch.get("target")
    path = patch.get("path", [])
    value = patch.get("value")

    node = find_node(ast, node_id)
    if not node:
        return ast

    if op == "replace":
        set_path(node, path, value)
    elif op == "insert":
        insert_path(node, path, value)
    elif op == "delete":
        delete_path(node, path)

    return ast


def find_node(ast, node_id):
    if ast.get("id") == node_id:
        return ast
    for section in ast.get("sections", []):
        if section.get("id") == node_id:
            return section
        for n in section.get("content", []):
            if n.get("id") == node_id:
                return n
    return None


def set_path(node, path, value):
    ref = node
    for p in path[:-1]:
        ref = ref[p]
    ref[path[-1]] = value


def insert_path(node, path, value):
    ref = node
    for p in path[:-1]:
        ref = ref[p]
    ref[path[-1]].append(value)


def delete_path(node, path):
    ref = node
    for p in path[:-1]:
        ref = ref[p]
    del ref[path[-1]]


# ================
# Serialization
# ================

def serialize_ast(ast):
    """Safe JSON serialization for frontend"""
    return copy.deepcopy(ast)
