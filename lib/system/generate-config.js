const findChrome = require('./../system/find-chrome');
const loadScenarios = require('./../system/load-scenarios');
const applyFilterIfAvailable = require('./filter');
const makeTimestampName = require('./../system/make-timestamp-name');

function createConfig(opts = {}) {
    const { filter, reportName, site, hosts, engine = 'playwright' } = opts;

    const scenarios = applyFilterIfAvailable(loadScenarios(site, hosts), filter);

    const baseArgs = [
        '--no-sandbox',
        '--disable-web-security',
        '--allow-running-insecure-content',
        '--disable-features=IsolateOrigins,site-per-process'
    ];

    const chromePath = findChrome();

    const finalName = reportName && String(reportName).trim()
        ? String(reportName).trim()
        : makeTimestampName();

    const makePath = (base) => `${base}_${finalName}`;

    const engineName = String(engine).toLowerCase() === 'puppeteer' ? 'puppeteer' : 'playwright';

    return {
        id: "backstop_default",
        viewports: [
            { label: "desktop", width: 1920, height: 1080 },
            { label: "tablet", width: 768, height: 1024 },
            { label: "mobile", width: 360, height: 667 }
        ],
        scenarios,
        paths: {
            bitmaps_reference: makePath("backstop_data/bitmaps_reference"),
            bitmaps_test: makePath("backstop_data/bitmaps_test"),
            html_report: makePath("backstop_data/html_report"),
            ci_report: makePath("backstop_data/ci_report"),
            engine_scripts: makePath("backstop_data/engine_scripts")
        },
        engine: engineName,
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
}

module.exports = createConfig;
