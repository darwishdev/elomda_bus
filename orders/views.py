from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from PIL import Image
import base64
import numpy as np
from pyzbar import pyzbar
import json
from io import BytesIO  # تم إضافة الاستيراد الصحيح هنا
from datetime import date
from .models import Size, Category, Topping, Price_List, Item_List, Cart_List, Extra, Order, ImageSlider, Attendance

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("scan_qr"))
        else:
            return render(request, "orders/login.html", {"message": "Invalid credentials."})
    return render(request, "orders/login.html")

def logout_view(request):
    logout(request)
    return render(request, "orders/login.html", {"message": "Logged out."})

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "orders/signup.html", {"form": form})
    form = UserCreationForm()
    return render(request, "orders/signup.html", {"form": form})

import cv2
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Item_List, Attendance
from django.contrib import messages
from django.utils import timezone
import base64
import json
import numpy as np
import cv2
from datetime import date

def scan_qr(request):
    if request.method == 'POST':
        image_data = request.POST.get('image', None)
        if image_data:
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image_np = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

            # تحويل الصورة إلى رمادي
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # اكتشاف الأكواد الشريطية (QR)
            decoded_qrs = cv2.QRCodeDetector().detectAndDecode(gray_image)

            if decoded_qrs[0]:
                qr_data = decoded_qrs[0]
                item_id = qr_data.split(',')[0].split(':')[-1].strip()
                item = get_object_or_404(Item_List, id=item_id)
                response_data = {
                    'id': item.id,
                    'name': item.name,
                    'category': item.category.name,
                    'subscription_start_date': item.subscription_start_date,
                    'subscription_end_date': item.subscription_end_date,
                    'image_url': item.image.url if item.image else None
                }
                return JsonResponse(response_data)
            else:
                return JsonResponse({'error': 'No QR code detected.'})
    elif request.method == 'GET':
        return render(request, 'scan_qr.html')
    return JsonResponse({'error': 'Invalid request'})

def attendance_view(request):
    if request.method == 'POST':
        attendance_data = request.POST.get('attendance_data', None)
        attendance_status = request.POST.get('attendance_status', None)

        if attendance_data:
            try:
                data = json.loads(attendance_data)
                existing_record = Attendance.objects.filter(
                    user_id=data['id'], attendance_date=date.today()
                ).first()

                if existing_record:
                    if attendance_status == 'حضور':
                        if existing_record.attendance_status == 'حضور':
                            messages.error(request, f"{data['name']} has already been marked as present today!")
                        else:
                            existing_record.attendance_status = 'حضور'
                            existing_record.save()
                            messages.success(request, f"{data['name']} marked as present successfully!")
                    elif attendance_status == 'انصراف':
                        if existing_record.departure_status == 'انصراف':
                            messages.error(request, f"{data['name']} has already been marked as departed today!")
                        else:
                            existing_record.departure_status = 'انصراف'
                            existing_record.save()
                            messages.success(request, f"{data['name']} marked as departed successfully!")
                else:
                    Attendance.objects.create(
                        user_id=data['id'],
                        name=data['name'],
                        category=data['category'],
                        subscription_start_date=data['subscription_start_date'],
                        subscription_end_date=data['subscription_end_date'],
                        attendance_status='حضور' if attendance_status == 'حضور' else 'غياب',
                        departure_status='انصراف' if attendance_status == 'انصراف' else 'غياب',
                        attendance_date=date.today()
                    )
                    messages.success(request, f"{data['name']} Attendance ({attendance_status}) recorded successfully!")
            except Exception as e:
                messages.error(request, f"Error: {e}")
    
    return render(request, 'scan_qr.html')

def attendance_reset_view(request):
    today = timezone.now().date()
    last_recorded_date = Attendance.objects.latest('attendance_date').attendance_date if Attendance.objects.exists() else None
    
    if not last_recorded_date or last_recorded_date < today:
        for item in Item_List.objects.all():
            Attendance.objects.create(
                user_id=item.id,
                name=item.name,
                category=item.category.name,
                subscription_start_date=item.subscription_start_date,
                subscription_end_date=item.subscription_end_date,
                attendance_status='غياب',
                attendance_date=today
            )
    return render(request, 'attendance_page.html', {'attendance_list': Attendance.objects.filter(attendance_date=today)})

def scan_qr_by_id(request):
    today = timezone.now().date()
    if request.method == 'POST':
        item_id = request.POST.get('item_id', None)
        if item_id:
            try:
                item = get_object_or_404(Item_List, id=item_id)
                response_data = {
                    'id': item.id,
                    'name': item.name,
                    'category': item.category.name,
                    'subscription_start_date': item.subscription_start_date,
                    'subscription_end_date': item.subscription_end_date,
                    'image_url': item.image.url if item.image else None
                }
                return JsonResponse(response_data)
            except Exception as e:
                return JsonResponse({'error': 'Item not found'})
        else:
            return JsonResponse({'error': 'Invalid item ID'})

def get_qr_code_as_base64(item):
    if item.qr_code:
        return base64.b64encode(item.qr_code).decode('utf-8')
    return None

def attendance_view(request):
    if request.method == 'POST':
        attendance_data = request.POST.get('attendance_data', None)
        attendance_status = request.POST.get('attendance_status', None)

        if attendance_data:
            try:
                data = json.loads(attendance_data)
                existing_record = Attendance.objects.filter(
                    user_id=data['id'], attendance_date=date.today()
                ).first()

                if existing_record:
                    if attendance_status == 'حضور':
                        if existing_record.attendance_status == 'حضور':
                            messages.error(request, f"{data['name']} has already been marked as present today!")
                        else:
                            existing_record.attendance_status = 'حضور'
                            existing_record.save()
                            messages.success(request, f"{data['name']} marked as present successfully!")
                    elif attendance_status == 'انصراف':
                        if existing_record.departure_status == 'انصراف':
                            messages.error(request, f"{data['name']} has already been marked as departed today!")
                        else:
                            existing_record.departure_status = 'انصراف'
                            existing_record.save()
                            messages.success(request, f"{data['name']} marked as departed successfully!")
                else:
                    Attendance.objects.create(
                        user_id=data['id'],
                        name=data['name'],
                        category=data['category'],
                        subscription_start_date=data['subscription_start_date'],
                        subscription_end_date=data['subscription_end_date'],
                        attendance_status='حضور' if attendance_status == 'حضور' else 'غياب',
                        departure_status='انصراف' if attendance_status == 'انصراف' else 'غياب',
                        attendance_date=date.today()
                    )
                    messages.success(request, f"{data['name']} Attendance ({attendance_status}) recorded successfully!")
            except Exception as e:
                messages.error(request, f"Error: {e}")
    
    return render(request, 'scan_qr.html')

def attendance_reset_view(request):
    today = timezone.now().date()
    last_recorded_date = Attendance.objects.latest('attendance_date').attendance_date if Attendance.objects.exists() else None
    
    if not last_recorded_date or last_recorded_date < today:
        for item in Item_List.objects.all():
            Attendance.objects.create(
                user_id=item.id,
                name=item.name,
                category=item.category.name,
                subscription_start_date=item.subscription_start_date,
                subscription_end_date=item.subscription_end_date,
                attendance_status='غياب',
                attendance_date=today
            )
    return render(request, 'attendance_page.html', {'attendance_list': Attendance.objects.filter(attendance_date=today)})

def scan_qr_by_id(request):
    today = timezone.now().date()
    if request.method == 'POST':
        item_id = request.POST.get('item_id', None)
        if item_id:
            try:
                item = get_object_or_404(Item_List, id=item_id)
                response_data = {
                    'id': item.id,
                    'name': item.name,
                    'category': item.category.name,
                    'subscription_start_date': item.subscription_start_date,
                    'subscription_end_date': item.subscription_end_date,
                    'image_url': item.image.url if item.image else None
                }
                return JsonResponse(response_data)
            except Exception as e:
                return JsonResponse({'error': 'Item not found'})
        else:
            return JsonResponse({'error': 'Invalid item ID'})
