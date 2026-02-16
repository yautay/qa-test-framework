class HomePageLocators:
    NUXT_WILDCARD = "//div[@id='__nuxt']"
    CONTAINER_daily_deal = "//div[@data-name='dailyDeal']"
    CONTAINER_ozo_box = "//*[@data-name='DailyDealWidget']"
    ELEMENTS_daily_deal_product_tiles = CONTAINER_daily_deal + "//div[@data-name='cardProduct']"

    CONTAINER_banners = "//img[@class='absolute top-0']"
    ELEMENT_banners_thumb_navigator = "//div[@id='pagination-hero-banner']"

    CONTAINER_new_products = "//div[@data-name='dailyDeal']"
    CHECKBOX_new_products = CONTAINER_new_products + "//div//h2"
    ELEMENT_new_products_not_hidden_products = CONTAINER_new_products + "//div[contains(@data-name, 'cardProduct')]"

    CONTAINER_our_promotions = "//h2[contains(@class, 'font-headline')]//a[contains(text(), 'Promocje')]"

    ELEMENT_canonical = "//link[@rel='canonical']"
    ELEMENT_meta_robots = "//meta[@name='robots']"


class HomePageOzoBoxLocators:
    CONTAINER_ozo_box = HomePageLocators.CONTAINER_ozo_box
    ELEMENT_promo_badge = CONTAINER_ozo_box + "//div[@data-name='badge']//div[contains(text(), 'Promocja')]"
    ELEMENT_title = CONTAINER_ozo_box + "//p[contains(@class,'line-clamp-3')]"
    ELEMENT_current_price = CONTAINER_ozo_box + "//span[contains(@class,'text-2xl') and contains(@class,'font-bold')]"
    ELEMENT_original_price = CONTAINER_ozo_box + "//p[contains(text(),'Cena bez promocji')]/span"
    ELEMENT_lowest_price = CONTAINER_ozo_box + "//p[contains(text(),'Najniższa cena')]/span"
    ELEMENT_countdown_days = CONTAINER_ozo_box + "//div[.//p[normalize-space()='dni']]//p[contains(@class,'font-bold')]"
    ELEMENT_sold_amount = CONTAINER_ozo_box + "//div[contains(text(),'Sprzedano')]/span"
    ELEMENT_remaining_amount = CONTAINER_ozo_box + "//div[contains(text(),'Pozostało')]/span"

