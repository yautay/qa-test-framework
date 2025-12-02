module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings search-filter gaming html_cache",
            resource: "search-filter/5022/laptopy-do-gier",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },

        {
            label: "komputronik-pl listings search-filter gaming no_html_cache",
            resource: "search-filter/5022/laptopy-do-gier?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};

