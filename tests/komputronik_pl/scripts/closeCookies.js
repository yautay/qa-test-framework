const locators = require('../locators/locatorsHomePage');
const utils = require('../../../lib/helpers');

module.exports = async (page) => {
    const closed_cookie_popup = await utils.clickXPath(page, locators.buttonCloseCookie);
};
