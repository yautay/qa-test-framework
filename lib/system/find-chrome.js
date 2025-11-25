// file: lib/find-chrome.js
const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

function exists(p) {
    try { return fs.existsSync(p); } catch { return false; }
}

function tryExec(cmd) {
    try {
        const out = execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] });
        if (!out) return null;
        return out.trim().split(/\r?\n/)[0] || null;
    } catch {
        return null;
    }
}

function findChrome() {
    const platform = process.platform;

    // WINDOWS
    if (platform === 'win32') {
        const possible = [
            // standard installations
            path.join(process.env.PROGRAMFILES, 'Google/Chrome/Application/chrome.exe'),
            path.join(process.env['PROGRAMFILES(X86)'], 'Google/Chrome/Application/chrome.exe'),
            // user-local installation
            path.join(process.env.LOCALAPPDATA, 'Google/Chrome/Application/chrome.exe'),
        ];

        for (const p of possible) {
            if (p && exists(p)) return p;
        }

        // fallback to PATH
        return tryExec('where chrome') || null;
    }

    // macOS
    if (platform === 'darwin') {
        const chromeApp = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
        const chromeAppUser = path.join(process.env.HOME, 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome');

        if (exists(chromeApp)) return chromeApp;
        if (exists(chromeAppUser)) return chromeAppUser;

        // fallback
        const which = tryExec('which google-chrome') || tryExec('which chromium') || null;
        if (which) return which;

        return null;
    }

    // LINUX
    const bin = tryExec('which google-chrome')
        || tryExec('which google-chrome-stable')
        || tryExec('which chromium-browser')
        || tryExec('which chromium')
        || null;

    return bin;
}

module.exports = findChrome;
