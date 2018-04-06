import time
import datetime
import requests
import json
import re
import os
from win10toast import ToastNotifier

class MixerScraper():
	scraped_codes_file = "spl_scraped_codes.txt"
	scrape_interval = 2
	code_length = 17
	code_pattern = r"AP[A-Z]+[0-9A-F]+"

	def __init__(self, chnl):
		self.channel = chnl
		self.chnl_info_url = "https://mixer.com/api/v1/channels/{}".format(chnl)
		self.chat_api_url = ""

		self.scraped_codes = []

		self.toaster = ToastNotifier()

		self.fetch_channel_info()
		self.load_codes()

	# are we still valid
	def valid(self):
		return (self.current_code == 200)

	def win_notify(self, code):
		self.toaster.show_toast("SPL Mixer Code",
						   "New Mixer code scraped from {}!\n{}".format(self.channel, code),
						   icon_path=None,
						   duration=2.5,
						   threaded=True)

		while self.toaster.notification_active():
			time.sleep(0.1)

	# scrape until mixer says fuck you and gives us the boot
	def begin_scrape(self):
		while self.valid():
			self.perform_scrape()
			time.sleep(self.scrape_interval)

	# setup with channel info
	def fetch_channel_info(self):
		response = requests.get(self.chnl_info_url)
		self.current_code = response.status_code

		if response.status_code == 200:
			data = json.loads(response.text)

			self.channel_id = data["id"]
			self.chat_api_url = "https://mixer.com/api/v1/chats/{}/history".format(self.channel_id)

	# regex match for codes in some text and return it
	def find_codes(self, text):
		found_codes = []
		for found_code in re.findall(self.code_pattern, text):
			if found_code in self.scraped_codes:
				continue
			if len(found_code) == self.code_length:
				found_codes.append(found_code)
		return found_codes

	# scrape chat for codes
	def perform_scrape(self):
		response = requests.get(self.chat_api_url)
		self.current_code = response.status_code

		history = json.loads(response.text)

		for msg in history:
			for actual_msg in msg["message"]["message"]:
				if actual_msg["type"] != "text":
					continue

				codes = self.find_codes(actual_msg["text"])
				if codes:
					for code in codes:
						self.store_code(code, msg["user_name"])

	# load scraped codes from file
	def load_codes(self):
		if not os.path.exists(self.scraped_codes_file):
			return

		with open(self.scraped_codes_file, "r") as file:
			for line in file:
				codes = self.find_codes(line)
				if codes:
					for code in codes:
						self.scraped_codes.append(code)

	# notify with popup & write code to file
	def store_code(self, code, user):
		self.scraped_codes.append(code)
		code += " ({})".format(user)

		self.win_notify(code)
		with open(self.scraped_codes_file, "a") as file:
			time = datetime.datetime.now().time()
			file.write(code + " - {}\n".format(time))

print("starting spl mixer code scraper")
scraper = MixerScraper("SmiteGame")
scraper.begin_scrape()