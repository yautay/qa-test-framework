const fs = require('fs');
const path = require('path');

const makeTimestampName = require('./../system/make-timestamp-name');

function parseArgs(argv) {
    const res = {};
    argv.slice(2).forEach(arg => {
        if (arg.startsWith('--')) {
            const [k, v] = arg.split('=');
            const key = k.replace(/^--/, '');
            res[key] = v === undefined ? true : v;
        }
    });
    return res;
}

(async function main() {
    const args = parseArgs(process.argv);
    const filter = args.filter || '';

    const outFile = args.outFile && String(args.outFile).trim()
        ? String(args.outFile).trim()
        : makeTimestampName();

    const site = args.site || 'komputronik-pl';

    const createConfig = require('./../system/generate-config.js');

    const cfg = createConfig({ filter:filter, reportName: outFile, site:site });

    const outDir = path.join(process.cwd(), 'backstop_data');
    fs.mkdirSync(outDir, { recursive: true });

    const filenameBase = `backstop_config_${outFile}`;
    const filename = `${filenameBase}.json`;
    const outPath = path.join(outDir, filename);

    try {
        fs.writeFileSync(outPath, JSON.stringify(cfg, null, 2), 'utf8');
        const relPath = path.relative(process.cwd(), outPath);
        console.log(`zapisano konfigurację: ${relPath}`);
        console.log(`Uruchom:   npx backstop reference --configPath=${path.join('backstop_data', filename)}`);
        console.log(`Następnie: npx backstop test --configPath=${path.join('backstop_data', filename)}`);
    } catch (e) {
        console.error('(e) Nie udało się zapisać pliku:', e.message);
        process.exit(1);
    }
})();
