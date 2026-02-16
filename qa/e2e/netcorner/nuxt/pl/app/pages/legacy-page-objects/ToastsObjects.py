from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import (
    CommonBasePageObject as CommonPO,
)
from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageLocators.ToastsLocators import (
    ToastsLocators,
)
from TestData.pl_komputronik_nuxt.PlCommonKeys import ToastTypeKey


class ToastsObjects(CommonPO):
    def __init__(self, driver):
        super().__init__(driver)

    def get_toast(self) -> ToastTypeKey | None:
        self.time.sleep(self.TIMEOUT_SHORT)
        toast = self.wait_for.element_visible(ToastsLocators.ELEMENT_toast,
                                              timeout=self.TIMEOUT_NUXT_TOASTS,
                                              raise_exception=False)
        if not toast:
            return None

        text = toast.text
        css_class = toast.get_attribute("class") or ""

        for toast_type in ToastTypeKey:
            if toast_type.value in text:
                return toast_type

        if "toast-positive" in css_class:
            return ToastTypeKey.POSITIVE
        if "toast-negative" in css_class:
            return ToastTypeKey.NEGATIVE

        return None
