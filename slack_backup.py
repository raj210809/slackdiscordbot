from collections import deque

backup_queue = deque()


def retrieve():
    priority, item = backup_queue.get()
    return item


def prev_log():
    if backup_queue.empty():
        return 0
    else:
        return 1


def mybackup(timestamp, channel_id, user_id, text, username, channelname):
    item = {
        "channel_id": channel_id,
        "channel_name": channelname,
        "user_id": user_id,
        "user_name": username,
        "timestamp": float(timestamp),
        "text": text,
    }

    # Check if queue is empty or if the new item should be inserted at the front
    if (not backup_queue) or item["timestamp"] < backup_queue[0]["timestamp"]:
        backup_queue.appendleft(item)
    else:
        backup_queue.append(item)
