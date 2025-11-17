module.exports = {
    /**
     * Kliknięcie elementu po XPath
     */
    clickXPath: async (page, xpath, timeout = 3000) => {
        try {
            await page.waitForXPath(xpath, { timeout });
            const elements = await page.$x(xpath);
            console.log('elements', elements);
            if (!elements || elements.length === 0) {
                console.log(`>>> XPath not found: ${xpath}`);
                return false;
            }
            await elements[0].click();
            console.log(`>>> Clicked XPath: ${xpath}`);
            return true;
        } catch (e) {
            console.log(`>>> Failed clicking XPath: ${xpath}`);
            return false;
        }
    },
};