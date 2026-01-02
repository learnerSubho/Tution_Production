from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from TeacherPanel.models import *
import calendar
from itertools import zip_longest
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.hashers import check_password
from django.views.decorators.http import require_GET

def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and password are required'
            })

        try:
            student = Student.objects.get(username__iexact=username)
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            })

        if not check_password(password, student.password):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            })

        request.session['student_id'] = student.student_id
        request.session['student_username'] = student.username
        request.session.set_expiry(3600)

        return JsonResponse({
            'status': 'success',
            'message': 'Logged in successfully'
        })

    return render(request, 'Student/student_login.html')

def student_logout(request):
    request.session.flush()
    return redirect('student_login')

def get_logged_in_student(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return None

    try:
        return Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        request.session.flush()
        return None

@require_GET
def student_dashboard(request):
    student = get_logged_in_student(request)

    if not student:
        return redirect('student_login')
    return render(request, 'Student/student_dashboard.html', {
        'student': student,
        'info': Website_Details_For_Easy_Access.objects.first(),
        'dues':student.fees.all().last(),
        'notes':Study_Materials.objects.filter(classname = student.classname, visibility=True, enable_date__gte = student.admission_date).order_by('enable_date')[:2],
        'notice':Notice.objects.all().first(),
        'feescard':FeesRecord.objects.filter(student=student).last(),
    })

@require_GET
def study_materials(request):
    student = get_logged_in_student(request)
    if not student:
        return redirect('student_login')
    
    notes = Study_Materials.objects.filter(classname = student.classname, visibility=True, enable_date__gte = student.admission_date).order_by('enable_date')
    print(student.admission_date)
    print(notes)
    return render(request, 'Student/Notes.html', {
            'student': student,
            'notes': notes,
            'info': Website_Details_For_Easy_Access.objects.first(),
        })

def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


@require_GET
def notes_api(request):
    student = get_logged_in_student(request)
    if not student:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    notes = Study_Materials.objects.filter(classname = student.classname, visibility=True, enable_date__gte = student.admission_date).order_by('enable_date')
    notes_data = []
    for note in notes:
        file_size = 0
        if note.file:
            file_size = format_file_size(note.file.size)

        notes_data.append({
            'id': note.material_id,
            'title': note.title,
            'description': note.description,
            'subject': note.subject,
            'file_name': note.file.name.split('/')[-1] if note.file else '',
            'file_url': note.file.url if note.file else '',
            'file_size': file_size,
            'enable_date': note.enable_date.strftime('%Y-%m-%d'),
        })

    return JsonResponse({'notes': notes_data})


@require_GET
def salarycard(request):
    student = get_logged_in_student(request)
    if not student:
        return redirect('student_login')

    records = FeesRecord.objects.filter(
        student=student,
        paying_month=True
    )

    months = [
        calendar.month_name[m]
        for m in range(student.admission_date.month, date.today().month )
    ]

    paid_month = []
    signatures = []

    for record in records:
        paid_month.append(record.paid_at.strftime("%d-%m-%Y"))
        signatures.append("Paid")

    combined = zip_longest(months, paid_month, signatures, fillvalue="Due")

    return render(request, 'Student/salary_card.html', {
        'combined': combined,
        'student': student,
        'info': Website_Details_For_Easy_Access.objects.first(),
    })

def changepassword(request):
    if request.method == 'POST':
        student = get_logged_in_student(request)
        if not student:
            return redirect('student_login')

        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            return JsonResponse({
                'status': 'error',
                'message': 'Passwords do not match.'
            })

        student.password = make_password(new_password)
        student.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Password changed successfully.'
        })
    return render(request, 'Student/change_password.html')