import nhentai
import requests
import re


def get_doujin_data(doujin_numbers):
	doujin = nhentai.get_doujin(doujin_numbers)
	dataset = {"name": doujin.titles["pretty"], "tags": [doujin.tags[i][2] for i in range(len(doujin.tags))], "page_count": len(doujin.pages), "image_gallery": [doujin.pages[i].url for i in range(len(doujin.pages))], "cover": doujin.cover}

	return dataset


def get_random_doujin():
	request = requests.get("https://nhentai.net/random")
	result = re.search("https://nhentai.net/g/(.*)/", request.url)
	magic_numbers = result.group(1)

	return magic_numbers
