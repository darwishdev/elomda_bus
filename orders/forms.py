from django import forms
from .models import Item_lists

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item_lists
        fields = ['name', 'quantity', 'purchase_price', 'sale_price']