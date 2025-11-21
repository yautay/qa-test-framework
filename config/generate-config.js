// javascript
// config/generate-config.js
const fs = require('fs');
const path = require('path');
const urls = require('./urls');
const findChrome = require('../lib/find-chrome');
const chromePath = findChrome();

function loadScenarios(site) {
    const siteDir = path.join(__dirname, '..', 'tests', site);
    const testsRootDir = path.join(siteDir, 'tests');

    const siteConfig = require(path.join(siteDir, 'config.json'));
    const channel = siteConfig.channel;

    let scenarios = [];

    const contexts = fs.readdirSync(testsRootDir).filter(item => {
        const itemPath = path.join(testsRootDir, item);
        return fs.statSync(itemPath).isDirectory();
    });

    function processSuiteFile(suitePath, labelPrefix) {
        try {
            delete require.cache[require.resolve(suitePath)];
        } catch (e) {
            // ignore if not resolvable
        }

        const suiteConfig = require(suitePath);

        let defaultResource = null;
        let suiteScenarios = [];

        if (Array.isArray(suiteConfig)) {
            suiteScenarios = suiteConfig;
        } else if (typeof suiteConfig === 'object' && suiteConfig !== null) {
            defaultResource = suiteConfig.defaultResource || null;
            suiteScenarios = suiteConfig.scenarios || [];
        }

        suiteScenarios.forEach(scenario => {
            scenario.label = scenario.label ? `${labelPrefix} - ${scenario.label}` : labelPrefix;

            let {testUrl, referenceUrl} = urls.buildUrl(channel);

            let resource = scenario.resource || defaultResource;
            if (resource) {
                resource = resource.startsWith('/') ? resource : '/' + resource;
                testUrl += resource;
                referenceUrl += resource;
            }

            scenario.url = testUrl;
            scenario.referenceUrl = referenceUrl;
            scenario.onBeforeScript = scenario.onBeforeScript || '../../../lib/silence-browser-console.js';
            scenarios.push(scenario);
        });
    }

    contexts.forEach(context => {
        const contextDir = path.join(testsRootDir, context);

        // Przejrzyj pliki bezpośrednio w kontekście
        const rootFiles = fs.readdirSync(contextDir).filter(file => {
            const filePath = path.join(contextDir, file);
            const ext = path.extname(file).toLowerCase();
            return fs.statSync(filePath).isFile() && (ext === '.json' || ext === '.js');
        });

        rootFiles.forEach(file => {
            const suitePath = path.join(contextDir, file);
            processSuiteFile(suitePath, context);
        });

        // Obsłuż jeden poziom podkatalogów (context/subcontext)
        const subdirs = fs.readdirSync(contextDir).filter(item => {
            const itemPath = path.join(contextDir, item);
            return fs.statSync(itemPath).isDirectory();
        });

        subdirs.forEach(sub => {
            const subDirPath = path.join(contextDir, sub);
            const subFiles = fs.readdirSync(subDirPath).filter(file => {
                const filePath = path.join(subDirPath, file);
                const ext = path.extname(file).toLowerCase();
                return fs.statSync(filePath).isFile() && (ext === '.json' || ext === '.js');
            });

            subFiles.forEach(file => {
                const suitePath = path.join(subDirPath, file);
                processSuiteFile(suitePath, `${context}/${sub}`);
            });
        });
    });

    return scenarios;
}



const komputronikPl_scenarios = loadScenarios('komputronik-pl');
// const dktr_scenarios = loadScenarios('dktr');
// const b2c_scenarios = loadScenarios('techrol_b2c');

const baseArgs = [
    '--no-sandbox',
    '--disable-web-security',
    '--allow-running-insecure-content',
    '--disable-features=IsolateOrigins,site-per-process'
];

module.exports = {
    id: "backstop_default",
    viewports: [
        {label: "desktop", width: 1920, height: 1080},
        {label: "tabletL", width: 1200, height: 800},
        {label: "tabletM", width: 768, height: 1024},
        {label: "mobile", width: 375, height: 667}
    ],
    scenarios: [
        ...komputronikPl_scenarios,
        // ...dktr_scenarios,
        // ...b2c_scenarios
    ],
    paths: {
        bitmaps_reference: "backstop_data/bitmaps_reference",
        bitmaps_test: "backstop_data/bitmaps_test",
        html_report: "backstop_data/html_report",
        ci_report: "backstop_data/ci_report"
    },
    engine: "playwright",
    engineOptions: chromePath
        ? {
            executablePath: chromePath,
            headless: true,
            args: baseArgs
        }
        : {
            launchOptions: {
                channel: 'chrome',
                headless: true,
                args: baseArgs
            }
        },
    report: ["CI"],
    debug: false,
    debugWindow: false,
};
