from django.http import HttpResponse
from django.shortcuts import render
from TeacherPanel.models import Website_Details_For_Easy_Access,Notice,Gallery
def home(request):
    context = {
        'info': Website_Details_For_Easy_Access.objects.first(),
        'notice': Notice.objects.all().last(),
        'photos':Gallery.objects.all()
    }
    return render(request, 'Public/index.html', context)

def technical_support(request):
    return render(request, 'Public/technical_support.html',{'info': Website_Details_For_Easy_Access.objects.first()})

def faq(request):
    return render(request, 'Public/faq.html',{'info': Website_Details_For_Easy_Access.objects.first()})