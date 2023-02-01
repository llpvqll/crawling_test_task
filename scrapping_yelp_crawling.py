import json
from typing import Any

from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import constants
from chrome_driver import ChromeDriver


class FlightScrapper:
    def __init__(self) -> None:

        self._category = str(input("Enter category (example: Restaurant: "))
        self._location = str(input("Enter location (example: New York, NY: "))
        self._options = self._set_options()
        self._service = Service(ChromeDriverManager().install())
        self._driver = ChromeDriver(self._service, self._options)
        self.date_format = '%d  %b %y'
        self.business_links: list[str] = []
        self.business_data: list[dict[str, Any]] = []
        self._base_url = constants.BASE_YELP_URL

    def _set_options(self) -> Options:

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--enable-experimental-cookie-features')
        return chrome_options

    def get_list_of_business(self) -> list[str]:
        try:
            with self._driver as driver:
                driver.get(self._base_url)

                category = driver.find_element(By.XPATH, constants.CATEGORY_SEARCH)
                category.send_keys(Keys.CONTROL, 'a')
                category.send_keys(self._category)

                location = driver.find_element(By.XPATH, constants.LOCATION_SEARCH)
                location.send_keys(Keys.CONTROL, 'a')
                location.send_keys(self._location)

                driver.find_element(By.XPATH, constants.SEARCH_BUTTON).click()
                try:
                    pagination_count = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, constants.PAGINATION_NUMBER))
                    ).text[5:]
                except (NoSuchElementException, TimeoutException):
                    pagination_count = 10

                for item in range(int(pagination_count) + 1):
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, constants.BUSINESS_LINK)))
                    a = driver.find_elements(By.XPATH, constants.BUSINESS_LINK)
                    for link in a:
                        self.business_links.append(link.get_attribute('href'))
                    try:
                        next_page = driver.find_element(By.XPATH, constants.NEXT_PAGE)
                        driver.get(next_page.get_attribute('href'))
                    except NoSuchElementException:
                        break
                return self.business_links
        except WebDriverException:
            raise ValueError("Invalid format or bad response!")

    @staticmethod
    def get_business_website_url(driver: Chrome) -> str | None:
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, constants.ORDER_BUTTON_FOR_WAIT)))
            return driver.find_element(By.XPATH, constants.BUSINESS_WEBSITE).text
        except (NoSuchElementException, TimeoutException):
            return None

    @staticmethod
    def get_business_reviews(driver: Chrome) -> list[dict[str, str]] | str:
        result_list: list[dict[str, str]] = []
        try:
            reviewer_name = driver.find_elements(By.XPATH, constants.REVIEWER_NAME)
            reviewer_location = driver.find_elements(By.XPATH, constants.REVIEWER_LOCATION)
            review_date = driver.find_elements(By.XPATH, constants.REVIEW_DATE)
            for index, item in enumerate(reviewer_name[:5]):
                result_list.append(
                    {
                        'reviewer_name': item.text,
                        'reviewer_location': reviewer_location[index].text,
                        'review_date': review_date[index].text
                    }
                )
            return result_list
        except (NoSuchElementException, TimeoutException):
            return 'No reviews yet!'

    def get_business_data(self) -> None:
        for item in self.get_list_of_business():
            with self._driver as driver:
                driver.get(item)
                self.business_data.append(
                    {
                        'business_name': WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, constants.BUSINESS_NAME))
                        ).text,
                        'business_rating': driver.find_element(
                            By.XPATH, constants.BUSINESS_RATING
                        ).get_attribute('aria-label'),
                        'number_of_reviews': driver.find_element(By.XPATH, constants.BUSINESS_REVIEWS).text,
                        'business_yelp_url': item,
                        'business_website': self.get_business_website_url(driver),
                        'business_reviews': self.get_business_reviews(driver)
                    }
                )
        self.save_business_data_to_json()

    def save_business_data_to_json(self):
        with open('business_data.json', 'w') as file:
            file.write(json.dumps(self.business_data, indent=10))


if __name__ == '__main__':
    FlightScrapper().get_business_data()
