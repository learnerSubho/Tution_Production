from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from . import models
from datetime import date
from django.db.models import When, Case, IntegerField, F, Count, Sum, Min
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, get_user_model
import random
from django.core.mail import send_mail
from django.contrib.auth import update_session_auth_hash
import calendar
from itertools import zip_longest
import numpy as np
from PIL import Image
import io
from django.core.files.base import ContentFile
from firebase_admin import messaging
from django.shortcuts import get_object_or_404

# Compressing Image
def compressed_image(image, max_width=800, quality=30):
    img = Image.open(image)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(float(img.height) * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    buffer = io.BytesIO()
    
    # Save compressed image to buffer
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)

    # Return file in Django-compatible format
    return ContentFile(buffer.read(), name=image.name)

# def compress_attachment()

# Starting of LOGIN Functionality 
def loginpage(request):
    '''Renders the login page for teachers.'''
    info = models.Website_Details_For_Easy_Access.objects.first()
    return render(request,'Teacher/login.html',{'info':info})

def send_otp_mail(request,user):
    otp = random.randint(100000,999999)
    request.session['otp'] = otp
    request.session['temp_user'] = user.id
    try:       
        send_mail(
        'Your Login OTP',
        f'Your verification code is {otp}. It will expire in 5 minutes.',
        'subhojitghosh988340@gmail.com',
        [user.email]
        )
        return JsonResponse({'status':'success','message':'OTP sent to registered mail'})
    except Exception as e:
        return JsonResponse({'status':'error','message':f'Unable to sent OTP {e}'})
    
def login_to(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username,password=password)
        if user is not None:
            if user.is_staff:
                # login(request,user)
                return send_otp_mail(request,user)
            else:
                return JsonResponse({'status':'error','message':'Access Denied'})
        else:
            return JsonResponse({'status':'error','message':'Invalid Username and Password'})
    return JsonResponse({'status':'error','message':'Oops!'})

@login_required(login_url='/teacher/loginpage/')
def logout_view(request):
    logout(request)
    return JsonResponse({'status':'success','message':'Logged out...'})


User = get_user_model()

def otpverify(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = str(request.session.get('otp'))
        user_id = request.session.get('temp_user')
        
        if entered_otp and stored_otp and user_id:
            if entered_otp == stored_otp:
                try:
                    user = User.objects.get(id = user_id)
                    login(request,user)
                    return JsonResponse({'status':'success','message':'Logged in successfully'})
                except Exception as e:
                    return JsonResponse({'status':'error','message':str(e)})
            else:
                return JsonResponse({'status':'error','message':'OTP Mismatch'})
        else:
            return JsonResponse({'status':'error','message':'Unable to fetch OTP'})
    else:
        return JsonResponse({'status':'error','message':'Unable to fetch OTP'})

@login_required(login_url='/teacher/loginpage/')
def ChangePassword(request):
    '''Responsible for changing password of logged in user'''
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            return JsonResponse({'status':'error','message':'Wrong Old Password'})
        if new_password != confirm_password:
            return JsonResponse({'status':'error','message':'New and Confirm Passwords do not match'})
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request,request.user)
            return JsonResponse({'status':'success','message':'Password Changed Successfully'})
        
    return render(request,'Teacher/ChangePassword.html')

# End of LOGIN Functionality

#General Requirements
@login_required(login_url='/teacher/loginpage/')
def dashboard(request):
    '''Renders the dashboard page for teachers.'''
    due=0
    for student in models.Student.objects.all():
        due = student.fees.first().due_months[2]+student.fees.first().due_months[3]
    return render(request,'Teacher/dashboard.html',{'info':models.Website_Details_For_Easy_Access.objects.first(),'std_count':models.Student.objects.all().count(),'due':due})

@login_required(login_url='/teacher/loginpage/')
def StudentManagment(request):
    '''Renders the student management page for teachers.'''
    classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    cases = [When(classname__classname=name, then=idx + 1) for idx, name in enumerate(classes)]
    students = models.Student.objects.all().annotate(
        class_order = Case(*cases, default=99, output_field=IntegerField())
    ).order_by('class_order','student_id')
    
    cases = [When(classname=name, then=idx + 1) for idx, name in enumerate(classes)]
    ordered_class = models.Classname.objects.all().annotate(
        class_order = Case(*cases, default=99, output_field=IntegerField())
    ).order_by('class_order')
    batches = models.Batch.objects.all()
    context ={
        'students':students,
        'count':students.count(),
        'classes':ordered_class,
        'batches':batches,
        'info':models.Website_Details_For_Easy_Access.objects.first()
    }
    return render(request,'Teacher/StudentManagement.html',context)

@login_required(login_url='/teacher/loginpage/')
def get_batches(request,class_id):
    '''Returns all the batch information'''
    batches_info = models.Batch.objects.filter(classname = class_id).values('batch_id','batch_name')
    batches = [{'id':b['batch_id'],'name':b['batch_name']}for b in batches_info]
    return JsonResponse ({'batches':batches})

#End Of General Requirements

# Starting Of Class ADD, DELETE, EDIT View

@login_required(login_url='/teacher/loginpage/')
def AddClasses(request):
    '''Renders the add classes page for teachers.'''
    if request.method == 'POST':
        classname = request.POST.get('className')
        fees = request.POST.get('feesPerMonth')
        if classname and fees:
            models.Classname.objects.create(
                classname=classname,
                fees=fees
            )
            return JsonResponse({'status':'success','message':'Class added successfully'})
        else:
            return JsonResponse({'status':'error','message':'Invalid data'})
    class_ordering = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    cases = [When(classname=name, then=idx+1) for idx, name in enumerate(class_ordering)]
    classes = models.Classname.objects.all().annotate(class_order = Case(*cases, default=99, output_field=IntegerField())).order_by('class_order')
    return render(request,'Teacher/add_classes.html',{'classes':classes,'info':models.Website_Details_For_Easy_Access.objects.first()})

@login_required(login_url='/teacher/loginpage/')
def DeleteClass(request,class_id):
    '''Deletes a class based on the provided class ID.'''
    classname = models.Classname.objects.get(class_id=class_id)
    if classname:
        classname.delete()
        return JsonResponse({'status':'success','message':'Class deleted successfully'})
    else:
        return JsonResponse({'status':'error','message':'Class not found'})

@login_required(login_url='/teacher/loginpage/')
def EditClass(request,class_id):
    '''Edits a class based on the provided class ID.'''
    classname = models.Classname.objects.get(class_id=class_id)
    if request.method == 'POST':
        new_classname = request.POST.get('className')
        new_fees = request.POST.get('feesPerMonth')
        if new_classname and new_fees:
            try:
                class_obj = models.Classname.objects.get(class_id=class_id)
                class_obj.classname = new_classname
                class_obj.fees = new_fees
                class_obj.save()
                return JsonResponse({'status':'success','message':'Class updated successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message': str(e)})
        else:
            return JsonResponse({'status':'error','message':'Invalid data'})
    return JsonResponse({'status':'error','message':'Invalid data'})

# End Of Class ADD, DELETE, EDIT Views

#Starting Of Batch ADD, EDIT, DELETE Views
@login_required(login_url='/teacher/loginpage/')
def AddBatchs(request):
    '''This function is responsible for Adding new batch'''
    if request.method == 'POST':
        classname = request.POST.get('className')
        batch_name = request.POST.get('batchName')
        if classname and batch_name:
            try:
                class_obj = models.Classname.objects.get(class_id = classname)
                models.Batch.objects.create(
                    classname = class_obj,
                    batch_name = batch_name
                )
                return JsonResponse({'status':'success','message':'Batch added successfully'})
            except Exception as e:
                return JsonResponse({'status':'Error','message':str(e)})
        else:
            return JsonResponse({'status':'Error','message':'Entered Invalid Data'})
    classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    cases = [When(classname = name, then=idx+1) for idx,name in enumerate(classes)]
    Ordered_Classes = models.Classname.objects.all().annotate(
        class_order = Case(*cases,default=99,output_field=IntegerField())
    ).order_by('class_order')
    cases = [When(classname__classname = name, then=idx+1) for idx,name in enumerate(classes)]
    batchs = models.Batch.objects.all().annotate(class_order = Case(*cases,default=99,output_field=IntegerField())).order_by('class_order')
    context={
        'classes':Ordered_Classes,
        'batchs':batchs,
        'count':batchs.count(),
        'info':models.Website_Details_For_Easy_Access.objects.first()
    }
    return render(request,'Teacher/add_batch.html',context)

@login_required(login_url='/teacher/loginpage/')
def EditBatch(request,batch_id):
    '''This function is responsible for edit a batch details'''
    if request.method == 'POST':
        new_classname = request.POST.get('className')
        new_batch_name = request.POST.get('batchName')
        if new_batch_name and new_classname:
            try:
                batch_obj = models.Batch.objects.get(batch_id=batch_id)
                batch_obj.classname = models.Classname.objects.get(class_id=new_classname)
                batch_obj.batch_name = new_batch_name
                batch_obj.save()
                return JsonResponse({'status':'success','message':'Batch Edited Successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message':str(e)})
        else:
            return JsonResponse({'status':'error','message':'Entered Invalid Data'})
    return JsonResponse({'status':'error','message':'Something went wrong'})

@login_required(login_url='/teacher/loginpage/')
def DeleteBatch(request,batch_id):
    '''This function is responsible to delete a specific batch'''
    try:
        batch = models.Batch.objects.get(batch_id = batch_id)
        batch.delete()
        return JsonResponse({'status':'success','message':'Deleted Successfully'})
    except Exception as e:
        return JsonResponse({'status':'error','message':str(e)})

# Starting of Student ADD,DELETE,EDIT PROMOTE, FEES, RECORD PAYMENT Views

@login_required(login_url='/teacher/loginpage/')
def AddStudent(request):
    '''Renders the add student page for teachers.'''
    if request.method == 'POST':
        studentname = request.POST.get('studentName')
        fathername = request.POST.get('fatherName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        classname = request.POST.get('className')
        batch = request.POST.get('batchName')
        photo = request.FILES.get('photo',None)
        
        if studentname and fathername and email and phone and address and classname:
            try:
                student = models.Student.objects.create(
                    studentname=studentname,
                    fathername=fathername,
                    email=email,
                    phone=phone,
                    address=address,
                    classname=models.Classname.objects.get(class_id=classname),
                    batch = models.Batch.objects.get(batch_id = batch),
                    photo=compressed_image(photo),
                    admission_date = date(2025,1,1)
                )
                models.FeesRecord.objects.create(
                    student = student,
                    fees = 0.00,
                    remark = 'Admission',
                    mode = 'Other',
                    paid_at = date(2025,5,5)
                )
                return JsonResponse({'status':'success','message':'Student added successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message': str(e)})
        else:
            return JsonResponse({'status':'Falied','message':'Fill all the required details.'})
    return JsonResponse({'status':'error','message':'Something went wrong'})

@login_required(login_url='/teacher/loginpage/')
def DeleteStudent(request,student_id):
    '''Deletes a student based on the provided student ID'''
    student = models.Student.objects.get(student_id=student_id)
    if student:
        try:
            student.delete()
            return JsonResponse({'status':'success','message':'Student deleted successfully'})
        except Exception as e:
            return JsonResponse({'status':'error','message': str(e)})
    else:
        return JsonResponse({'status':'error','message':'Student not found'})

@login_required(login_url='/teacher/loginpage/')   
def EditStudent(request,student_id):
    '''Edits a student based on the provided student ID'''
    if request.method == 'POST':
        studentname = request.POST.get('studentName')
        fathername = request.POST.get('fatherName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        classname = request.POST.get('className')
        batch = request.POST.get('batchName')
        photo = request.FILES.get('photo',None)
        
        if studentname and fathername and email and phone and address and classname:
            try:
                student = models.Student.objects.get(student_id=student_id)
                student.studentname = studentname
                student.fathername = fathername
                student.email = email
                student.phone = phone
                student.address = address
                student.classname = models.Classname.objects.get(class_id=classname)
                student.batch = models.Batch.objects.get(batch_id = batch)
                if photo:
                    student.photo = photo
                student.save()
                return JsonResponse({'status':'success','message':'Student updated successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message': str(e)})
        else:
            return JsonResponse({'status':'error','message':'Fill all the required details.'})
    return JsonResponse({'status':'error','message':'Somthing went wrong.'})

# End of Student ADD,DELETE,EDIT PROMOTE, FEES, RECORD PAYMENT Views

@login_required(login_url='/teacher/loginpage/')
def PromoteStudent(request):
    '''Renders the promote student page for teachers.'''
    classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    cases = [When(classname=name, then=idx+1) for idx,name in enumerate(classes)] 
    ordered_class = models.Classname.objects.annotate(
        class_order = Case(*cases,default=99, output_field=IntegerField())
    ).order_by('class_order')
    students = models.Student.objects.all()
    context={
        'students':students,
        'count':students.count(),
        'ordered_class':ordered_class,
        'info':models.Website_Details_For_Easy_Access.objects.first()
    }
    return render(request,'Teacher/PromoteStudent.html',context)

@login_required(login_url='/teacher/loginpage/')
def promote(request,id):
    if request.method == 'POST':
        student = models.Student.objects.get(student_id = id)
        fees_obj = student.fees.all().last()
        year_outstanding = fees_obj.due_months[2]+fees_obj.due_months[3]
        print(year_outstanding)
        classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
        try:
            next_class = classes[classes.index(student.classname.classname)+1]
        except Exception as e:
            return JsonResponse({'status':'Error','message':str(e)})
        models.Batch.objects.get_or_create(classname = models.Classname.objects.get(classname=next_class),batch_name=student.batch.batch_name)
        student.classname = models.Classname.objects.get(classname=next_class)
        student.batch = models.Batch.objects.get(classname=student.classname,batch_name=student.batch.batch_name)
        student.year_outstanding = year_outstanding
        student.admission_date = datetime(2025,11,3)
        fees = models.FeesRecord.objects.filter(student=student)
        for fee in fees:
            models.rescuedFeesRecord.objects.create(
                student_name = student.studentname,
                father_name = student.fathername,
                phone = student.phone,
                paid_at = fee.paid_at,
                remark = fee.remark,
                mode = fee.mode,
                fees = fee.fees,
                total_fees = fee.total_fees,
                paying_month = fee.paying_month,
                how_many_month = fee.how_many_month
            )
        fees.delete()
        models.FeesRecord.objects.create(
            student = student,
            fees = 0.00,
            remark = 'Admission',
            mode = 'Other',
            paid_at = date(2025,11,5)
        )
        student.save()
        return JsonResponse({'status':'success','message':f'Student {student.studentname} promoted to next class {student.classname.classname}'})

# Start of Fees Management
@login_required(login_url='/teacher/loginpage/')
def Fees(request):
    '''Renders the fees page for teachers.'''
    classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    cases = [When(classname = name, then=idx+1) for idx,name in enumerate(classes)]
    Ordered_Classes = models.Classname.objects.all().annotate(
        class_order = Case(*cases,default=99,output_field=IntegerField())
    ).order_by('class_order')
    context = {
        'classes': Ordered_Classes,
        'students':models.Student.objects.all().order_by('studentname'),
        'info':models.Website_Details_For_Easy_Access.objects.first()
    }
    return render(request,'Teacher/Fees.html',context)

@login_required(login_url='/teacher/loginpage/')
def RecordPayment(request,student_id):
    '''Renders the record payment page for teachers.'''
    if request.method == 'POST':
        fees = request.POST.get('fees')
        mode = request.POST.get('paymentMode')
        remark = request.POST.get('remarks')
        
        if fees:
            try:
                models.FeesRecord.objects.create(
                    student = models.Student.objects.get(student_id=student_id),
                    fees = fees,
                    remark = remark,
                    mode = mode
                )
                return JsonResponse({'status':'success','message':'Recorded Successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message':str(e)})
        else:
            return JsonResponse({'status':'error','message':'Fill all required fields'})
            
    context = {
        'student': models.Student.objects.get(student_id=student_id),
        'info':models.Website_Details_For_Easy_Access.objects.first()
    }
    return render(request,'Teacher/RecordPayment.html',context)

@login_required(login_url='/teacher/loginpage/')
def transactions(request,student_id):
    student = models.Student.objects.get(student_id = student_id)
    all_records = student.fees.all()
    context={
        'student':student,
        'all_records': all_records.order_by('-paid_at','-fees_id')
    }
    return render(request,'Teacher/transactions.html',context)

@login_required(login_url='/teacher/loginpage/')
# def salarycard(request, student_id):
#     # 1. Fetch student safely (same logic, safer failure)
#     student = get_object_or_404(models.Student, student_id=student_id)
#     records = models.FeesRecord.objects.filter(
#         student=student,
#         paying_month=True
#     )
#     months = [
#         calendar.month_name[m]
#         for m in range(student.admission_date.month, date.today().month)
#     ]
#     paid_month = []
#     signatures = []

#     for record in records:
#         paid_month.append(record.paid_at.strftime("%d-%m-%Y"))
#         signatures.append("Paid")
        
#     combined = zip_longest(months, paid_month, signatures, fillvalue='Due')

#     context = {
#         'combined': combined,
#         'student': student,
#         'info': models.Website_Details_For_Easy_Access.objects.first(),
#     }

#     return render(request, 'Teacher/salary_card.html', context)

@login_required(login_url='/teacher/loginpage/')
# def salarycard(request, student_id):
#     student = get_object_or_404(models.Student, student_id=student_id)
#     full_month_paid_id = models.FeesRecord.objects.filter(student=student, paying_month=True)
#     for record in full_month_paid_id:
#         record.how_many_month

def salarycard(request,student_id):
    student = models.Student.objects.get(student_id=student_id)
    full_month_paid_id = models.FeesRecord.objects.filter(student=student,paying_month=True).values_list('fees_id',flat=True)
    month = ['January','February','March','April','May','June','July','August','September','October','November','December']
    bw = (date.today() - student.admission_date).days//30
    print(bw)
    months = []
    admission = month.index(calendar.month_name[student.admission_date.month])
    for i in range(bw):
        months.append(month[(admission + i)%12])
    paid_month = []
    signatures = []
    for id in full_month_paid_id:
        record = models.FeesRecord.objects.get(fees_id=id)
        for num in range(record.how_many_month):
            paid_month.append(record.paid_at.strftime("%d-%m-%Y"))
            signatures.append(1)
    print(paid_month)
    print(signatures)
    # print(full_month_paid_id)
    combined = zip_longest(months,paid_month,signatures,fillvalue='Due')
    context={'combined':combined,
             'info':models.Website_Details_For_Easy_Access.objects.first(),
             'student':student}
    return render(request,'Teacher/salary_card.html',context)
# End of the Fees Management

@login_required(login_url='/teacher/loginpage/')
def Notes(request):
    '''Renders the notes page for teachers.'''
    if request.method == 'POST':
        title = request.POST.get('title')
        classname = request.POST.get('className')
        subject = request.POST.get('subject')
        document = request.FILES.get('document')
        visible = request.POST.get('visible') == 'true'
        description = request.POST.get('description','')
        
        if title and classname and subject and document:
            try:
                models.Study_Materials.objects.create(
                    title = title,
                    classname = models.Classname.objects.get(class_id=classname),
                    subject = subject,
                    file = document,
                    visibility = visible,
                    description = description,
                    enable_date = date.today() if visible else None
                )
                return JsonResponse({'status':'success','message':'Material added successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message': str(e)})
        else:
            return JsonResponse({'status':'error','message':'Fill all the required details.'})
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            print(material_id)

            material = models.Study_Materials.objects.get(material_id=material_id)
            material.delete()

            return JsonResponse({'status': 'success', 'message': 'Material deleted successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    elif request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            visibility = data.get('visible')
            print(material_id,visibility)
            material = models.Study_Materials.objects.get(material_id=material_id)
            material.visibility = visibility
            material.enable_date = date.today() if visibility else None
            material.save()
            return JsonResponse({'status':'success','message':'Material visibility updated successfully'})
        except Exception as e:
            return JsonResponse({'status':'error','message': str(e)})
    classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    cases = [When(classname=name , then = idx+1) for idx,name in enumerate(classes)]
    models_list = models.Classname.objects.all().annotate(
            class_order = Case(*cases, default=99, output_field=IntegerField())
        ).order_by('class_order')
    return render(request,'Teacher/Notes.html',{'classes':models_list,'info':models.Website_Details_For_Easy_Access.objects.first()})

def materials_api(request):
    materials = models.Study_Materials.objects.all().order_by('upload_date')

    data = []
    for m in materials:
        data.append({
            "id": m.material_id,
            "title": m.title,
            "className": m.classname.classname,
            "subject": m.subject,
            "documentName": m.file.name.split('/')[-1],
            "documentURL": m.file.url,
            "documentSize": f"{round(m.file.size / 1024 / 1024, 2)} MB",
            "visible": m.visibility,
        })

    return JsonResponse(data, safe=False)

@login_required(login_url='/teacher/loginpage/')
def OnlineClass(request):
    '''Renders the online class page for teachers.'''
    
    if request.method == 'POST':
        classname = request.POST.get('className')
        batch = request.POST.get('batchName')
        class_date = request.POST.get('classDate')
        time = request.POST.get('classTime')
        meet_link = request.POST.get('meetLink')
        subject = request.POST.get('subject')
        
        if classname and class_date and time and meet_link and subject:
            try:
                class_obj = models.Classname.objects.get(class_id=classname)
                if batch:
                    batch_obj = models.Batch.objects.get(batch_id=batch)
                else:
                    batch_obj = None
                models.Online_Class_Link.objects.create(
                    classname = class_obj,
                    batch = batch_obj,
                    class_date = class_date,
                    time = time,
                    class_link = meet_link,
                    subject = subject
                )
                return JsonResponse({'status':'success','message':'Online class link added successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message': str(e)})
        else:
            return JsonResponse({'status':'error','message':'Fill all the required details.'})
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            class_link_id = data.get('class_link_id')
            class_link = models.Online_Class_Link.objects.get(class_link_id=class_link_id)
            class_link.delete()
            return JsonResponse({'status':'success','message':'Class link deleted successfully'})
        except Exception as e:
            return JsonResponse({'status':'error','message': str(e)})
    classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    cases = [When(classname=name , then = idx+1) for idx,name in enumerate(classes)]
    ordered_class = models.Classname.objects.all().annotate(
            class_order = Case(*cases, default=99, output_field=IntegerField())
        ).order_by('class_order')
    return render(request,'Teacher/Link-upload.html',{'classes':ordered_class,'online_classes':models.Online_Class_Link.objects.all().order_by('-class_date','-time'),'info':models.Website_Details_For_Easy_Access.objects.first()})

@login_required(login_url='/teacher/loginpage/')
def Expenditure(request):
    '''Renders the expenditure page for teachers.'''
    return render(request,'Teacher/Expenditure.html')

#Starting Of Notice Management like ADD,EDIT,DELETE
@login_required(login_url='/teacher/loginpage/')
def AddNotice(request):
    '''Renders the notice page for teachers.'''
    if request.method == 'POST':
        notice_instraction = request.POST.get('notice_instraction')
        notice_photo = request.FILES.get('notice_photo',None)
        if notice_instraction:
            try:
                models.Notice.objects.all().delete()
                models.Notice.objects.create(
                    notice_instraction = notice_instraction,
                    notice_photo = compressed_image(notice_photo)
                )
                return JsonResponse({'status':'success','message':'Notice uploaded successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message': str(e)})
        else:
            return JsonResponse({'status':'error','message':'Invalid Data'})
    context = {
        'notices':models.Notice.objects.all().order_by('-notice_date'),
        'count':models.Notice.objects.all().count(),
        'info':models.Website_Details_For_Easy_Access.objects.first()
    }
    return render(request,'Teacher/Notice.html',context)

@login_required(login_url='/teacher/loginpage/')
def EditNotice(request,notice_id):
    '''This function is responsible for edit an existing notice'''
    if request.method == 'POST':
        new_notice_instruction = request.POST.get('notice_instraction')
        new_notice_photo = request.FILES.get('notice_photo',None)
        if new_notice_instruction:
            try:
                notice = models.Notice.objects.get(notice_id = notice_id)
                notice.notice_instraction = new_notice_instruction
                notice.notice_photo = new_notice_photo
                notice.save()
                return JsonResponse({'status':'success','message':'Notice Updated Successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message':'Exception'+str(e)})
        else:
            return JsonResponse({'status':'error','message':'Invalid data'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required(login_url='/teacher/loginpage/')
def DeleteNotice(request,notice_id):
    try:
        notice = models.Notice.objects.get(notice_id=notice_id)
        notice.delete()
        return JsonResponse({'status':'success','message':'Notice Deleted Successfully'})
    except Exception as e:
        return JsonResponse({'status':'error','message':'Unable to delete notice: '+str(e)})

#End of the Notice
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
@login_required(login_url='/teacher/loginpage/')
def Routine(request):
    '''Renders the routine page for teachers.'''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            class_id = data.get('class')
            batch = data.get('batch')
            days_per_week = data.get('daysPerWeek')
            days = data.get('days',[])
            if not class_id or not days:
                return JsonResponse({'status':'error','message':'Class and Days are required'})
            
            try:
                classname = models.Classname.objects.get(class_id=class_id)
            except models.Classname.DoesNotExist:
                return JsonResponse({'status':'error','message':'Class not found'})
            
            try:
                batch = models.Batch.objects.get(batch_id=batch)
            except models.Batch.DoesNotExist:
                return JsonResponse({'status':'error','message':'Batch not found'})
            
            for d in days:
                day_name = d.get('day')
                subjects = d.get('subject')
                time = d.get('time')
                
                try:
                    if '-' in time:
                        start_str, end_str = [t.strip() for t in time.split('-')]
                    else:
                        start_str, end_str = time.strip(), time.strip()

                    start_time = datetime.strptime(start_str, "%I:%M %p").time()
                    end_time = datetime.strptime(end_str, "%I:%M %p").time()
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid time format'})

                models.RoutineEntry.objects.update_or_create(
                    classname=classname,
                    batch=batch,
                    day_of_week = days_per_week,
                    day_name=day_name,
                    subject=subjects,
                    start_time=start_time,
                    end_time=end_time
                )
            return JsonResponse({'status':'success','message':'Routine updated successfully'})   
                    
        except Exception as e:
            return JsonResponse({'status':'error','message':str(e)})
    
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            entry_id = data.get('id')

            if not entry_id:
                return JsonResponse({'status': 'error', 'message': 'No ID provided'})

            try:
                entry = models.RoutineEntry.objects.get(entry_id=entry_id)
                entry.delete()
                return JsonResponse({'status': 'success', 'message': 'Routine deleted successfully'})
            except models.RoutineEntry.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Routine not found'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            entry_id = data.get('id')
            day_info = data.get('days',[])
            if not entry_id:
                return JsonResponse({'status':'error','message':'Unable to fetch data'})
            try:
                day_det = day_info[0]
                day_name = day_det.get('day')
                subject = day_det.get('subject')
                start_time = day_det.get('time')
            except Exception as e:
                return JsonResponse({'status':'error','message':str(e)})
            try:
                entry = models.RoutineEntry.objects.get(entry_id=entry_id)
                entry.day_name = day_name
                entry.subject = subject
                entry.start_time = datetime.strptime(start_time, "%I:%M %p").time()
                entry.save()
                return JsonResponse({'status':'success','message':'Routine updated successfully'})
            except Exception as e:
                return JsonResponse({'status':'error','message':str(e)})
        except Exception as e:
            return JsonResponse({'status':'error','message':str(e)})
    
    elif request.method == 'GET':
        routines = models.RoutineEntry.objects.all()
        data = []
        for routine in routines:
            data.append({
                'id':routine.entry_id,
                'class':routine.classname.classname,
                'batch':routine.batch.batch_name,
                'day_of_week':routine.day_of_week,
                'days':[
                    {
                        'day':routine.day_name,
                        'subject':routine.subject,
                        'time':f"{routine.start_time.strftime('%I:%M %p')}"
                    }
                ]
            })
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'routines': data})
        
        classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
        cases = [When(classname=name , then = idx+1) for idx,name in enumerate(classes)]
        ordered_class = models.Classname.objects.all().annotate(
            class_order = Case(*cases, default=99, output_field=IntegerField())
        ).order_by('class_order')
        
        return render(request,'Teacher/Routine.html',{'classes':ordered_class,'info':models.RoutineEntry.objects.first(),'routines':data})

def grid_routine(request):
    '''Renders the grid routine page for teachers.'''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            day_name = data.get('day')
            subject = data.get('activity')
            start_time = data.get('time')
            models.RoutineEntry.objects.create(
                day_name=day_name,
                subject=subject,
                start_time=datetime.strptime(start_time, "%I:%M %p").time()
            )
            return JsonResponse({'status':'success','message':'Routine added successfully'})
        except Exception as e:
            return JsonResponse({'status':'error','message': str(e)})
    
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            day_name = data.get('day')
            start_time = data.get('time')
            entry = models.RoutineEntry.objects.filter(day_name=day_name,start_time=datetime.strptime(start_time, "%I:%M %p").time())
            entry.delete()
            return JsonResponse({'status':'success','message':'Deleted Successfully'})
        except Exception as e:
            return JsonResponse({'status':'Error','message':str(e)})
        
    records = models.RoutineEntry.objects.all()
    times = ['07:00 AM', '07:30 AM', '08:00 AM', '08:30 AM', '09:00 AM', '09:30 AM',
            '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM',
            '01:00 PM', '01:30 PM', '02:00 PM', '02:30 PM', '03:00 PM', '03:30 PM',
            '04:00 PM', '04:30 PM', '05:00 PM', '05:30 PM', '06:00 PM', '06:30 PM',
            '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM', '09:00 PM']
    
    grid_record = [["" for _ in range(len(times))] for _ in range(7)]
    for record in records:
        time_str = record.start_time.strftime("%I:%M %p")
        if time_str in times:
            time_index = times.index(time_str)
            day_index = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'].index(record.day_name)
            grid_record[day_index][time_index] = record.subject
    return render(request,'Teacher/gridroutine.html',{'grid_record':grid_record,'info':models.Website_Details_For_Easy_Access.objects.first()})

@login_required(login_url='/teacher/loginpage/')
def chart_collection(request):
    min_admission_date = models.Student.objects.aggregate(
        earliest=Min('admission_date')
    )['earliest']

    if not min_admission_date:
        return JsonResponse({'months': [], 'month_wise_collection': []})

    start_month = min_admission_date.month
    end_month = date.today().month

    if start_month > end_month:
        start_month = 1   # prevent empty range

    months = []
    collections = []

    for month in range(start_month, end_month + 1):
        months.append(calendar.month_abbr[month])

        total = models.FeesRecord.objects.filter(
            paid_at__month=month
        ).aggregate(sum_fees=Sum('fees'))['sum_fees'] or 0
        collections.append(total)
    print(months, collections)
    return JsonResponse({
        'months': months,
        'month_wise_collection': collections
    })
@login_required(login_url='/teacher/loginpage/') 
def doughnut_chart(request):
    try:
        class_names = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
        cases = [When(classname=name , then = idx+1) for idx,name in enumerate(class_names)]
        classes = models.Classname.objects.annotate(
            class_order=Case(*cases, default=99, output_field=IntegerField())
        ).order_by('class_order')

        class_names = [cls.classname for cls in classes]
        
        expected_fees = []
        for cls in classes:
            expected = 0
            for std in cls.students.all():
                expected+= (date.today().month - std.admission_date.month)*std.classname.fees + std.year_outstanding
            expected_fees.append(expected)
        
        fees_by_class = (
            models.FeesRecord.objects
            .values('student__classname')
            .annotate(total_collected=Sum('fees'))
        )
        collected_dict = {item['student__classname']: float(item['total_collected']) for item in fees_by_class}
        collected_fees = [collected_dict.get(cls.class_id, 0) for cls in classes]
        print(class_names, expected_fees, collected_fees)
        return JsonResponse({
            'status': 'success',
            'class_names': class_names,
            'expected_fees':expected_fees,
            'collected_fees': collected_fees
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required(login_url='/teacher/loginpage/')
def open_gallery(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        photo = request.FILES.get('photo')
        
        if photo:
            models.Gallery.objects.create(
                title = title,
                photo = photo
            )
            return JsonResponse({'status':'success','message':'Photo added successfully'})
        else:
            return JsonResponse({'status':'error','message':'Fill all the fields'})
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            gallery_id = data.get('id')

            item = models.Gallery.objects.get(gallery_id=gallery_id)
            item.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Deleted Successfully'
            })

        except models.Gallery.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Image not found'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
          
    context = {
        'photos':models.Gallery.objects.all(),
        'info':models.Website_Details_For_Easy_Access.objects.first()
    }   
    return render(request,'teacher/open_gallery.html',context)

@login_required(login_url='/teacher/loginpage/')
def Done(request):
    '''Renders the done page for teachers.'''
    return render(request,'Teacher/Done.html')

def subhojit(request):
    if request.method == 'GET':
        try:
            otp = random.randint(100000, 999999)
            request.session['temp_otp'] = otp
            request.session['session'] = False
            send_mail(
                'Welcome to Secret World',
                f'Your One Time Password for your request id {otp}',
                'subhojitghosh988340@gmail.com',
                ['subhojitghosh4200@gmail.com']
            )
        except Exception as e:
            return HttpResponse('Slow internet connection')
        
        return render(request, 'Teacher/secret.html')

    elif request.method == 'POST':
        OTP = request.POST.get('otp')
        stored_otp = request.session.get('temp_otp')
        if str(OTP) == str(stored_otp):
            request.session['session'] = True
            del request.session['temp_otp']
            return redirect('name_and_logo_modifier_for_easy_access')
        else:
            return HttpResponse('OTP mismatch')


def name_and_logo_modifier_for_easy_access(request):
    # Ensure the user has access first
    if not request.session.get('session'):
        return HttpResponse("Sorry, you can't afford it...")

    if request.method == 'POST':
        website_name = request.POST.get('website_name')
        website_logo = request.FILES.get('website_logo')

        if website_logo and website_name:
            try:
                models.Website_Details_For_Easy_Access.objects.all().delete()
                models.Website_Details_For_Easy_Access.objects.create(
                    website_name=website_name,
                    website_logo=compressed_image(website_logo,800,50)
                )
                request.session['session'] = False  # optional logout
                return redirect('loginpage')
            except Exception as e:
                return HttpResponse('Error in create instance in database')
        else:
            return HttpResponse('Fill all the required details')

    # For GET requests, just show the page
    return render(request, 'Teacher/supersecret.html')

def id_card(request,id):
    try:
        student = models.Student.objects.get(student_id=id)
    except Exception as e:
        return JsonResponse({'status':'error','message':str(e)})
    return render(request,'Teacher/id_card.html',{'student':student,'info':models.Website_Details_For_Easy_Access.objects.first()})

def noti(request):
    return render(request,'Teacher/noti.html')

@csrf_exempt
def save_fcm_token(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            token = data.get("token")

            if not token:
                return JsonResponse({"error": "Token missing"}, status=400)

            # TODO: Save token to DB here
            print("FCM Token saved:", token)

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=405)

def send_data_message(token, title, body, image_url=None):
     data = {
          "title":title,
          "body":body,
          "icon": 'TeacherWeb\media\website_details_metadata\port6.jpg'
     }
     if image_url:
          data["image"]=image_url
     
     message = messaging.Message(data=data, token=token)

     response = messaging.send(message)
     print("Data message sent: ", response)