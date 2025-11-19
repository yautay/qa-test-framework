const locators = require('../locators/locators-home-page');
const utils = require('../../../lib/helpers');


module.exports = async (page) => {
    await utils.click(page, locators.buttonCloseCookie);
    await page.waitForTimeout(3000);
};
