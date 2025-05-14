from django.contrib import admin
from .models import CVUpload, Candidate, Job, Match

# Register your models here.
admin.site.register(CVUpload)
admin.site.register(Candidate)
admin.site.register(Job)
admin.site.register(Match)
