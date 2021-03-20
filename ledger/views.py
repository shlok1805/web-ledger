from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import LedgerForm, DealerForm, RoadExpenseForm
from .decorators import unauthenticated_user, allowed_users, admin_only
from django.core.paginator import Paginator, EmptyPage

# for current date displaying in netbal_pdf_view
import datetime
from datetime import date, timedelta
#for rendering pdf
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
#for image storage
from django.core.files.storage import FileSystemStorage



#function for rendering pdf of dealer report
@login_required(login_url='loginuser')
@allowed_users(allowed_roles=['admin'])
def netbal_pdf_view(request):
    template_path = 'ledger/netbalpdf.html'
    a = BrandNew.objects.all()
    size = len(a)
    today = date.today()
    d4 = today.strftime("%d-%b-%Y")
    context = {'a':a,'size':size,'today':d4}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    #if direct download needed uncomment line below
    #response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

#function for rendering pdf of records in range of mentioned dates


def day_range_rec(request):
    if request.method == 'GET':
        return render(request,'ledger/dailytrans.html')

    else:
        template_path = 'ledger/day_range_rec.html'
        fromdate = request.POST.get('fromdate')
        todate = request.POST.get('todate')
        # To force selection of both the date fields
        if fromdate == "" or todate == "":
            context = {"error": "Please select both the fields"}
            return render(request,'ledger/dailytrans.html', context)

        # To ensure selected date range is valid
        today = date.today()
        d1 = today.strftime("%Y-%m-%d")
        tomorrow = today + timedelta(1)
        d2 =  tomorrow.strftime("%Y-%m-%d")
        if fromdate>todate or fromdate>d1 or todate>d2:
            context = {"error": "selected date range is invalid"}
            return render(request,'ledger/dailytrans.html', context)

        ledgers = Ledger.objects.raw('select * from led where date between "'+fromdate+'" and "'+todate+'"')
        context = {'ledgers': ledgers, 'fromdate':fromdate, 'todate': todate}
        # Create a Django response object, and specify content_type as pdf
        response = HttpResponse(content_type='application/pdf')
        #if direct download needed uncomment line below
        #response['Content-Disposition'] = 'attachment; filename="report.pdf"'
        response['Content-Disposition'] = 'filename="report.pdf"'
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # create a pdf
        pisa_status = pisa.CreatePDF(
           html, dest=response)
        # if error then show some funy view
        if pisa_status.err:
           return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response


#LEDGER
@login_required(login_url='loginuser')
@admin_only
def home(request):
    #this edit to solve the MultiValueDictKeyError
    query = request.POST.get('query', False)
    if query == "":
        return render(request, 'ledger/home.html')
    alldealers = Dealer.objects.filter(name__istartswith=query)
    context = {'alldealers':alldealers}
    return render(request, 'ledger/home.html', context)

@login_required(login_url='loginuser')
@allowed_users(allowed_roles=['admin', 'employee'])
def ledger(request, pk):
    dealer = Dealer.objects.get(id=pk)
    form = LedgerForm(initial={"dealer":dealer},instance=dealer)
    if request.method == 'GET':
        return render(request, 'ledger/ledger.html', {'form':form})
    else:
        form = LedgerForm(request.POST, request.FILES or None)

        if form.is_valid():
            form.save()
            # redirecting employee groups to their userpage and admins to the dealer page
            if request.user.groups.filter(name='admin'):
                return redirect('dealer', pk)
            else:
                return redirect('userpage')


@login_required(login_url='loginuser')
@allowed_users(allowed_roles=['admin'])
def dealer(request, pk):
    dealer = Dealer.objects.get(id=pk)
    ledgers = dealer.ledger_set.all()
    orderedledger = ledgers.order_by('-date')

    #paginating
    p = Paginator(orderedledger, 10)
    page_num = request.GET.get('page', 1)
    try:
        page = p.page(page_num)
    except EmptyPage:
        page = p.page(1)

    context = {'dealer':dealer,'orderedledger':page,'pk':pk}
    return render(request, 'ledger/dealer.html', context)

@login_required(login_url='loginuser')
@allowed_users(allowed_roles=['admin'])
def dealerform(request):
    if request.method == 'GET':
        return render(request, 'ledger/dealerform.html', {'form':DealerForm()})
    else:
        form = DealerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')

@login_required(login_url='loginuser')
def userpage(request):
    try :
        userobjects = ViewDealer.objects.get(user=request.user)
        dealerallowed = userobjects.dealer.all()
    except :
        context = {"message": "No dealers allowed to view"}
        return render(request, 'ledger/user.html', context)
    # list l is storing data of all allowed dealer and their ledgers
    l = []
    for d in dealerallowed:
        dict = {}
        dict["name"] = d.name
        dict["address"] = d.address
        dict["mobile"] = d.mob_num
        dict['dealerid'] = d.id
        #leg list for storing ledgers of the current iterating dealer
        leg = []
        bn = BrandNew.objects.get(dealer = d.id)
        led_number = bn.ledger_number
        k = 0
        while(k!=30):
            try:
                led = Ledger.objects.get(dealer = d,dealer_ledger_number = led_number-k)
                leg.append(led)
            except:
                break
            k += 1
        dict["ledger"] = leg
        l.append(dict)
    if len(dealerallowed) == 0:
        context = {"message": "No dealers allowed to view"}
    else:
        context = {"ledgers":l}
    return render(request, 'ledger/user.html', context)

def roadexpense(request):
    if request.method == 'GET':
        user = request.user
        form = RoadExpenseForm(initial={"user":user},instance=user)
        return render(request, 'ledger/expense.html', {'form':form})
    else:
        form = RoadExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')



# report to be converted into pdf from html
@login_required(login_url='loginuser')
@allowed_users(allowed_roles=['admin'])
def dailytrans(request):
    return render(request,'ledger/dailytrans.html')




# AUTHENTICATION FUNCTIONS

@unauthenticated_user
def loginuser(request):
    if request.method == 'POST':
        username=request.POST['username']
        password=request.POST['password']
        user = authenticate(username=request.POST['username'],password=request.POST['password'])
        if user is None:
            print("I'm In")
            print(AuthenticationForm())
            return render(request, 'ledger/login.html', {'form':AuthenticationForm(), 'error': 'Username or Password did not match'})
        else:
            login(request, user)
            return redirect('home')
    else:
        return render(request, 'ledger/login.html', {'form':AuthenticationForm()})


def logoutuser(request):
    if request.method == 'POST':
        logout(request)
        return redirect('loginuser')

def cheque_alter(request,ledger_no,pk):
    dealer = Dealer.objects.get(id = pk)
    led = Ledger.objects.get(dealer_ledger_number = ledger_no,dealer = dealer.id)
    val = led.isChequeCleared
    led.isChequeCleared = not val
    led.save()
    return redirect('dealer',pk)
