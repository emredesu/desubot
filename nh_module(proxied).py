import requests
import re


def get_doujin_data(doujin_numbers):
	data = requests.get(f"https://imgproxy.ivr.ovh/nh/{doujin_numbers}").json()
	dataset = {"name": data["title"]["pretty"], "tags": [data["tags"][i]["name"] for i in range(len(data["tags"]))], "page_count": len(data["pages"]), "image_gallery": [data["pages"][i]["url"] for i in range(len(data["pages"]))], "cover": data["cover"]}

	return dataset


def search_doujins(args):
	data = requests.get(f"https://imgproxy.ivr.ovh/nhsearch?tags={args}").json()
	ids = [data["result"][i]["id"] for i in range(len(data["result"]))]

	return ids


def get_random_doujin():
	return int(requests.get("https://imgproxy.ivr.ovh/nhrandom").json()["random"])

