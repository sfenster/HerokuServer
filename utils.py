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


def count_and_save_words(url):
    errors = []

    try:
        r = requests.get(url)
    except:
        errors.append(
            "Unable to get URL. Please make sure it's valid and try again."
        )
        return {"error": errors}

    # text processing
    raw = BeautifulSoup(r.text, 'html.parser').get_text()
    nltk.data.path.append('./nltk_data/')  # set the path
    tokens = nltk.word_tokenize(raw)
    text = nltk.Text(tokens)

    # remove punctuation, count raw words
    nonPunct = re.compile('.*[A-Za-z].*')
    raw_words = [w for w in text if nonPunct.match(w)]
    raw_word_count = Counter(raw_words)

    # stop words
    no_stop_words = [w for w in raw_words if w.lower() not in stops]
    no_stop_words_count = Counter(no_stop_words)

    # save the results
    try:
        result = Result(
            url=url,
            result_all=raw_word_count,
            result_no_stop_words=no_stop_words_count
        )
        db.session.add(result)
        db.session.commit()
        return result.id
    except:
        errors.append("Unable to add item to database.")
        return {"error": errors}
