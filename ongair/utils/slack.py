from slacker import Slacker

slack = Slacker('xoxp-13657551446-18943926514-28542309984-38163b7a5b')


def notifyslack(number):
    slack.chat.post_message(
        '#trialnumbers', 'New trial number %s' % (number))

    return None