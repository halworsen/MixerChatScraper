import time
import datetime
import requests
import json
import re
import os
from win10toast import ToastNotifier
import pyperclip

class MixerScraper():
	scraped_codes_file = "spl_scraped_codes.txt"
	scrape_interval = 1
	retry_interval = 300
	code_length = 17
	code_pattern = r"AP[A-Z]+[0-9A-F]+"
	copy_to_clipboard = True

	def __init__(self, chnl):
		self.channel = chnl
		self.chnl_info_url = "https://mixer.com/api/v1/channels/{}".format(chnl)
		self.chat_api_url = ""

		self.scraping = False
		self.scraped_codes = []

		self.toaster = ToastNotifier()

		self.update_channel_info()
		self.load_codes()

	# are we still valid (aka has mixer shown us the door)
	def valid(self):
		return (self.current_code == 200)

	def win_notify(self, title, text):
		self.toaster.show_toast(title,
							text,
							icon_path=None,
							duration=3,
							threaded=True)

		while self.toaster.notification_active():
			time.sleep(0.1)

	# scrape until mixer says fuck you and gives us the boot
	def begin_scrape(self):
		# its accuracy relies on the scrape interval while scraping but that's fine
		# since it's only used to check if the channel has gone offline
		timer = 0

		while self.valid():
			sleep_time = self.scrape_interval

			if self.scraping:
				self.perform_scrape()
			else:
				print("Channel is offline. Retrying in {} seconds".format(self.retry_interval))
				sleep_time = self.retry_interval

			# check if the channel is (still) online
			if timer >= self.retry_interval:
				self.update_channel_info()

			time.sleep(sleep_time)
			timer += sleep_time
		print("stopped scraping (invalid response code: {})".format(self.current_code))
		self.win_notify("Scraping stopped!", "SPL code scraping has stopped (Response code: {})".format(self.current_code))

	# grab channel info
	def update_channel_info(self):
		response = requests.get(self.chnl_info_url)
		self.current_code = response.status_code

		if response.status_code == 200:
			data = json.loads(response.text)

			self.channel_id = data["id"]
			self.chat_api_url = "https://mixer.com/api/v1/chats/{}/history".format(self.channel_id)

			self.scraping = data["online"]

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
		print("Performing chat scrape... ({})".format(self.current_code))

		history = json.loads(response.text)

		for msg in history:
			for actual_msg in msg["message"]["message"]:
				if actual_msg["type"] != "text":
					continue

				codes = self.find_codes(actual_msg["text"])
				if codes:
					for code in codes:
						self.store_code(code, msg["user_name"])
						print("Found a code! {}".format(code))

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
		if self.copy_to_clipboard:
			pyperclip.copy("/claimpromotion {}".format(code))

		self.scraped_codes.append(code)
		code += " ({})".format(user)

		notif_text = "New Mixer code scraped from {}!\n{}".format(self.channel, code)
		self.win_notify("New Mixer chest code scraped!", notif_text)

		with open(self.scraped_codes_file, "a") as file:
			time = datetime.datetime.now().time()
			file.write(code + " - {}\n".format(time))

print("starting spl mixer code scraper")
scraper = MixerScraper("SmiteGame")
scraper.begin_scrape()