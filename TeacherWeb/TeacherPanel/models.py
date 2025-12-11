from django.db import models
from django.db.models import Sum
from datetime import timedelta,date
from decimal import Decimal
class Classname(models.Model):
    class_id = models.AutoField(primary_key=True)
    classname = models.CharField(max_length=50,unique=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    classes = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    
    @property
    def decode_classname(self):
        idx = self.classes.index(self.classname)
        return idx+1
    
    class Meta:
        verbose_name = 'Classname'
        verbose_name_plural = 'Classnames'
        db_table = 'class_info'
    
    def __str__(self):
        return self.classname

class Batch(models.Model):
    batch_id = models.AutoField(primary_key=True)
    classname = models.ForeignKey(Classname,on_delete=models.CASCADE,related_name='batch')
    batch_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.classname}-{self.batch_name}"

class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    studentname = models.CharField(max_length=100)
    fathername = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    photo = models.ImageField(upload_to='student_photos/')
    classname = models.ForeignKey(Classname, on_delete=models.CASCADE,related_name='students')
    batch = models.ForeignKey(Batch,on_delete=models.CASCADE,related_name='students')
    admission_date = models.DateField(default=date(2025,5,5))
    year_outstanding = models.DecimalField(max_digits=10,decimal_places=2,default=250.00)
    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        db_table = 'student_info'
        ordering = ['studentname']
    
    def __str__(self):
        return self.studentname

class Notice(models.Model):
    notice_id = models.AutoField(primary_key=True)
    notice_instraction = models.CharField(max_length=5000)
    notice_photo = models.ImageField(upload_to='notice_photos/',blank=True,null=True)
    notice_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Notice'
        verbose_name = 'NoticeInstruction'
        ordering = ['notice_id']
    
    def __str__(self):
        return self.notice_instraction[:1000]

class FeesRecord(models.Model):
    fees_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student,on_delete=models.CASCADE,related_name='fees')
    paid_at = models.DateField(auto_now_add=True)
    remark = models.CharField(max_length=1000,default='Paid')
    mode = models.CharField(max_length=1000,default='Cash')
    fees = models.DecimalField(max_digits=10,decimal_places=2)
    total_fees = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    paying_month = models.BooleanField(default=False)
    how_many_month = models.IntegerField(default=0)
    def save(self, *args, **kwargs):
        previous_record = FeesRecord.objects.filter(student = self.student).exclude(pk=self.pk).order_by('-paid_at','-fees_id').first()
        super().save(*args, **kwargs)
        total = self.student.fees.aggregate(totalfees=Sum('fees'))['totalfees'] or 0
        self.total_fees = total
        if previous_record:
            previous_paid_for = previous_record.due_months[4]
            new_paid_for = self.due_months[4]
            if new_paid_for > previous_paid_for:
                self.paying_month = True
                self.how_many_month = new_paid_for - previous_paid_for
        super().save(update_fields=['total_fees','paying_month','how_many_month'])
    
    @property
    def due_months(self):
        year_outstanding_balance = max(self.student.year_outstanding - self.total_fees,0)
        total_after_year_outstanding = max(self.total_fees - self.student.year_outstanding,0)
        today = date.today()
        total_month_have_studided = (today - self.student.admission_date).days // 30
        paid_for = total_after_year_outstanding//self.student.classname.fees
        due_months = int(total_month_have_studided - paid_for)
        saved_money = total_after_year_outstanding % self.student.classname.fees
        due_amount = max(due_months*self.student.classname.fees - saved_money,0)
        return due_months,saved_money,due_amount,year_outstanding_balance,paid_for
            
    def __str__(self):
        return f'{self.student.studentname}-{self.paid_at}'

class RoutineEntry(models.Model):
    entry_id = models.AutoField(primary_key=True)
    day_name = models.CharField(max_length=20)
    subject = models.CharField(max_length=100)
    start_time = models.TimeField()
    
    class Meta:
        db_table = 'Routine_Entry'
        verbose_name = 'RoutineEntry'
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.subject}"   

class Online_Class_Link(models.Model):
    class_link_id = models.AutoField(primary_key=True)
    classname = models.ForeignKey(Classname,on_delete=models.CASCADE,related_name='online_class_links')
    batch = models.ForeignKey(Batch,on_delete=models.CASCADE,related_name='online_class_links',blank=True,null=True)
    class_date = models.DateField()
    time = models.TimeField()
    subject = models.CharField(max_length=100)
    class_link = models.URLField()
    
    class Meta:
        db_table = 'Online_Class_Link'
        verbose_name = 'OnlineClassLink'
        ordering = ['classname','batch','class_date','time']
    def __str__(self):
        return f"{self.classname}-{self.batch.batch_name}-{self.class_date}-{self.subject}"
    
class Website_Details_For_Easy_Access(models.Model):
    instance_id = models.AutoField(primary_key=True)
    website_logo = models.ImageField(upload_to='website_details_metadata')
    website_name = models.CharField(max_length=1000)
    
    class Meta:
        db_table = "Website_Details"
        verbose_name = "info"
    
    def __str__(self):
        return self.website_name