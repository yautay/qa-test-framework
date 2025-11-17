const locators = require('../locators/homePage');
const utils = require('../../../utils/helpers');

module.exports = async (page, scenario) => {
    console.log('>>> CLICK COOKIES POPUP');
    await utils.clickXPath(page, locators.buttonCloseCookie);
};
