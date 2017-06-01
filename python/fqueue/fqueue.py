# -*- coding: utf-8 -*-
import os
import glob
import logging
import threading
import traceback

logger = logging.getLogger("fqueue")


class FileQueue:
    def __init__(self, path):
        self.path = path
        self.mutex = threading.Lock()
        self.mutex.acquire()
        self.items = []
        try:
            logger.info("initializing FileQueue at {}".format(self.path))
            if not os.path.isdir(self.path):
                os.makedirs(self.path)
            self.items = [os.path.basename(file)[:5] for file in glob.glob(self.path + "/*.que")]
            self.items.sort()
            logger.debug("loaded items: {}".format(self.items))
        except Exception:
            logger.error(traceback.format_exc())
            raise Exception("cannot initialize FileQueue at \'{}\'".format(self.path))
        finally:
            self.mutex.release()

    def length(self):
        self.mutex.acquire()
        try:
            return len(self.items)
        except Exception:
            logger.error(traceback.format_exc())
            raise Exception("cannot get FileQueue length")
        finally:
            self.mutex.release()

    def head(self):
        self.mutex.acquire()
        try:
            if len(self.items) > 0:
                logger.debug("head item: {}".format(self.items[0]))
                with open(self.__filename(self.items[0]), "r") as file:
                    return file.read()
            return None
        except Exception:
            logger.error(traceback.format_exc())
            raise Exception("cannot get head item")
        finally:
            self.mutex.release()

    def pop(self):
        self.mutex.acquire()
        try:
            text = None
            if len(self.items) > 0:
                logger.debug("pop item: {}".format(self.items[0]))
                with open(self.__filename(self.items[0]), "r") as file:
                    text = file.read()
                os.remove(self.__filename(self.items[0]))
                self.items.pop(0)
            return text
        except Exception:
            logger.error(traceback.format_exc())
            raise Exception("cannot pop item")
        finally:
            self.mutex.release()

    def push(self, text):
        self.mutex.acquire()
        try:
            tail = -1
            if len(self.items) > 0:
                last_item = self.items[len(self.items) - 1]
                tail = int(last_item)
            item = "{0:05d}".format(tail + 1)
            logger.debug("push item: {}".format(item))
            with open(self.__filename(item), "w") as file:
                file.write(text)
            self.items.append(item)
        except Exception:
            logger.error(traceback.format_exc())
            raise Exception("cannot push item")
        finally:
            self.mutex.release()

    def __filename(self, item):
        return self.path + "/" + item + ".que"

#######################################################


TEST_PATH = "test_queue"
NUM_ITEMS = 50


def test_enqueue(num_items):
    queue = FileQueue(TEST_PATH)
    length = queue.length()
    for i in range(length, length + num_items):
        queue.push("{0:05d}".format(i))
    queue = None


def test_dequeue(first_item=0, num_items=-1):
    queue = FileQueue(TEST_PATH)
    counter = 0
    while num_items < 0 or counter < num_items:
        item = queue.pop()
        if not item:
            break
        found = int(item)
        if counter + first_item != found:
            raise Exception("expected: {}, found: {}".format(counter + first_item, found))
        counter = counter + 1
    if num_items < 0 and (queue.head() or queue.length() > 0):
        raise Exception("queue must be empty")
    queue = None


if __name__ == "__main__":
    logger.info("testing...")
    test_enqueue(num_items=NUM_ITEMS)
    test_enqueue(num_items=NUM_ITEMS)
    test_dequeue(first_item=0)
    test_enqueue(num_items=NUM_ITEMS)
    test_enqueue(num_items=NUM_ITEMS)
    test_dequeue(first_item=0, num_items=NUM_ITEMS)
    test_dequeue(first_item=NUM_ITEMS, num_items=NUM_ITEMS)
    logger.info("testing done.")
logger.info("bye")
print("bye")
