#!/usr/bin/env python3
"""Batch migration script to convert legacy AdminLTE templates to Tailwind CSS."""
import re
import os

TEMPLATES_DIR = "/Users/buntie/Desktop/Project ETC/U-MAS/student_management_app/templates"

def migrate_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Remove AdminLTE wrapper structure
    content = re.sub(r'<!-- Main content -->\s*', '', content)
    content = re.sub(r'<section class="content">\s*<div class="container-fluid">\s*<div class="row">\s*<div class="col-(?:md-)?12">', '', content)
    content = re.sub(r'<section class="content">\s*<div class="container-fluid">\s*<div class="row">\s*<div class="col-md-12">', '', content)
    content = re.sub(r'</div>\s*</div>\s*</div>\s*</section>\s*<!-- /\.content -->', '', content)
    content = re.sub(r'</div>\s*</div>\s*</div>\s*</section>', '', content)
    
    # Remove section wrappers without content
    content = re.sub(r'<section class="content">\s*<div class="container-fluid">', '', content)
    content = content.replace('<!-- /.content -->', '')
    content = content.replace('<!-- /.card-header -->', '')
    content = content.replace('<!-- /.card-body -->', '')
    content = content.replace('<!-- /.card -->', '')
    content = content.replace('<!-- general form elements -->', '')
    content = content.replace('<!-- form start -->', '')
    
    # Card structure → Tailwind containers
    content = re.sub(r'<div class="card\s*">', '<div class="bg-surface-container-lowest rounded-2xl overflow-hidden">', content)
    content = re.sub(r'<div class="card glass">', '<div class="bg-surface-container-lowest rounded-2xl overflow-hidden">', content)
    content = re.sub(r'<div class="card ">', '<div class="bg-surface-container-lowest rounded-2xl overflow-hidden">', content)
    
    # Card headers → Tailwind headers
    content = re.sub(
        r'<div class="card-header"[^>]*>\s*<h3 class="card-title">([^<]+)</h3>\s*</div>',
        r'<div class="px-8 py-5 border-b border-outline-variant/10"><h3 class="font-headline font-bold text-on-surface text-lg">\1</h3></div>',
        content
    )
    content = re.sub(
        r'<div class="card-header"[^>]*>\s*<h3 class="card-title"[^>]*>([^<]+)</h3>',
        r'<div class="px-8 py-5 border-b border-outline-variant/10"><h3 class="font-headline font-bold text-on-surface text-lg">\1</h3>',
        content
    )
    
    # Card body → padding
    content = re.sub(r'<div class="card-body[^"]*">', '<div class="p-8 space-y-6">', content)
    
    # Card footer → form action area
    content = re.sub(r'<div class="card-footer">', '<div class="px-8 py-6 border-t border-outline-variant/20">', content)
    
    # Form controls → Tailwind inputs
    content = re.sub(
        r'<input([^>]*?)class="form-control"([^>]*?)>',
        r'<input\1class="w-full px-4 py-3 bg-surface-container-low border-none rounded-xl focus:ring-2 focus:ring-primary/20 text-on-surface font-body"\2>',
        content
    )
    content = re.sub(
        r'<select([^>]*?)class="form-control"([^>]*?)>',
        r'<select\1class="w-full px-4 py-3 bg-surface-container-low border-none rounded-xl focus:ring-2 focus:ring-primary/20 text-on-surface font-body"\2>',
        content
    )
    content = re.sub(
        r'<textarea([^>]*?)class="form-control"([^>]*?)>',
        r'<textarea\1class="w-full px-4 py-3 bg-surface-container-low border-none rounded-xl focus:ring-2 focus:ring-primary/20 text-on-surface font-body resize-y"\2>',
        content
    )
    
    # Form group → space-y-2
    content = content.replace('<div class="form-group">', '<div class="space-y-2">')
    
    # Labels
    content = re.sub(
        r'<label([^>]*)>([^<]+)</label>',
        lambda m: f'<label{m.group(1)} class="block font-label text-sm font-bold text-on-surface-variant">{m.group(2)}</label>' if 'class=' not in m.group(1) else m.group(0),
        content
    )
    
    # Buttons
    content = re.sub(
        r'<button type="submit" class="btn btn-primary btn-block">([^<]+)</button>',
        r'<button type="submit" class="w-full py-4 premium-gradient text-white font-display font-bold rounded-xl shadow-lg shadow-primary/20 active:scale-[0.98] transition-transform">\1</button>',
        content
    )
    content = re.sub(
        r'<button type="submit" class="btn btn-primary">([^<]+)</button>',
        r'<button type="submit" class="px-6 py-3 premium-gradient text-white font-label font-bold rounded-xl shadow-lg shadow-primary/20 active:scale-[0.98] transition-transform">\1</button>',
        content
    )
    
    # Links styled as buttons
    content = re.sub(
        r'<a href="([^"]+)" class="btn btn-success">Edit</a>',
        r'<a href="\1" class="px-4 py-2 rounded-lg bg-primary/10 text-primary text-xs font-label font-bold uppercase tracking-wider hover:bg-primary/20 transition-colors no-underline">Edit</a>',
        content
    )
    content = re.sub(
        r'<a href="([^"]+)" class="btn btn-danger"([^>]*)>Delete</a>',
        r'<a href="\1" class="px-4 py-2 rounded-lg bg-error/10 text-error text-xs font-label font-bold uppercase tracking-wider hover:bg-error/20 transition-colors no-underline"\2>Delete</a>',
        content
    )
    
    # Alert messages
    content = re.sub(
        r'<div class="alert alert-danger"[^>]*>',
        '<div class="px-5 py-4 rounded-2xl text-sm font-medium flex items-center gap-3 bg-error/10 text-error">',
        content
    )
    content = re.sub(
        r'<div class="alert alert-success"[^>]*>',
        '<div class="px-5 py-4 rounded-2xl text-sm font-medium flex items-center gap-3 bg-green-100 text-green-700">',
        content
    )
    content = re.sub(
        r'<div class="alert alert-warning[^"]*"[^>]*>',
        '<div class="px-5 py-4 rounded-2xl text-sm font-medium flex items-center gap-3 bg-yellow-50 text-yellow-700">',
        content
    )
    
    # Table classes
    content = re.sub(
        r'<div class="card-body table-responsive p-0">',
        '<div class="overflow-x-auto">',
        content
    )
    content = re.sub(
        r'<table class="table table-hover text-nowrap">',
        '<table class="w-full text-left border-collapse">',
        content
    )
    content = re.sub(r'<table class="table">', '<table class="w-full text-left border-collapse">', content)
    
    # FontAwesome → Material Symbols
    fa_to_ms = {
        'fa-search': 'search',
        'fa-plus': 'add',
        'fa-edit': 'edit',
        'fa-trash': 'delete',
        'fa-trash-alt': 'delete',
        'fa-save': 'save',
        'fa-user-plus': 'person_add',
        'fa-user-edit': 'edit',
        'fa-user-slash': 'person_off',
        'fa-shield-alt': 'security',
        'fa-check-circle': 'check_circle',
        'fa-exclamation-circle': 'error',
        'fa-exclamation-triangle': 'warning',
        'fa-tools': 'construction',
        'fa-upload': 'upload',
        'fa-download': 'download',
        'fa-file-upload': 'upload_file',
        'fa-bell': 'notifications',
        'fa-inbox': 'inbox',
        'fa-spinner': 'sync',
        'fa-arrow-left': 'arrow_back',
        'fa-arrow-right': 'arrow_forward',
        'fa-times': 'close',
        'fa-chart-line': 'insights',
        'fa-university': 'domain',
        'fa-user-graduate': 'school',
        'fa-chalkboard-teacher': 'badge',
        'fa-expand-alt': 'open_in_full',
    }
    for fa_class, ms_name in fa_to_ms.items():
        content = re.sub(
            rf'<i class="fas {fa_class}"[^>]*></i>',
            f'<span class="material-symbols-outlined">{ms_name}</span>',
            content
        )
    
    # Card tools section (search etc)
    content = re.sub(
        r'<div class="card-tools">.*?</div>\s*</div>',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Misc Bootstrap classes
    content = content.replace('class="form-check mb-1"', 'class="flex items-center gap-2 py-1"')
    content = content.replace('class="form-check-input"', 'class="w-4 h-4 accent-indigo-600 rounded"')
    content = content.replace('class="form-check-label"', 'class="text-sm font-body text-on-surface cursor-pointer"')
    content = content.replace('class="text-muted mb-0"', 'class="text-on-surface-variant text-sm"')
    content = re.sub(r'<small class="form-text text-muted">', '<p class="text-xs text-on-surface-variant mt-1">', content)
    content = content.replace('</small>', '</p>')
    
    # Clean up empty wrappers, stray tags
    content = re.sub(r'<div class="col-md-12">\s*</div>', '', content)
    content = re.sub(r'<div class="row">\s*</div>', '', content)
    content = re.sub(r'<div class="container-fluid">\s*</div>', '', content)
    
    # Clean excess whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    count = 0
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for filename in files:
            if not filename.endswith('.html'):
                continue
            filepath = os.path.join(root, filename)
            if migrate_file(filepath):
                count += 1
                print(f"  ✓ Migrated: {os.path.relpath(filepath, TEMPLATES_DIR)}")
    
    print(f"\n{'='*50}")
    print(f"Total files migrated: {count}")

if __name__ == '__main__':
    main()
