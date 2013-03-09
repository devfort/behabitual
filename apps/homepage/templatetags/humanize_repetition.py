from django import template
from django.utils.encoding import force_text
from django.contrib.humanize.templatetags.humanize import apnumber

register = template.Library()

@register.simple_tag
def humanize_repetition(habit):
    resolution_name = force_text(habit.get_resolution_name())
    if 1 == habit.target_value:
      return "once a %s" % resolution_name
    elif 2 == habit.target_value:
      return "twice a %s" % resolution_name
    elif 3 == habit.target_value:
      return "%s times a <!-- lady, and I love you --> %s" % (
        apnumber(habit.target_value), resolution_name
    )
    else:
      return "%s times a %s" % (
        apnumber(habit.target_value), resolution_name
    )
