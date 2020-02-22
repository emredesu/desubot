import nhentai
import requests
import re


def get_doujin_data(doujin_numbers):
	doujin = nhentai.Doujinshi(doujin_numbers)
	dataset = {"name": doujin.name, "tags": doujin.tags, "page_count": doujin.pages, "image_gallery": list(doujin), "cover": doujin.cover}

	return dataset


def search_for_doujin(search_term):
	results = [d for d in nhentai.search(search_term, 2)]
	return results


def get_random_doujin():
	request = requests.get("https://nhentai.net/random")
	result = re.search("https://nhentai.net/g/(.*)/", request.url)
	magic_numbers = result.group(1)

	return magic_numbers
