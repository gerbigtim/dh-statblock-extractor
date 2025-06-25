"""A module to extract statblocks from the Daggerheart core rulebook
and convert them for use in Obsidian via the Fantasy Statblock Plugin"""

import pymupdf
import unicodedata
import re
import json
import spellchecker
import string
from typing import Dict

import spellchecker.spellchecker

COMMON_CHAR_REPLACEMENTS = {
    0x2018: "'",  # ‘ left single quote
    0x2019: "'",  # ’ right single quote
    0x201C: '"',  # “ left double quote
    0x201D: '"',  # ” right double quote
    0x00A0: ' ',  # non-breaking space
    0x2013: '-',  # en dash
    0x2014: '-',  # em dash
    0x2212: '-',  # minus sign
    0x2022: '*',  # bullet
}



def is_start(li, lines):
  if lines[li].isupper() and lines[li+1].startswith("Tier"):
    return True
  elif lines[li].isupper() and lines[li].endswith(":") and lines[li+1].isupper() and lines[li+2].startswith("Tier"):
    return True
  return False

def get_statblock_lis(lines):
  """Given the text of the page, return a list of tuples (start_line, end_line)
  of the statblocks on the page."""

  statblock_lis = []
  within_statblock = False
  for li, line in enumerate(lines):
    if not within_statblock and is_start(li, lines):
      start_li = li
      within_statblock = True

    if within_statblock and line.isspace():
      end_li = li
      statblock_lis.append((start_li, end_li))
      within_statblock = False

  return statblock_lis

def append_statblock_texts(statblock_texts, page):
  page_text = page.get_text()
  lines = page_text.splitlines()
  statblock_lis = get_statblock_lis(lines)

  for start, end in statblock_lis:
    statblock_texts.append("\n".join(lines[start:end]))

def get_tier(line):
  words = line.split()
  tier_char = words[1][0]
  # Tier is unicode from private range with tier 1 = 0xE541 and incrementing for each tier
  tier = ord(tier_char) - 0xE540
  return tier

def get_weapon(line):
  start_idx = line.index("|") + 2
  end_idx = line.rindex(":")
  return line[start_idx:end_idx]

def get_range(line):
  start_idx = line.rindex(":") + 2
  end_idx = line.rindex("|") - 1
  return line[start_idx:end_idx]

def get_features(li, lines):
  if not lines[li].startswith("FEATURES"):
    raise ValueError(f"Line at index li must be 'Features', is is {lines[li]}.")
  features = []
  name = None
  desc = None
  for li, line in enumerate(lines[li+1:]):
    if re.match(r"^.* [-,—,–] \w*:", line):
      if name and desc:
        features.append({"name": name, "desc": desc})
      name = line[:line.index(":")]
      desc = line[line.index(":")+2:]
    elif li == len(lines) - 1:
      features.append({"name": name, "desc": desc})
    else:
      desc += " " + line
  return features

def print_current_line(li, lines):
  print(f"{li} : {lines[li]}")

def statblock_text_to_dict(statblock_text):
  statblock_dict = {}
  lines = statblock_text.splitlines()
  li = 0

  print(f"Extracting adversary {lines[0]} {lines[1]}")

  name = ""
  while lines[li].isupper():
    name += lines[li] + " "
    li +=1
  statblock_dict['name'] = name.strip().title()

  statblock_dict["tier"] = get_tier(lines[li])
  statblock_dict["type"] = " ".join(lines[li].split()[2:])
  li += 1

  description = ""
  while not lines[li].startswith("Motives & Tactics"):
    description += lines[li] + " "
    li += 1
  statblock_dict['description'] = description.strip()

  moves = lines[li][lines[li].index(":")+2:]
  li+=1
  while not lines[li].startswith("Diff"):
    moves += " " + lines[li]
    li +=1
  statblock_dict['moves'] = moves


  words = lines[li].split()
  statblock_dict["ac"] = words[2]
  statblock_dict["thresholds"] = words[5]
  statblock_dict["hp"] = words[8]
  statblock_dict["stress"] = words[-1]
  li += 1

  words = lines[li].split()
  statblock_dict["atk"] = words[1]
  statblock_dict["weapon"] = get_weapon(lines[li])
  statblock_dict["range"] = get_range(lines[li])
  statblock_dict["dmg"] = " ".join(words[-2:])
  li += 1

  if lines[li].startswith("Experience:"):
    words = lines[li].split()
    experiences = " ".join(words[1:])
    while not lines[li+1].startswith("FEATURES"):
      experiences += " " + lines[li+1]
      li += 1
    statblock_dict["experiences"] = experiences

  if not lines[li].startswith("FEATURES"):
    li += 1

  statblock_dict["features"] = get_features(li, lines)

  return statblock_dict

def terminates_with_punctuation(text: str) -> bool:
  """Returns True if text terminates with punctuation character, else False"""
  return bool(re.match(rf".*[{re.escape(string.punctuation)}]+$", text))

def remove_end_punctuation(text: str) -> str:
  match = re.match(rf"(?P<text>.*?)(?P<punct>[{re.escape(string.punctuation)}]+)$", text)
  if match:
    return match.group("text")
  else:
    return text

def are_combinable(word1: str, word2: str) -> bool:
  """Check if combining 2 words could possibly yield a new word."""
  if (word1 is None) or (word2 is None):
    return False
  if terminates_with_punctuation(word1):
    return False
  if word2.istitle():
    return False
  return True

def combined_more_likely(word1: str, word2: str, wf_dict: Dict) -> bool:
  if not are_combinable(word1, word2):
    return False

  word1 = word1.lower()
  word2 = remove_end_punctuation(word2).lower()
  merged = word1 + word2

  return wf_dict[merged] > min(wf_dict[word1], wf_dict[word2])


def repair_split_words(text: str) -> str:
  spell = spellchecker.SpellChecker()
  wf_dict = spell.word_frequency.dictionary
  words = text.split()
  repaired = []
  word_idx = 0

  last_combined = False
  while word_idx < len(words):
    word_before = words[word_idx - 1] if word_idx > 0 else None
    word_before = repaired[-1] if last_combined else word_before
    word = words[word_idx]
    word_after = words[word_idx] if word_idx + 1 < len(words) else None

    if combined_more_likely(word_before, word, wf_dict):
      repaired[-1] = word_before + word
      last_combined = True
      word_idx += 1
    elif combined_more_likely(word, word_after, wf_dict):
      repaired.append(word + word_after)
      last_combined = True
      word_idx += 2
    else:
      repaired.append(word)
      last_combined = False
      word_idx += 1

  return ' '.join(repaired)

class StatblockScraper:
  """A Scraper for Daggerheart Adversaries"""
  def __init__(self, pdf_path: str, page_range: tuple[int,int] = None):
    self.pdf_path = pdf_path
    self.doc = pymupdf.open(pdf_path)
    self.page_range = page_range
    self.raw_pages = {}
    self.statblocks = []

  def extract_text(self):
    start_idx, end_idx = self.page_range if self.page_range else (0, None)
    print(f"{self.page_range},{start_idx}, {end_idx}")
    for page_num, page in enumerate(self.doc[start_idx: end_idx], start=start_idx):
      self.raw_pages[page_num] = page.get_text()

  def clean_pages(self):
    def clean_unicode_pua_chars(text: str) -> str:
      text = unicodedata.normalize("NFKC", text)
      pua_replacements = {pua_hex: str(digit) for pua_hex, digit in zip(range(0xE540, 0xE550), range(10))}
      text = text.translate(COMMON_CHAR_REPLACEMENTS | pua_replacements)
      return text

    for page_num, page in self.raw_pages.items():
      self.raw_pages[page_num] = clean_unicode_pua_chars(page)

  def normalize_lines(self):
    # split into lines, fix Unicode, strip lines
    pass

  def detect_statblock_start(self, line_idx, lines):
    pass

  def parse_statblock(self, line_idx, lines):
    pass

  def save_to_json(self, path):
    pass






def main():
  Scraper = StatblockScraper("pdfs/Daggerheart_Core_Rulebook-5-20-2025.pdf", page_range=(210,240))
  Scraper.extract_text()
  Scraper.clean_pages()

  print(Scraper.raw_pages[1])






if __name__ == "__main__":
  main()
