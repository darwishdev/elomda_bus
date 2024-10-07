from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, Size, Topping, Extra, Price_List, Item_List, Cart_List, Order, ImageSlider
from django.utils.translation import gettext_lazy as _
from io import BytesIO
import qrcode
import base64

admin.site.site_header = _("elomda_bus")
admin.site.site_title = _("elomda Admin")
admin.site.index_title = _("Welcome to Admin Portal")

class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'purchase_price')
    search_fields = ('name',)
    list_filter = ('name',)


class ItemListAdmin(admin.ModelAdmin):
    list_display = ('formatted_id', 'name', 'category', 'subscription_start_date', 'subscription_end_date', 'qr_code_tag')
    search_fields = ('name',)
    list_filter = ('category', 'subscription_start_date', 'subscription_end_date')
    readonly_fields = ('qr_code_tag',)

    def formatted_id(self, obj):
        return str(obj.id).zfill(4)
    formatted_id.short_description = 'ID'

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # تحويل QR code إلى صورة Base64
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return img_str

    def qr_code_tag(self, obj):
        # هنا يتم توليد QR code من معلومات العنصر (مثلاً، الاسم أو ID)
        qr_data = f"Product ID: {obj.id}, Name: {obj.name}, Category: {obj.category.name}, Start Date: {obj.subscription_start_date}, End Date: {obj.subscription_end_date}"
        qr_code_base64 = self.generate_qr_code(qr_data)

        # عرض QR code في Admin باستخدام Base64
        if qr_code_base64:
            return mark_safe(f'<img src="data:image/png;base64,{qr_code_base64}" width="150" height="150" />')
        return None
    qr_code_tag.short_description = 'QR Code Preview'

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'custom_topping', 'custom_extra', 'custom_size', 'logo_tag')
    search_fields = ('name',)
    readonly_fields = ('logo_tag',)

    def logo_tag(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="50" height="50" />')
        return None
    logo_tag.short_description = 'Logo Preview'

class ImageSliderAdmin(admin.ModelAdmin):
    list_display = ('caption', 'image_tag')
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="150" height="150" />')
        return None
    image_tag.short_description = 'Image Preview'

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'order_items_display', 'total_purchase_price', 'total_sale_price', 'net_profit')
    list_display_links = None  # إزالة الروابط من الأعمدة لتجنب ظهور الروابط عند الضغط

    def order_items_display(self, obj):
        items = obj.cart_id.all()
        return mark_safe("<br>".join([f"{item.quantity} x {item.item_id.name}" for item in items]))
    order_items_display.short_description = 'Order Items'

    def total_purchase_price(self, obj):
        total_purchase = 0
        for cart_item in obj.cart_id.all():
            if cart_item.size:
                total_purchase += cart_item.size.purchase_price * cart_item.quantity
        return total_purchase
    total_purchase_price.short_description = 'Total Purchase Price'

    def total_sale_price(self, obj):
        total_sale = 0
        for cart_item in obj.cart_id.all():
            total_sale += cart_item.calculated_price
        return total_sale
    total_sale_price.short_description = 'Total Sale Price'

    def net_profit(self, obj):
        profit = self.total_sale_price(obj) - self.total_purchase_price(obj)
        return profit
    net_profit.short_description = 'Net Profit'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_purchase = sum(self.total_purchase_price(obj) for obj in qs)
            total_sale = sum(self.total_sale_price(obj) for obj in qs)
            total_profit = sum(self.net_profit(obj) for obj in qs)

            extra_context = extra_context or {}
            extra_context['total_purchase'] = total_purchase
            extra_context['total_sale'] = total_sale
            extra_context['total_profit'] = total_profit

            response.context_data.update({
                'title': f'Orders ({qs.count()} orders, Total Net Profit: {total_profit:.2f})'
            })
            
            response.context_data.update(extra_context)
        except (AttributeError, KeyError):
            pass
        return response

# admin.site.register(Size, SizeAdmin)
# admin.site.register(Category, CategoryAdmin)
# admin.site.register(Price_List)
# admin.site.register(Item_List, ItemListAdmin)
# admin.site.register(Cart_List)
# admin.site.register(Order, OrderAdmin)

from .models import Attendance




from django.utils.html import mark_safe
from django.utils import timezone


from django.db.models import Q

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'category', 'subscription_start_date', 'subscription_end_date', 'attendance_date', 'attendance_status', 'departure_status')
    search_fields = ('name', 'user_id')
    list_filter = ('attendance_date', 'category', 'attendance_status', 'departure_status')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        today = timezone.now().date()

        # التحقق من أن كل طالب لديه سجل في اليوم الحالي
        for item in Item_List.objects.all():
            attendance_record = Attendance.objects.filter(user_id=item.id, attendance_date=today).first()

            # إذا لم يكن هناك سجل، قم بإنشاء سجل جديد بحالة غياب للحضور والانصراف
            if attendance_record is None:
                Attendance.objects.create(
                    user_id=item.id,
                    name=item.name,
                    category=item.category.name,
                    subscription_start_date=item.subscription_start_date,
                    subscription_end_date=item.subscription_end_date,
                    attendance_status='غياب',  # تعيين القيمة الافتراضية إلى غياب للحضور
                    departure_status='غياب',  # تعيين القيمة الافتراضية إلى غياب للانصراف
                    attendance_date=today
                )

        return queryset

    def save_model(self, request, obj, form, change):
        # البحث عن السجل الموجود في اليوم الحالي
        attendance_record = Attendance.objects.filter(user_id=obj.user_id, attendance_date=obj.attendance_date).first()

        # إذا كان السجل موجودًا، قم بتحديث حالة الحضور أو الانصراف
        if attendance_record:
            if obj.attendance_status == 'حضور':
                attendance_record.attendance_status = 'حضور'
            if obj.departure_status == 'انصراف':
                attendance_record.departure_status = 'انصراف'
            attendance_record.save()  # حفظ التعديلات
        else:
            # إذا لم يكن هناك سجل، قم بحفظ السجل الجديد
            super().save_model(request, obj, form, change)

admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Item_List, ItemListAdmin)
admin.site.register(Category, CategoryAdmin)


# 

# User id
# Name
# Category
# Subscription start date
# Subscription end date
# Attendance date
# Attendance status