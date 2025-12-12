module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings search-query no_html_cache smoke",
            resource: "search/category/1?query=promo:tp_layout_context",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings search-query no_html_cache",
            resource: "search/category/1?query=klawiatura+czarna",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings search-query no_html_cache",
            resource: "search/category/1?query=klawiatura+czarna&showBuyActiveOnly=1&p=20",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};
