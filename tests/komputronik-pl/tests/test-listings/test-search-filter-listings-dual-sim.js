module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings search-filter dual-sim html_cache",
            resource: "search-filter/1596/smartfony-z-dual-sim",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },

        {
            label: "komputronik-pl listings search-filter dual-sim no_html_cache",
            resource: "search-filter/1596/smartfony-z-dual-sim?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};

