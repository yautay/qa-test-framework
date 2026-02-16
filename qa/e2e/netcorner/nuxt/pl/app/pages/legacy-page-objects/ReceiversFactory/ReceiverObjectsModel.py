from abc import ABC, abstractmethod

from TestCases.NetCornerProducts.Common.PageObjects.CommonBasePageObject import CommonBasePageObject


class ReceiversObjectsModel(ABC, CommonBasePageObject):
    """
    This class represents the model for managing receiver objects.

    It provides abstract methods for filling a new receiver object and retrieving the available objects.

    :param ABC: Abstract Base Class
    :param CommonBasePageObject: Base class for all page objects
    """

    @abstractmethod
    def enter_form_layer(self, skip_if_receiver_exists: bool = True):
        pass

    @abstractmethod
    def fill_new_receiver_object(self):
        pass

    @abstractmethod
    def edit_existing_receiver_object(self):
        pass

    @abstractmethod
    def assert_existing_receiver_objects(self) -> bool:
        pass

    @abstractmethod
    def delete_existing_receiver_object(self):
        pass

    @abstractmethod
    def back_to_checkout(self):
        pass
