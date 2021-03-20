from django.forms import ModelForm
from .models import *

class LedgerForm(ModelForm):
    class Meta:
        model = Ledger
        fields = ['particulars', 'debit', 'credit', 'paymode', 'invoice', 'dealer', 'collect_by']



class DealerForm(ModelForm):
    class Meta:
        model = Dealer
        fields = '__all__'


class RoadExpenseForm(ModelForm):
    class Meta:
        model = RoadExpense
        fields = '__all__'
