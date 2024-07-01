from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright.async_api import Browser, BrowserContext, Page, ElementHandle
from playwright._impl._api_types import Error
import asyncio
import random
import os
import database
import logging


load_dotenv()

def get_logger():
    root_logger= logging.getLogger(__name__)
    root_logger.setLevel(logging.INFO)
    handler = logging.FileHandler("logs.log", "a", "utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s:%(filename)s:%(asctime)s:%(message)s"))
    root_logger.addHandler(handler)

    return root_logger


logger = get_logger()

BASE_URL = "https://x.com"

BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEOUT = float(os.getenv("TIMEOUT"))
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

accounts = ["DailyMonitor", "BBCWorld", "Entekhab_News"]
comments = [
    "Interesting update on current events! 📰",
    "Thanks for sharing the news! 👍",
    "This article was very insightful! 🌟",
    "Great coverage of the topic! 📢",
    "Appreciate the detailed report! 👏"
]

tweets_container_xpath = '//div[starts-with(@aria-label, "Timeline: ") and substring-after(@aria-label, "’s") = " posts"]'
contexts: list[BrowserContext] = []


async def initialize() -> None:
    await init_contexts()

    for context in contexts:
        await init_pages(context)


async def init_contexts(contexts_number=3) -> None:
    p = await async_playwright().start()
    browser = await p.chromium.launch()
    for _ in range(contexts_number):
        context = await get_context(browser)
        contexts.append(context)


async def init_pages(context: BrowserContext) -> None:
    ckey = contexts.index(context)

    print(f"Initializing pages (context: {ckey})")

    url = f"{BASE_URL}/{accounts[ckey]}"

    await open_page(context, url)


async def get_context(browser: Browser) -> BrowserContext:
    """Creates a new context with authorized cookie."""

    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 6.1; rv:50.0) Gecko/20100101 Firefox/127.0.2")
    await context.add_cookies([{
        "name": "auth_token",     # Cookie name
        "value": AUTH_TOKEN,      # Cookie value
        "domain": ".x.com",       # Cookie domain
        "path": "/",              # Cookie path
        "expires": -1,            # Expiry date (-1 for session cookie)
        "httpOnly": True,         # HTTP only
        "secure": True,           # Secure
        "sameSite": "None",       # SameSite attribute (None, Lax, Strict)
    }])

    return context


async def open_page(context: BrowserContext, url) -> None:
    """Tries to create and fully load a page."""

    try:
        page = await context.new_page()
        await page.goto(url, timeout=0, wait_until="load")
        print(f"Loaded {url}")
    except Error:
        await page.close()
        print(f"Not loaded {url}")


async def comment(account: str) -> str:
    """Performs a procedure to reply a random comment to a random tweet of selected account."""

    async def get_current_tweet() -> list[ElementHandle]:
        """Fetchs loaded tweets."""

        current_tweets = await tweets_container.query_selector_all(f"xpath=.//div[@data-testid='cellInnerDiv']//a[@href='/{account}' and @class='css-175oi2r r-1wbh5a2 r-dnmrzs r-1ny4l3l r-1loqt21']/ancestor::div[@data-testid='cellInnerDiv']")
        if len(current_tweets) < 5:
            await page.mouse.wheel(0, 500)
            await asyncio.sleep(TIMEOUT)

            await get_current_tweet()

        return current_tweets

    async def check_reply_box() -> None:
        """Makes sure that the reply box is shown."""

        if await page.query_selector("//div[@class='public-DraftEditorPlaceholder-inner' and text()='Post your reply']"):
            await asyncio.sleep(TIMEOUT)
        else:
            await asyncio.sleep(TIMEOUT)
            await check_reply_box()

    async def click_on_element(element: ElementHandle, xpath: str) -> None:
        """Makes sure that the button is pressed."""

        try:
            button = await element.query_selector(xpath)
            await button.click()
        except Exception:
            await asyncio.sleep(TIMEOUT)
            await click_on_element(element, xpath)

    async def go_to_main_page():
        url = f"{BASE_URL}/{account}"
        await page.goto(url, timeout=0, wait_until="load")

    try:
        page = contexts[accounts.index(account)].pages[0]

        try:
            tweets_container = await page.query_selector(tweets_container_xpath)
        except Error:
            raise Exception("Tweets container didn't load.")

        current_tweets = await get_current_tweet()

        random_comment = random.choice(comments)
        random_tweet = random.choice(current_tweets)

        # Clicking on a clickable spot of the tweet to open the tweet and save tweet_url
        await (await random_tweet.query_selector("xpath=.//div[@class='css-175oi2r r-18kxxzh r-1wron08 r-onrtq4 r-1awozwy']")).click()
        await asyncio.sleep(TIMEOUT)
        tweet_url = page.url

        if database.is_tweet_exists(tweet_url):
            raise Exception("An already replied tweet was selected.")

        await click_on_element(page, "xpath=.//button[@data-testid='reply']")

        await check_reply_box()
        await page.keyboard.type(random_comment)

        await click_on_element(page, "xpath=.//button[@data-testid='tweetButton']")

        await click_on_element(page, "//span[text()='View']")

        reply_url = page.url

        database.add_reply(random_comment, reply_url, tweet_url, account)
        logger.info(f"New reply just added: {reply_url}.")
    except Exception as err:
        logger.error(f"Error occurred: {err} during replying to @{account}.")
        return f"Error occurred: {err} during replying to @{account}."
    else:
        return (random_comment, reply_url)
    finally:
        await go_to_main_page() # Back to the first page, so the procedure can be repeated again
