from django import forms


class BarcodeScanForm(forms.Form):
    barcode = forms.CharField(max_length=64)
