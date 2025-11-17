const locators = require('../locators/homePage');
const utils = require('../../../utils/helpers');
const close_cookies = require('../scripts/closeCookies');

module.exports = async (page, scenario) => {
    await close_cookies(page, scenario);
    console.log('>>> ENTER LOGIN LAYER');
    await utils.clickXPath(page, locators.buttonLoginToAccount);
};
