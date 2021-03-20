from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.db.models.signals import post_save,post_delete
import datetime
from django.utils import timezone

# Create your models here.
class Dealer(models.Model):
    name = models.CharField(unique=True, max_length=200)
    mob_num = models.IntegerField(unique=True, blank=True, null=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Collected_by(models.Model):
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = "Money Collected By"

    def __str__(self):
        return self.name


class Ledger(models.Model):
    date = models.DateTimeField("Date",default = timezone.now)
    particulars = models.CharField("Particulars",max_length=100,blank=True)
    debit = models.PositiveIntegerField("Debit",blank=True, default=0)
    credit = models.PositiveIntegerField("Credit",blank=True, default=0)
    paymode = models.CharField("Payment Mode",max_length=25, choices=(('Cash','Cash'),
                                                       ('Cheque','Cheque'),
                                                       ('No Money Collected','No Money Collected'),))
    isChequeCleared = models.BooleanField(default=False,verbose_name='Check only in case of cleared Cheque')
    new_balance = models.IntegerField(editable=False)
    dr_cr = models.CharField("Dr/Cr",max_length=2,default='nil',editable=False)
    invoice = models.ImageField("Invoice", blank=True, null=True)#,upload_to='images/')
    dealer = models.ForeignKey(Dealer,verbose_name="Dealer", null=True, on_delete=models.CASCADE)
    balance = models.IntegerField(editable=False,default=0)
    dealer_ledger_number = models.IntegerField(editable=False,default=0)
    display_date = models.DateField("DI Date",default = timezone.now,editable = False)
    #created = models.DateTimeField("Date",auto_now_add=True)
    @property
    def cur_bal_calculator(self):
        prev = BrandNew.objects.get(dealer = self.dealer)
        return prev.balance + self.debit-self.credit

    @property
    def assign_dealer_ledger_number(self):
        prev = BrandNew.objects.get(dealer = self.dealer)
        return prev.ledger_number + 1

    @property
    def assign_dr_cr(self):
        if(self.new_balance<0):
            return "Cr"
        else:
            return "Dr"

    @property
    def assign_positive_balance(self):
        return abs(self.new_balance)

    collect_by = models.ForeignKey(Collected_by,verbose_name="Collected By", blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
          self.new_balance = self.cur_bal_calculator
          self.dealer_ledger_number = self.assign_dealer_ledger_number
          self.balance = self.assign_positive_balance
          self.dr_cr = self.assign_dr_cr
          super(Ledger, self).save(*args, **kwargs)



    class Meta:
        db_table= "led"

class ViewDealer(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    dealer = models.ManyToManyField(Dealer, related_name="dealer", blank= True)

    class Meta:
        verbose_name_plural = "Dealer Permission Area"

class RoadExpense(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    fooding = models.PositiveIntegerField(blank=True, default=0)
    fuel = models.PositiveIntegerField(blank=True, default=0)
    misc = models.TextField(blank=True)
    date = models.DateTimeField("Date",auto_now_add=True)

    # def __str__(self):
    #     return self.user

#class ForDate(models.Model):
#    dealer = models.ForeignKey(Dealer)

class BrandNew(models.Model):
    dealer = models.ForeignKey(Dealer,on_delete=models.CASCADE)
    #dr_cr = models.CharField("Dr/Cr",max_length=10, default='', choices=(('Dr','Dr'),('Cr','Cr'),))
    balance = models.IntegerField(default=0)
    ledger_number = models.IntegerField(default=0)

def bal_one(sender, instance, **kwargs):
    if kwargs['created']:
        a = BrandNew(dealer = instance,balance = 0,ledger_number=0)
        a.save()


def update_bal_one(sender,instance,**kwargs):
    if kwargs['created']:

        a = BrandNew.objects.get(dealer = instance.dealer)

        a.delete()
        m = BrandNew(dealer = instance.dealer,balance = instance.new_balance,ledger_number = instance.dealer_ledger_number)
        m.save()

    if  not kwargs['created']:
        print(instance.date)
        m = BrandNew.objects.get(dealer = instance.dealer)
        latest_ledger_number = instance.dealer_ledger_number
        cur_ledger_number = latest_ledger_number -1
        while(cur_ledger_number!=1):
            try:
                obj = Ledger.objects.get(dealer_ledger_number = cur_ledger_number,dealer = instance.dealer)
                print(obj.particulars)
            except:
                break
            cur_ledger_number-=1
        print(cur_ledger_number,"is changed")
        if cur_ledger_number == 1:
            prev = 0
        else:
            prev = Ledger.objects.get(dealer_ledger_number = cur_ledger_number-1,dealer= instance.dealer).new_balance
        i = cur_ledger_number
        new_balance = prev + instance.debit - instance.credit
        BN = BrandNew.objects.get(dealer = instance.dealer)
        BN.delete()
        BN.ledger_number = i-1
        BN.dealer = instance.dealer
        BN.balance = prev
        BN.save()
        led = Ledger(dealer = instance.dealer,date=instance.date,debit = instance.debit,credit = instance.credit,collect_by=instance.collect_by,paymode=instance.paymode,particulars=instance.particulars,isChequeCleared=instance.isChequeCleared)
        led.save()
        i = i+1
        while(i!=latest_ledger_number):
            old = Ledger.objects.get(dealer_ledger_number = i,dealer=instance.dealer)
            cb = old.collect_by
            print('here')
            print(old.particulars)
            part = old.particulars
            old.delete()
            old.save()
            i = i+1
        Ledger.objects.get(dealer_ledger_number = latest_ledger_number,dealer = instance.dealer).delete()



post_save.connect(bal_one,sender = Dealer)
post_save.connect(update_bal_one,sender = Ledger)
