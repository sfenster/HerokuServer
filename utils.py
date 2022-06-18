import requests
import random

def count_words_at_url(url):
    resp = requests.get(url)
    return len(resp.text.split())

from datetime import datetime, timedelta
import time

def print_task(seconds):
    print("Starting task")
    random_num = random.randrange(1, 3, 1)
    # optional print statement to see the numbers
    # print("the randomly generated number = ", random_num)
    if random_num == 2:
        raise RuntimeError('Sorry, I failed! Let me try again.')
    else:
        for num in range(seconds):
            print(num, ". Hello World!")
            time.sleep(1)
    print("Task completed")

def print_numbers(seconds):
    print("Starting num task")
    for num in range(seconds):
        print(num)
        time.sleep(1)
    print("Task to print_numbers completed")
