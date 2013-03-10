from util.render_to_email import render_to_email

def send_email(habit):
    render_to_email(
        text_template='habits/emails/reminder.txt',
        html_template='habits/emails/reminder.html',
        to=(habit.user,),
        subject=habit.description,
        context=dict(description=habit.description),
    )
