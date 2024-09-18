from django.db import models
from django.contrib.auth.models import User
import qrcode
from django.core.files import File
from io import BytesIO


class Category(models.Model):
    name = models.CharField(max_length=64)
    custom_topping = models.BooleanField(default=False)
    custom_extra = models.BooleanField(default=False)
    custom_size = models.BooleanField(default=False)
    logo = models.ImageField(upload_to='category_logos/', null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

class Size(models.Model):
    name = models.CharField(max_length=64, verbose_name="مكان الشراء")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الشراء", default=0.00)

    def __str__(self):
        return self.name

class Topping(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"

class Extra(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"

class Price_List(models.Model):
    name = models.CharField(max_length=64)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    large_supp = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name}, Base: {self.base_price}, large_supp: {self.large_supp}"


class Item_List(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    subscription_start_date = models.DateField(verbose_name="Subscription Start Date", null=True, blank=True)
    subscription_end_date = models.DateField(verbose_name="Subscription End Date", null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)

    def __str__(self):
        return f"{str(self.id).zfill(4)} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)

        qr_data = f"Product ID: {self.id}, Name: {self.name}, Category: {self.category.name}, Start Date: {self.subscription_start_date}, End Date: {self.subscription_end_date}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        file_name = f"qr_code_{self.id}.png"
        self.qr_code.save(file_name, File(buffer), save=False)

        super().save(*args, **kwargs)

class Cart_List(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    item_id = models.ForeignKey(Item_List, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    calculated_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_current = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.quantity} x {self.item_id.name}"

class Order(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    cart_id = models.ManyToManyField(Cart_List)
    complete = models.BooleanField(default=False)

    def __str__(self):
        status = "Complete" if self.complete else "On Order"
        return f"{self.user_id}, Status: {status}"

class ImageSlider(models.Model):
    image = models.ImageField(upload_to='slider_images/')
    caption = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.caption if self.caption else f"Image {self.id}"

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comments = models.TextField()

    def __str__(self):
        return f'Feedback from {self.user.username} - Rating: {self.rating}'

# --------------------
# models.py

from django.db import models
from django.utils import timezone

from datetime import date

class Attendance(models.Model):
    user_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255) 
    subscription_start_date = models.DateField()
    subscription_end_date = models.DateField()
    attendance_date = models.DateField(default=timezone.now)

    ATTENDANCE_CHOICES = [
        ('حضور', 'حضور'),
        ('انصراف', 'انصراف'),
        ('غياب', 'غياب'),
    ]

    # إضافة حقول للحضور والانصراف
    attendance_status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_CHOICES,
        default='غياب',
        verbose_name='حالة الحضور',
    )
    departure_status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_CHOICES,
        default='غياب',
        verbose_name='حالة الانصراف',
    )

    def __str__(self):
        return f"{self.name} - {self.attendance_status} / {self.departure_status} - {self.attendance_date}"

    @classmethod
    def mark_attendance(cls, user_id, status, is_departure=False):
        today = timezone.now().date()
        attendance_record, created = cls.objects.get_or_create(
            user_id=user_id,
            attendance_date=today,
            defaults={'attendance_status': 'غياب', 'departure_status': 'غياب'}  # تعيين القيمة الافتراضية إلى غياب
        )

        # تحديث حالة الحضور أو الانصراف بناءً على المدخلات
        if not is_departure and status == 'حضور':
            attendance_record.attendance_status = status
        elif is_departure and status == 'انصراف':
            attendance_record.departure_status = status

        # التحقق من تحديث الحالة الافتراضية
        if attendance_record.attendance_status == 'غياب' and not is_departure:
            attendance_record.attendance_status = status
        if attendance_record.departure_status == 'غياب' and is_departure:
            attendance_record.departure_status = status

        attendance_record.save()
        return attendance_record
