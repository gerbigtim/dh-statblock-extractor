"""A module to extract statblocks from the Daggerheart core rulebook
and convert them for use in Obsidian via the Fantasy Statblock Plugin"""

import pymupdf
import unicodedata
import re

def is_start(li, lines):
  while lines[li].isupper():
    li +=1
  return lines[li].startswith("Tier")

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

def statblock_text_to_dict(statblock_text):
  pass





def main():
  page_idxs = range(210,240)

  doc = pymupdf.open("pdfs/Daggerheart_Core_Rulebook-5-20-2025.pdf")
  statblock_texts = []

  for page_idx in page_idxs:
    page = doc[page_idx]
    append_statblock_texts(statblock_texts, page)

  print(statblock_texts[0])
  print(statblock_texts[-3])







if __name__ == "__main__":
  main()
