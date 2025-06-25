import pytest

from statblock_extractor import terminates_with_punctuation, remove_end_punctuation, are_combinable, repair_split_words

def test_terminates_with_punctuation():
  assert(terminates_with_punctuation("") == False)
  assert(terminates_with_punctuation("Hi") == False)
  assert(terminates_with_punctuation("Hi ") == False)
  assert(terminates_with_punctuation("Hi. ") == False)
  assert(terminates_with_punctuation("Hi.") == True)
  assert(terminates_with_punctuation("Hi,") == True)
  assert(terminates_with_punctuation("Hi:") == True)
  assert(terminates_with_punctuation("Hi;") == True)
  assert(terminates_with_punctuation("Hi?") == True)
  assert(terminates_with_punctuation("Hi!") == True)
  assert(terminates_with_punctuation("Hi'") == True)
  assert(terminates_with_punctuation("Hi\"") == True)
  assert(terminates_with_punctuation("Hi...") == True)
  assert(terminates_with_punctuation("...") == True)
  assert(terminates_with_punctuation("Hello there") == False)
  assert(terminates_with_punctuation("Hello there.") == True)
  assert(terminates_with_punctuation("Hello, there.") == True)
  assert(terminates_with_punctuation("Hello-there.") == True)

def test_remove_end_punctuation():
  assert(remove_end_punctuation("") == "")
  assert(remove_end_punctuation("Hi") == "Hi")
  assert(remove_end_punctuation("Hi.") == "Hi")
  assert(remove_end_punctuation("Hi,") == "Hi")
  assert(remove_end_punctuation("Hi:") == "Hi")
  assert(remove_end_punctuation("Hi;") == "Hi")
  assert(remove_end_punctuation("Hi?") == "Hi")
  assert(remove_end_punctuation("Hi!") == "Hi")
  assert(remove_end_punctuation("Hi'") == "Hi")
  assert(remove_end_punctuation("Hi\"") == "Hi")
  assert(remove_end_punctuation("Hi...") == "Hi")
  assert(remove_end_punctuation("...") == "")
  assert(remove_end_punctuation("Hello there") == "Hello there")
  assert(remove_end_punctuation("Hello there.") == "Hello there")
  assert(remove_end_punctuation("Hello, there.") == "Hello, there")
  assert(remove_end_punctuation("Hello-there.") == "Hello-there")

def test_are_combinable():
  assert(are_combinable(None, None) == False)
  assert(are_combinable("hi", None) == False)
  assert(are_combinable(None, "hi") == False)
  assert(are_combinable("Hello", "there") == True)
  assert(are_combinable("Hello", "there!") == True)
  assert(are_combinable("Hello", "There") == False)
  assert(are_combinable("Hello", "There!") == False)
  assert(are_combinable("Hello,", "there") == False)
  assert(are_combinable("Hello,", "There") == False)
  assert(are_combinable("hello", "there") == True)
  assert(are_combinable("hello", "there!") == True)
  assert(are_combinable("hello", "There") == False)
  assert(are_combinable("hello", "There!") == False)
  assert(are_combinable("hello,", "there") == False)
  assert(are_combinable("hello,", "There") == False)


def test_repair_split_words():
  assert(repair_split_words("") == "")
  assert(repair_split_words("Hello") == "Hello")
  assert(repair_split_words("Hello!") == "Hello!")
  assert(repair_split_words("Hello, there!") == "Hello, there!")
  assert(repair_split_words("Hello there!") == "Hello there!")

  test_text = "Hello there!"
  for i in range(len(test_text)):
    split_text = test_text[:i] + " " + test_text[i:]
    assert(repair_split_words(split_text) == test_text)

  test_text = "Hi, my name is Jo and I work in a button factory."
  assert(repair_split_words(test_text) == test_text)
