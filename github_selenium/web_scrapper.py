import csv

from pybloomfilter import BloomFilter

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

TIMEOUT = 20
GITHUB_IMG='//img[contains(@class, "avatar width-full height-full")]'
GITHUB_REPO_TITLE='//a[@itemprop="name codeRepository"]'
GITHUB_LANGUAGE='//span[@itemprop="programmingLanguage"]'
GITHUB_USERNAME_TITLE='//span[@class="link-gray pl-1"]'

PATH_PREFIX_DEFAULT='data/users_order_'

options = webdriver.ChromeOptions()
options.add_argument(' - incognito')

browser = webdriver.Chrome(
    executable_path=r'/home/kevin/Downloads/chromedriver',
    options=options
)

seen_usernames = BloomFilter(10000, .03)

def make_url(user, tab):
    return f'https://github.com/{user}?tab={tab}'


def is_loaded(url):
    browser.get(url)
    try:
        WebDriverWait(browser, TIMEOUT).until(
            EC.visibility_of_element_located((
                By.XPATH, GITHUB_IMG
            ))
        )

    except TimeoutException:
        print(f'Timed out waiting for {url} to load')
        return False

    return True




def get_repos(username):
    url = make_url(username, 'repositories')
    if not is_loaded(url):
        return []


    title_elements = browser.find_elements_by_xpath(
        GITHUB_REPO_TITLE
    )

    titles = [x.text for x in title_elements]

    language_elements = browser.find_elements_by_xpath(
        GITHUB_LANGUAGE
    )

    languages = [x.text for x in language_elements]

    return [(t, l) for t, l in zip(titles, languages)]


def get_followers(username):
    url = make_url(username, 'followers')
    if not is_loaded(url):
        return []

    title_elements = browser.find_elements_by_xpath(
        GITHUB_USERNAME_TITLE
    )

    yield username
    for element in title_elements:
        follower = element.text
        if follower in seen_usernames:
            continue

        seen_usernames.add(follower)
        yield follower


def create_higher_order_users(order, path_prefix=PATH_PREFIX_DEFAULT):
    initial_path = f'{path_prefix}{order}.txt'
    higher_order_path = f'{path_prefix}{order + 1}.txt'
    with open(initial_path) as f, open(higher_order_path, 'w') as o:
        for line in f.readlines():
            username = line.strip()
            followers_gen = get_followers(username)
            for follower in followers_gen:
                o.write(follower + '\n')

if __name__ == '__main__':
    for order in range(1):
        create_higher_order_users(order)

    with open(f'{PATH_PREFIX_DEFAULT}2.txt') as f, open('data/output.csv', 'w') as o:
        headers = ['username', 'repo_name', 'most_used_language']
        csv_writer = csv.writer(o)
        csv_writer.writerow(headers)
        for line in f.readlines():
            username = line.strip()
            response_pairs = get_repos(username)
            for title, language in response_pairs:
                csv_writer.writerow([username, title, language])
        browser.quit()
