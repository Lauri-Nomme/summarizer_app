const fs = require('fs');
const path = require('path');

const basePath = 'C:\\github-ai-assisted-coding-2153871\\summarizer-app';

const dirsToCreate = [
    path.join(basePath, 'backend', 'app', 'summarizer'),
    path.join(basePath, 'backend', 'tests'),
    path.join(basePath, 'frontend', 'templates')
];

dirsToCreate.forEach(dirPath => {
    fs.mkdirSync(dirPath, { recursive: true });
    console.log(`Created: ${dirPath}`);
});

console.log('\nVerifying directories exist:');
dirsToCreate.forEach(dirPath => {
    const exists = fs.existsSync(dirPath);
    const status = exists ? '✓' : '✗';
    console.log(`${status} ${dirPath}`);
});
