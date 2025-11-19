const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

module.exports = function findChrome() {
    const common = [
        process.env['PROGRAMFILES'] && path.join(process.env['PROGRAMFILES'], 'Google', 'Chrome', 'Application', 'chrome.exe'),
        process.env['PROGRAMFILES(X86)'] && path.join(process.env['PROGRAMFILES(X86)'], 'Google', 'Chrome', 'Application', 'chrome.exe'),
        path.join(process.env['LOCALAPPDATA'] || '', 'Google', 'Chrome', 'Application', 'chrome.exe')
    ].filter(Boolean);

    for (const p of common) {
        if (fs.existsSync(p)) return p;
    }

    try {
        const out = execSync('where chrome', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
        if (out) {
            const first = out.split(/\r?\n/)[0];
            if (fs.existsSync(first)) return first;
        }
    } catch (e) {
        console.log(e)
    }

    return null;
};