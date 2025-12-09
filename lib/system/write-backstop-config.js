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
    console.log(args);
    const filter = args.filter || '';

    const outFile = args.outFile && String(args.outFile).trim()
        ? String(args.outFile).trim()
        : makeTimestampName();

    const site = args.site || 'komputronik-pl';

    const createConfig = require('./../system/generate-config.js');

    const refHost = args.referenceHost || undefined;
    const testHost = args.testHost || 'selenium.alfa';

    const usePuppeteerMain = Boolean(
        (typeof filter === 'string' && filter.includes('disable-js'))
    );

    const cfgMain = createConfig({
        filter: filter + ' !disabled-js',
        reportName: outFile,
        site: site,
        hosts: {reference: refHost, test: testHost},
        engine: usePuppeteerMain ? 'puppeteer' : undefined
    });

    const disabledFilter = 'disabled-js';
    const cfgDisabled = createConfig({
        filter: disabledFilter,
        reportName: outFile,
        site: site,
        hosts: {reference: refHost, test: testHost},
        engine: 'puppeteer'
    });

    const outDir = path.join(process.cwd(), 'backstop_data');
    fs.mkdirSync(outDir, {recursive: true});

    const filenameMain = `backstop_config_${outFile}.json`;
    const outPathMain = path.join(outDir, filenameMain);

    const filenameDisabled = `backstop_config_${outFile}_disabled_js.json`;
    const outPathDisabled = path.join(outDir, filenameDisabled);

    try {
        fs.writeFileSync(outPathMain, JSON.stringify(cfgMain, null, 2), 'utf8');
        console.log(`zapisano konfigurację: ${path.relative(process.cwd(), outPathMain)}`);

        if (Array.isArray(cfgDisabled.scenarios) && cfgDisabled.scenarios.length > 0) {
            fs.writeFileSync(outPathDisabled, JSON.stringify(cfgDisabled, null, 2), 'utf8');
            console.log(`zapisano konfigurację (disabled-js): ${path.relative(process.cwd(), outPathDisabled)}`);
        } else {
            console.log('Brak scenariuszy pasujących do filtru disable-js — plik disabled_js nie został zapisany.');
        }

        console.log(`Uruchom:   npx backstop reference --configPath=${path.join('backstop_data', filenameMain)}`);
        console.log(`Następnie: npx backstop test --configPath=${path.join('backstop_data', filenameMain)}`);

        if (Array.isArray(cfgDisabled.scenarios) && cfgDisabled.scenarios.length > 0) {
            console.log(`Dla testów z wyłączonym JS: npx backstop reference --configPath=${path.join('backstop_data', filenameDisabled)}`);
            console.log(`Dla testów z wyłączonym JS: npx backstop test --configPath=${path.join('backstop_data', filenameDisabled)}`);
        }
    } catch (e) {
        console.error('(e) Nie udało się zapisać pliku:', e.message);
        process.exit(1);
    }
})();
