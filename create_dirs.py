#!/usr/bin/env python
import os

base_path = r'C:\github-ai-assisted-coding-2153871\summarizer-app'

# Create directories
dirs_to_create = [
    os.path.join(base_path, 'backend', 'app', 'summarizer'),
    os.path.join(base_path, 'backend', 'tests'),
    os.path.join(base_path, 'frontend', 'templates')
]

for dir_path in dirs_to_create:
    os.makedirs(dir_path, exist_ok=True)
    print(f'Created: {dir_path}')

# Verify they exist
print('\nVerifying directories exist:')
for dir_path in dirs_to_create:
    exists = os.path.isdir(dir_path)
    status = '✓' if exists else '✗'
    print(f'{status} {dir_path}')
