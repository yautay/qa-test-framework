from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiversCourierObjects import (
    ReceiversCourierObjects,
)


class ReceiversDigitalObjects(ReceiversCourierObjects):
    def __init__(self, driver, test_data: dict):
        super().__init__(driver, test_data)
