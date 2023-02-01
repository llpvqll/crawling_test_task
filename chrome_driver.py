from selenium import webdriver
import traceback


class ChromeDriver:

    def __init__(self, service, options):
        self._service = service
        self._options = options
        self._driver = None

    def __enter__(self):
        self._driver = webdriver.Chrome(service=self._service, options=self._options)
        return self._driver

    def __exit__(self, exc_type, exc_value, tb):
        self._driver.close()
        self._driver.quit()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        return True
