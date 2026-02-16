# Each class with page objects must be added below.

from TestCases.NetCornerProducts.pl_komputronik_nuxt.Lib.PageObjects.ReceiversFactory.ReceiverObjectsFactory import (
    ReceiversObjectsFactory,
)

from .AdminPageObject import AdminPageObjects
from .AggregatorObjects import AggregatorObjects
from .CartObjects import (
    CartCleaner,
    CartObjects,
    CartOfferObjects,
    CartProductAmountObjects,
    CartProductPriceObjects,
    CartPromoCodeObject,
)
from .CategoriesObjects import CategoryTreeNavigator, ListingFunctions, NavigateToProductListByUrl
from .CheckoutObjects import (
    CheckoutObjects,
    CheckoutPaymentObjects,
    CheckoutPurchaserObjectsFactory,
    CheckoutReceiverObjectsFactory,
    CheckoutThankYouPage,
    ChooseDeliveryMethodObjects,
)
from .ConfiguratorObjects import (
    AssemblyNewSetFromConfigurator,
    ConfiguratorObjects,
    GoToConfiguratorSummary,
    SelectItemFromConfiguratorSetList,
)
from .FooterObjects import FooterObjects
from .FunctionalObjects import FunctionalObjects
from .HeaderObjects import HeaderObjects
from .HomePageObjects import HomePageObjects
from .LayersObjects import (
    AfterLoginLayerObject,
    AfterRegisterLayerObject,
    CookieLayerObject,
    LayerProductsAddedToCompareObjects,
    LayerPromotionsObject,
    LayerSummaryObject,
    LayerWishlistOnProductPageObjects,
    LayerWishlistOnWishlistSummaryPage,
    LayerWithProductAvailability,
    LayerWithProductRecommendationPageObjects,
    LayerWithStorehouseAvailability,
    LoginLayerObject,
    LogoutLayerObject,
    MontageLayerObject,
    OpinionLayerObjects,
    PurchaserLayerObject,
    ReceiverLayerObject,
)
from .MyAccountObjects import (
    AccountChangePasswordObjects,
    MyAccountObjects,
    MyAccountOrderSummary,
    OrderSummaryObjects,
    WishlistObjects,
)
from .NewPromotionObjects import NewPromotionObjects
from .PasswordRecoveryObjects import PasswordRecoveryObjects
from .ProductListObject import (
    FilterProductsList,
    ProductListAddProductToCompare,
    ProductListObject,
    ProductListPaginationObjects,
    ProductListSort,
    SelectTestProductFromProductListObject,
)
from .ProductPageObjects import (
    ProductLabelsPageObjects,
    ProductOpinionPageObjects,
    ProductPageObjects,
    ProductPromoCodePageObjects,
    ProductPromotionsPageObjects,
)
from .PurchaserObjectsFactory import PurchaserObjectFactory
from .RegisterObjects import (
    RegisterObjects,
)
from .SearchObjects import SearchObjects, SearchSuggestion
from .ToastsObjects import ToastsObjects
