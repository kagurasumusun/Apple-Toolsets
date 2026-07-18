import os
import ast

def extract_module_info(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except Exception:
        return None
        
    docstring = ast.get_docstring(tree)
    classes = []
    functions = []
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            c_doc = ast.get_docstring(node)
            methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
            classes.append((node.name, c_doc, methods))
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                f_doc = ast.get_docstring(node)
                functions.append((node.name, f_doc))
                
    return {
        "docstring": docstring,
        "classes": classes,
        "functions": functions
    }

def generate_docs():
    target_dir = "actool_linux/stable"
    out_dir = "wiki/7_developer_api_reference"
    os.makedirs(out_dir, exist_ok=True)
    
    index_md = "# 💻 Developer API Reference (Stable Core)\\n\\n"
    index_md += "このセクションは `Apple-actool-py` のコアコンパイラ（`actool_linux.stable`）を構成する**全ファイルの完全なリファレンス**です。各モジュールのクラス、関数、内部ロジックの詳細を解説します。\\n\\n"
    
    for filename in sorted(os.listdir(target_dir)):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue
            
        module_name = filename[:-3]
        info = extract_module_info(os.path.join(target_dir, filename))
        if not info:
            continue
            
        md = f"# Module: `{module_name}`\\n\\n"
        
        if info["docstring"]:
            md += f"## Overview\\n{info['docstring']}\\n\\n"
            
        if info["classes"]:
            md += "## Classes\\n"
            for c_name, c_doc, methods in info["classes"]:
                md += f"### `{c_name}`\\n"
                if c_doc:
                    md += f"{c_doc}\\n\\n"
                if methods:
                    md += "**Methods:**\\n"
                    for m in methods:
                        md += f"- `{m}()`\\n"
                md += "\\n"
                
        if info["functions"]:
            md += "## Public Functions\\n"
            for f_name, f_doc in info["functions"]:
                md += f"### `{f_name}()`\\n"
                if f_doc:
                    md += f"{f_doc}\\n"
                md += "\\n"
                
        with open(os.path.join(out_dir, f"{module_name}.md"), "w") as f:
            f.write(md)
            
        index_md += f"- [{module_name}]({module_name}.md): "
        if info["docstring"]:
            index_md += info["docstring"].split("\\n")[0][:80] + "..."
        index_md += "\\n"
        
    with open(os.path.join(out_dir, "INDEX.md"), "w") as f:
        f.write(index_md)

if __name__ == "__main__":
    generate_docs()
