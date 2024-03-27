import queue
import threading
from time import sleep
from random import random

def worker(q):
    """Worker thread function that processes tasks from the queue."""
    while True:
        try:
            r=random()
            task = q.get(timeout=30)  # Wait for a task with a 3-second timeout
            # Process the task (replace with your actual processing logic)
            sleep(r*20)
            print(f"Processing task: {task}")
            q.task_done()  # Signal completion of the task
        except queue.Empty:
            # No tasks available, potentially exit the thread
            break

# Create a queue to hold tasks
task_queue = queue.Queue()

# Create and start worker threads (adjust the number of threads as needed)
num_workers = 4
for _ in range(num_workers):
    t = threading.Thread(target=worker, args=(task_queue,))
    t.daemon = True  # Make threads daemonic to avoid program hanging
    t.start()

# Add tasks to the queue (replace with your task generation logic)
for task in range(10):
    task_queue.put(task)

# Wait for the queue to be empty and all tasks to be processed
task_queue.join()

print("All tasks completed!")
