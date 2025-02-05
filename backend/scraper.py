# backend/scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def get_program_details(search_query: str):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)  # タイムアウト設定

    result = []
    try:
        url = f"https://bangumi.org/search?q={search_query}&area_code=23"
        safe_get(driver, url)

        program_links = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li > a[href*='/tv_events/']"))
        )
        links = [link.get_attribute('href') for link in program_links]

        for link in links[:3]:
            try:
                safe_get(driver, link)
                title = driver.find_element(By.CLASS_NAME, 'program_title').text
                supplement = driver.find_element(By.CLASS_NAME, 'program_supplement').text
                cast_elements = driver.find_elements(By.CSS_SELECTOR, ".addition li h2.heading + p a")
                cast_names = [c.text for c in cast_elements if c.text]
                result.append({
                    "url": link,
                    "title": title,
                    "supplement": supplement,
                    "cast_names": cast_names
                })
            except Exception as e:
                print(f"エラーが発生しました: {e}")
    finally:
        driver.quit()

    return result

def safe_get(driver, url, retries=3):
    for attempt in range(retries):
        try:
            driver.get(url)
            return
        except TimeoutException:
            print(f"Attempt {attempt + 1} failed. Retrying...")
    raise TimeoutException(f"Failed to load {url} after {retries} attempts.")
