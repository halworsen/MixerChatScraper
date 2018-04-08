# Name of the channel whose chat you want to scrape
channel_name = ""

# How often to perform a scrape
# Be careful with intervals <= 0.125 as that'll exceed the rate limit for the mixer API
scrape_interval = 1
# How often to check if the channel is on-/offline
# This is +/- the scrape interval when the script is scraping
retry_interval = 300

# The regex pattern to use for matching
pattern = r"@[a-zA-Z0-9_]+"

# Message types to look for matches in
watched_types = ["text", "tag"]

##################
# Niche features #
##################

# Which file to save matches to. You can use string formatting to add the channel name and date (YYMMDD)
# If you don't want to use this just leave the string empty
scraped_result_file = "mixer_scrape_{}{}.txt"
# How to format the match results in the result file
# 1. The match itself
# 2. Username
# 3. Date
# 4. Time
file_result_format = "{} ({}) - {} {}"

# Copy matches to clipboard?
copy_to_clipboard = False
# What to copy to the clipboard. Formatted with the match
clipboard_format = "{}"
# Use windows 10 toaster notifications for matches?
use_win10_notifs = False
# Title of the toaster notifications
win10_notif_title = "New match found!"
# Content of the toaster notifications. Formatting order is
# 1. Channel name
# 2. The match itself
win10_notif_content = "New match in {}!\n{}"