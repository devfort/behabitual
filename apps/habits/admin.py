from django.contrib import admin

from apps.habits.models import Habit


class HabitAdmin(admin.ModelAdmin):
    list_display = ('id', 'resolution', 'start', 'user')
    raw_id_fields = ('user',)


admin.site.register(Habit, HabitAdmin)
