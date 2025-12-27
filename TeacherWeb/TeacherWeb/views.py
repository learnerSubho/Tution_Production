from django.http import HttpResponse
from django.shortcuts import render
from TeacherPanel.models import Website_Details_For_Easy_Access,Notice
def home(request):
    context = {
        'info': Website_Details_For_Easy_Access.objects.first(),
        'notice': Notice.objects.all().last(),
    }
    return render(request, 'Public/index.html', context)