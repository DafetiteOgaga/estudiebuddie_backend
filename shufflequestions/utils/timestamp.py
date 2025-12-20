from datetime import datetime

def get_timestamp():
    days = ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
				'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    now = datetime.now()
    return f"@{now.hour}:{now.minute} on {days[now.weekday()]}, {months[now.month - 1]}, {now.day}, {now.year}"
