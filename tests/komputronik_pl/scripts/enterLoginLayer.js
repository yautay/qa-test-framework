const locatorsHomePage = require('../locators/locatorsHomePage');
const locatorsLayers = require('../locators/locatorsLayers');
const utils = require('../../../lib/helpers');
const close_cookies = require('../scripts/closeCookies');

module.exports = async (page) => {
    console.log('>>> enterLoginLayer start');

    await close_cookies(page);
    await utils.click(page, locatorsHomePage.buttonLoginToAccount);
    await utils.isVisible(page, locatorsLayers.loginLayer);
    await page.waitForTimeout(2000);
};