from django import template
from django.contrib.auth.models import Group

register = template.Library()

#file created to be able to sort user by the group he is in, in template base.html
@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False
