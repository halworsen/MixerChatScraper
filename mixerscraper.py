import config as cfg

import time
import datetime
import requests
import json
import re
import os

if cfg.use_win10_notifs:
	from win10toast import ToastNotifier
if cfg.copy_to_clipboard:
	import pyperclip

class MixerScraper():
	mixer_chat_api_url = "https://mixer.com/api/v1/chats/{}/history"
	mixer_channel_api_url = "https://mixer.com/api/v1/channels/{}"

	def __init__(self, channel):
		self.channel = channel
		self.channel_info_url = self.mixer_channel_api_url.format(channel)
		self.chat_api_url = ""

		self.scraping = False
		self.scraped_results = []

		if cfg.use_win10_notifs:
			self.toaster = ToastNotifier()

		self.update_channel_info()
		self.load_matches()

	# did the api request fail
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

	# scrape until mixer gives us the boot
	def begin_scrape(self):
		# its accuracy relies on the scrape interval while scraping but that's fine
		# since it's only used to check if the channel has gone offline
		timer = 0

		while self.valid():
			sleep_time = cfg.scrape_interval

			if self.scraping:
				self.perform_scrape()
			else:
				print("Channel is offline. Retrying in {} seconds".format(cfg.retry_interval))
				sleep_time = cfg.retry_interval

			# check if the channel is (still) online
			if timer >= cfg.retry_interval:
				self.update_channel_info()

			time.sleep(sleep_time)
			timer += sleep_time
		print("Stopped scraping (invalid response code: {})".format(self.current_code))

		if cfg.use_win10_notifs:
			self.win_notify("Scraping stopped!", "Mixer chat scraping has stopped (Response code: {})".format(self.current_code))

	# grab channel info
	def update_channel_info(self):
		response = requests.get(self.channel_info_url)
		self.current_code = response.status_code

		if response.status_code == 200:
			data = json.loads(response.text)

			self.channel_id = data["id"]
			self.chat_api_url = self.mixer_chat_api_url.format(self.channel_id)

			self.scraping = data["online"]

	# regex match for something in some text and return it
	def find_matches(self, text):
		found_matches = []
		for match in re.findall(cfg.pattern, text):
			if match in self.scraped_results:
				continue
			found_matches.append(match)
		return found_matches

	# scrape chat for codes
	def perform_scrape(self):
		response = requests.get(self.chat_api_url)
		self.current_code = response.status_code
		print("Performing chat scrape... ({})".format(self.current_code))

		history = json.loads(response.text)

		for msg in history:
			for actual_msg in msg["message"]["message"]:
				if not actual_msg["type"] in cfg.watched_types:
					continue

				print(actual_msg["text"])

				matches = self.find_matches(actual_msg["text"])
				if matches:
					for match in matches:
						self.store_match(match, msg["user_name"])
						print("Found a match! {}".format(match))

	# load scraped codes from file
	def load_matches(self):
		if not cfg.scraped_result_file:
			return

		now = datetime.datetime.now()
		file_name = cfg.scraped_result_file.format(self.channel, now.strftime("%y%m%d"))
		if not os.path.exists(file_name):
			return

		with open(file_name, "r") as file:
			for line in file:
				matches = self.find_matches(line)
				if matches:
					for match in matches:
						self.scraped_results.append(match)

	# store the match, then notify the user of the match
	def store_match(self, match, user):
		if cfg.copy_to_clipboard:
			pyperclip.copy(cfg.clipboard_format.format(match))

		self.scraped_results.append(match)

		if cfg.use_win10_notifs:
			notif_text = cfg.win10_notif_content.format(self.channel, match)
			self.win_notify(cfg.win10_notif_title, notif_text)

		if not cfg.scraped_result_file:
			return

		now = datetime.datetime.now()
		file_name = cfg.scraped_result_file.format(self.channel, now.strftime("%y%m%d"))
		with open(file_name, "a") as file:
			time = now.time()
			time = time.replace(microsecond=0)

			result = (cfg.file_result_format + "\n").format(match, user, now.date(), time)
			file.write(result)

print("Starting mixer chat scraper")
if cfg.channel_name:
	scraper = MixerScraper(cfg.channel_name)
	scraper.begin_scrape()
else:
	print("No channel name provided! Please update config")