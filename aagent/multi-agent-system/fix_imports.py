#!/usr/bin/env python3
"""
修复项目中的导入路径问题
"""
import os
import re

def fix_imports_in_file(file_path):
    """修复单个文件的导入路径"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 添加sys.path修复
    if 'import sys' not in content and 'from ' in content:
        # 找到第一个导入语句的位置
        import_match = re.search(r'^(from|import)\s', content, re.MULTILINE)
        if import_match:
            insert_pos = import_match.start()
            
            # 计算需要向上多少级目录
            rel_path = os.path.relpath(file_path, 'backend')
            levels = len(rel_path.split(os.sep)) - 1
            
            sys_path_fix = """import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(""" + "os.path.dirname(" * levels + "os.path.abspath(__file__)" + ")" * levels + """))

"""
            
            content = content[:insert_pos] + sys_path_fix + content[insert_pos:]
    
    # 修复相对导入为绝对导入
    replacements = [
        (r'from \.\.config', 'from config'),
        (r'from \.\.models', 'from models'),
        (r'from \.\.core', 'from core'),
        (r'from \.config', 'from config'),
        (r'from \.models', 'from models'),
        (r'from \.core', 'from core'),
        (r'from \.', 'from core.'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # 只有在内容改变时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fixed imports in: {file_path}")
        return True
    return False


def fix_all_imports():
    """修复所有Python文件的导入"""
    print("Fixing import paths in all Python files...")
    
    backend_dir = 'backend'
    fixed_count = 0
    
    for root, dirs, files in os.walk(backend_dir):
        # 跳过__pycache__和venv目录
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'venv', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    
    print(f"\n✓ Fixed {fixed_count} files")


def create_init_files():
    """创建缺失的__init__.py文件"""
    print("\nCreating missing __init__.py files...")
    
    directories = [
        'backend/core',
        'backend/core/agents',
        'backend/core/workflow',
        'backend/models',
        'backend/api',
        'backend/api/routes',
        'backend/services',
        'backend/utils',
        'backend/tools'
    ]
    
    created_count = 0
    for directory in directories:
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            os.makedirs(directory, exist_ok=True)
            with open(init_file, 'w') as f:
                f.write('# Package initialization\n')
            print(f"✓ Created: {init_file}")
            created_count += 1
    
    print(f"\n✓ Created {created_count} __init__.py files")


if __name__ == "__main__":
    # 确保在正确的目录运行
    if not os.path.exists('backend'):
        print("Error: Please run this script from the multi-agent-system directory")
        exit(1)
    
    fix_all_imports()
    create_init_files()
    
    print("\n✅ Import fixes completed!")