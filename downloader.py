"""
required:
selenium 			(https://pypi.org/project/selenium/#files)
webdriver-manager 	(https://pypi.org/project/webdriver-manager/#files)
"""
import os
import shutil
import threading
import time

from pip._internal.utils import filetypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def get_page_count(_driver, url):
	http_GET(_driver, f"{url}?page=99999")
	_count = "1"
	page_buttons = _driver.find_elements(By.CLASS_NAME, 'usa-pagination__button')
	for btn in page_buttons:
		_count = btn.text
	return int(_count)

def http_GET(_driver, url):
	_driver.get(url)
	while _driver.execute_script("return document.readyState") != "complete":
		time.sleep(0.1)
	button = _driver.find_elements(By.ID, "age-button-yes")
	if button:
		try:
			button[0].click()
			time.sleep(1)
		except Exception as ignored:
			_ = ignored

def log_failed(pdf):
	with open("failed.txt", "a+") as a:
		a.write(pdf + "\n")

class DatasetDownloader:
	def __init__(self, dataset, output):
		print(f"downloading started for dataset {dataset}")
		self.output = output
		options = webdriver.ChromeOptions()
		options.add_experimental_option('prefs', {
			"download.default_directory": self.output,
			"download.prompt_for_download": False,
			"plugins.always_open_pdf_externally": True
		})
		self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
		try:
			self.driver.minimize_window()
		except:
			pass
		self.download_dataset_pdfs(dataset)

	def get_dataset_page_count(self, dataset):
		http_GET(self.driver, f"https://www.justice.gov/epstein/doj-disclosures/data-set-{dataset}-files?page=99999")
		page_count = "1"
		page_buttons = self.driver.find_elements(By.CLASS_NAME, 'usa-pagination__button')
		for btn in page_buttons:
			page_count = btn.text
		return int(page_count)

	def download_pdf(self, pdf, output_dir):
		download_options = webdriver.ChromeOptions()
		#download_options.add_argument("--headless") # no
		download_options.add_experimental_option('prefs', {
			"download.default_directory": output,
			"download.prompt_for_download": False,
			"plugins.always_open_pdf_externally": True
		})
		download_options.add_argument("--window-position=-5000,0") # out of bounds
		download_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=download_options)
		try:
			download_driver.minimize_window()
		except:
			pass
		download_complete = False
		max_tries = 10
		while max_tries > 0:
			max_tries -= 1
			try:
				http_GET(self.driver, pdf)
				name = os.path.basename(pdf)
				downloaded_pdf = os.path.join(output, name)
				while not os.path.isfile(downloaded_pdf):
					time.sleep(0.1)
				final_pdf = os.path.join(output_dir, name)
				shutil.move(downloaded_pdf, final_pdf)
				download_complete = True
				break
			except Exception as ignored:
				_ = ignored
				time.sleep(3)
		download_driver.quit()

		if download_complete:
			print(f"{pdf}:OK")
		else:
			print(f"{pdf}:FAILED")
			log_failed(pdf)

	def download_dataset_page(self, dataset, page):
		page_dir = os.path.join(self.output, f"data-set-{dataset}-files", f"{page}")
		if not os.path.isdir(page_dir):
			os.mkdir(page_dir)
		http_GET(self.driver, f"https://www.justice.gov/epstein/doj-disclosures/data-set-{dataset}-files?page={page}")
		pdf_links = [link.get_attribute('href') for link in self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")]
		print(f"pdfs: {len(pdf_links)}")
		for pdf in pdf_links:
			threading.Thread(target=self.download_pdf, args=[pdf, page_dir]).start()
			time.sleep(0.75)

	def download_dataset_pdfs(self, dataset):
		dataset_output = os.path.join(output, f"data-set-{dataset}-files")
		if not os.path.isdir(dataset_output):
			os.mkdir(dataset_output)
		page_count = self.get_dataset_page_count(dataset)
		print(f"dataset: {dataset} page_count: {page_count}")
		i = 0
		while i < page_count:
			self.download_dataset_page(dataset, i)
			i += 1
		self.driver.quit()


class Downloader:
	def __init__(self, output, types, skip_datasets, only_datasets):
		self.skip_datasets = skip_datasets
		self.only_datasets = only_datasets
		self.failed = 0
		self.downloaded = 0
		self.download_options = None
		self.download_driver = None
		self.filetypes = types
		self.output = output
		options = webdriver.ChromeOptions()
		options.add_experimental_option('prefs', {
			"download.default_directory": self.output,
			"download.prompt_for_download": False,
			"plugins.always_open_pdf_externally": True
		})
		self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
		self.download_everything()

		print(f"-- result --")
		print(f"downloaded: {self.downloaded}")
		print(f"failed: {self.failed}")
		self.driver.quit()

	def download_file(self, url, output_dir):
		name = os.path.basename(url)
		final_file = os.path.join(output_dir, name)
		if os.path.isfile(final_file):
			if os.path.getsize(final_file) > 0:
				print(f"skipping existing: {final_file}")
				return
		self.download_options = webdriver.ChromeOptions()
		self.download_options.add_experimental_option('prefs', {
			"download.default_directory": self.output,
			"download.prompt_for_download": False,
			"plugins.always_open_pdf_externally": True
		})
		self.download_options.add_argument("--window-position=-5000,0") # out of bounds
		self.download_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.download_options)
		try:
			self.download_driver.minimize_window()
		except:
			pass
		ok = False
		max_tries = 10
		while max_tries > 0:
			max_tries -= 1
			try:
				http_GET(self.driver, url)
				downloaded_file = os.path.join(self.output, name)
				while not os.path.isfile(downloaded_file):
					time.sleep(0.1)
				shutil.move(str(downloaded_file), final_file)
				ok = True
				break
			except Exception as ignored:
				_ = ignored
				time.sleep(3)
		if ok:
			print(f"{final_file}:OK")
			self.downloaded += 1
		else:
			print(f"{final_file}:FAILED")
			self.failed += 1
		self.download_driver.quit()

	def download_everything(self):
		http_GET(self.driver, "https://www.justice.gov/epstein/doj-disclosures")

		# click all content buttons to show the href's
		buttons = self.driver.find_elements(By.CLASS_NAME, 'usa-accordion__button')
		for button in buttons:
			aria_controls = button.get_attribute("aria-controls")
			if aria_controls and str(aria_controls).startswith("0-"):
				self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
				time.sleep(0.5)
				button.click()

		hrefs = []
		for c in self.driver.find_elements(By.CLASS_NAME, 'usa-accordion__content'):
			links = c.find_elements(By.TAG_NAME, 'a')
			hrefs.extend([link.get_attribute('href') for link in links if link.get_attribute('href')])

		for href in hrefs:
			section_name = os.path.basename(href)

			# skip datasets
			if section_name.startswith("data-set"):
				if self.skip_datasets:
					continue
			elif self.only_datasets:
				continue

			section_dir = os.path.join(self.output, section_name)
			if not os.path.isdir(section_dir):
				os.mkdir(section_dir)
			print(f"saving {section_name} to {section_dir}")
			http_GET(self.driver, href)
			page_count = get_page_count(self.driver, href)
			current_page = 0
			while current_page < page_count:
				page_dir = os.path.join(section_dir, str(current_page))
				if not os.path.isdir(page_dir):
					os.mkdir(page_dir)
				page_url = f"{href}"
				if current_page > 0:
					page_url += f"?page={current_page}"
				http_GET(self.driver, page_url)
				for filetype in self.filetypes:
					file_links = [link.get_attribute('href') for link in self.driver.find_elements(By.XPATH, f"//a[contains(@href, '.{filetype}')]")]
					for file in file_links:
						name = os.path.basename(file)
						final_file = os.path.join(page_dir, name)
						if not os.path.isfile(final_file):
							threading.Thread(target=self.download_file, args=[file, page_dir]).start()
							time.sleep(0.75)
						else:
							print(f"skipping existing: {final_file}")
				current_page += 1



output = "C:\\EPSTEIN\\DOWNLOADS"
if not os.path.isdir(output):
	os.mkdir(output)

print(f"1) everything")
print(f"2) everything except datasets")
print(f"3) all datasets")
print(f"4) custom dataset")
choice = input("What do you want to download:")

if choice == "1":
	print(f"downloading everything")
	Downloader(output, ["pdf"], False, False)
if choice == "2":
	print(f"downloading everything except datasets")
	Downloader(output, ["pdf"], True, False)
if choice == "3":
	print(f"downloading all datasets")
	Downloader(output, ["pdf"], False, True)
if choice == "4":
	choice = input("choose which dataset to download:")
	if choice.isdigit():
		print(f"downloading dataset: {choice}")
		DatasetDownloader(choice, output)


