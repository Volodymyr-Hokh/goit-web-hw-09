import json
import asyncio

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com"


async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()
    

def get_quote_data(quote):
    text = quote.find("span", class_="text").text
    author = quote.find("small", class_="author").text
    tags = [tag.text for tag in quote.find("div", class_="tags").find_all("a", class_="tag")]
    result = {
        "tags": tags,
        "author": author,
        "quote": text
    }
    return result


async def parse_author(session, author_link):
    author_url = BASE_URL + author_link
    async with session.get(author_url) as response:
        response_html = await response.text()

    soup = BeautifulSoup(response_html, "lxml")
    fullname = soup.find("h3", class_="author-title").text.strip()
    born_date = soup.find("span", class_="author-born-date").text.strip()
    born_location = soup.find("span", class_="author-born-location").text.strip()
    description = soup.find("div", class_="author-description").text.strip()

    return {
        "fullname": fullname,
        "born_date": born_date,
        "born_location": born_location,
        "description": description
    }


async def main():
    quotes_data = []
    author_links = set()
    next_page = "/page/1/"

    async with aiohttp.ClientSession() as session:
        while next_page:
            response_html = await fetch_url(session, BASE_URL + next_page)
            soup = BeautifulSoup(response_html, "lxml")
            quotes = soup.find_all("div", class_="quote")

            for quote in quotes:
                quote_data = get_quote_data(quote)
                quotes_data.append(quote_data)

                author_link = quote.find("small", class_="author").find_next_sibling("a").get("href")
                author_links.add(author_link)

            try:
                next_page = soup.find("ul", class_="pager").find("li", class_="next").find("a").get("href")
            except AttributeError:
                break

        quotes_json = json.dumps(quotes_data, indent=4, ensure_ascii=False)
        authors_data = await asyncio.gather(*[parse_author(session, author_link) for author_link in author_links])
        authors_json = json.dumps(authors_data, indent=4, ensure_ascii=False)

    with open("quotes.json", "w", encoding="utf-8") as quotes_file:
        quotes_file.write(quotes_json)

    with open("authors.json", "w", encoding="utf-8") as authors_file:
        authors_file.write(authors_json)


if __name__ == "__main__":
    asyncio.run(main())

