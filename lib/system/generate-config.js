// file: config/generate-config.js
const findChrome = require('./../system/find-chrome');
const loadScenarios = require('./../system/load-scenarios');
const applyFilterIfAvailable = require('./../system/apply-filter-if-available');
const makeTimestampName = require('./../system/make-timestamp-name');

function createConfig(opts = {}) {
    const { filter, reportName, site } = opts;

    const scenarios = applyFilterIfAvailable(loadScenarios(site), filter);

    const baseArgs = [
        '--no-sandbox',
        '--disable-web-security',
        '--allow-running-insecure-content',
        '--disable-features=IsolateOrigins,site-per-process'
    ];

    const chromePath = findChrome();
    console.log("Browser executable path", chromePath);

    const finalName = reportName && String(reportName).trim()
        ? String(reportName).trim()
        : makeTimestampName();

    const makePath = (base) => `${base}_${finalName}`;

    return {
        id: "backstop_default",
        viewports: [
            { label: "desktop", width: 1920, height: 1080 },
            { label: "tabletL", width: 1200, height: 800 },
            { label: "tabletM", width: 768, height: 1024 },
            { label: "mobile", width: 375, height: 667 }
        ],
        scenarios,
        paths: {
            bitmaps_reference: makePath("backstop_data/bitmaps_reference"),
            bitmaps_test: makePath("backstop_data/bitmaps_test"),
            html_report: makePath("backstop_data/html_report"),
            ci_report: makePath("backstop_data/ci_report"),
            engine_scripts: "backstop_data/engine_scripts"
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
}

module.exports = createConfig;
