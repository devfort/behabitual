from django import template
from django.utils.encoding import force_text
from django.contrib.humanize.templatetags.humanize import apnumber

register = template.Library()

@register.simple_tag
def humanize_repetition(habit):
    if hasattr(habit, 'get_resolution_name'):
        resolution_name = force_text(habit.get_resolution_name())
        target_value = habit.target_value
    else:
        resolution_name = habit['resolution']
        target_value = habit['target_value']
    if 1 == target_value:
      return "<em>once</em> a <em>%s</em>" % resolution_name
    elif 2 == target_value:
      return "<em>twice</em> a <em>%s</em>" % resolution_name
    elif 3 == target_value:
      return "<em>%s</em> times a <!-- lady, and I love you --> <em>%s</em>" % (
        apnumber(target_value), resolution_name
    )
    else:
      return "%s times a %s" % (
        apnumber(target_value), resolution_name
    )
