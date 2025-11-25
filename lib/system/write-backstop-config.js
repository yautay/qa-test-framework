const fs = require('fs');
const path = require('path');

const makeTimestampName = require('./../system/make-timestamp-name');

function parseArgs(argv) {
    const res = {};
    argv.slice(2).forEach(arg => {
        if (arg.startsWith('--')) {
            const idx = arg.indexOf('=');
            const k = idx === -1 ? arg : arg.slice(0, idx);
            const v = idx === -1 ? undefined : arg.slice(idx + 1);
            const key = k.replace(/^--/, '');
            res[key] = v === undefined ? true : v;
        }
    });
    const allowed = new Set(['site', 'outFile', 'filter', 'referenceHost', 'testHost']);
    const invalid = Object.keys(res).filter(k => !allowed.has(k));
    if (invalid.length) {
        console.error(`Nieprawidłowe parametry: ${invalid.join(', ')}. Dozwolone klucze: site, outFile, filter, referenceHost, testHost.`);
        process.exit(1);
    }
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

    const refHost = args.referenceHost || 'selenium.alfa';
    const testHost = args.testHost || undefined;

    const cfg = createConfig({
        filter: filter,
        reportName: outFile,
        site: site,
        hosts: {reference: refHost, test: testHost}
    });

    const outDir = path.join(process.cwd(), 'backstop_data');
    fs.mkdirSync(outDir, {recursive: true});

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
