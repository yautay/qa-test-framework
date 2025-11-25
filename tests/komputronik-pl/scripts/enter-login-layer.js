const locatorsHomePage = require('../locators/locators-home-page');
const locatorsLayers = require('../locators/locators-layers');
const utils = require('../../../lib/functional/helpers');
const close_cookies = require('./close-cookies');

module.exports = async (page) => {
    console.log('>>> enterLoginLayer start');

    await close_cookies(page);
    await utils.click(page, locatorsHomePage.buttonLoginToAccount);
    await utils.isVisible(page, locatorsLayers.loginLayer);
    await page.waitForTimeout(2000);
};