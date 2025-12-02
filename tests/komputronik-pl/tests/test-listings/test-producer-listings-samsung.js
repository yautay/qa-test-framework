module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings producer-listing samsung html_cache",
            resource: "/producer/24/samsung.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },

        {
            label: "komputronik-pl listings producer-listing samsung no_html_cache",
            resource: "/producer/24/samsung.html?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};

