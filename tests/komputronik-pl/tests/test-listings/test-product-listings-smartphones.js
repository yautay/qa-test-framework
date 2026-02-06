module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings product-listing phones html_cache",
            resource: "/category/1596/telefony.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },

        {
            label: "komputronik-pl listings product-listing phones no_html_cache",
            resource: "/category/1596/telefony.html?a=0",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};

