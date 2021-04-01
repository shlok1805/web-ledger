"""webledger URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from ledger import views
#for invoice images
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    #url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    #url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}), 
    path('admin/', admin.site.urls),

    #ledger
    path('', views.home, name = 'home'),
    path('dealerform/', views.dealerform, name = 'dealerform'),
    path('ledger/<int:pk>/', views.ledger, name = 'ledger'),
    path('dealer/<int:pk>/', views.dealer, name = 'dealer'),
    path('user/', views.userpage, name = 'userpage'),
    path('expense/', views.roadexpense, name = 'roadexpense'),
    #report to convert in pdf
    path('dailytrans/', views.dailytrans, name = 'dailytrans'),

    #pdf rendering
    path('netbalpdf/', views.netbal_pdf_view, name = 'netbalpdf'),
    path('day_range_rec/', views.day_range_rec, name = 'day_range_rec'),
    path('cheque_alter/<int:ledger_no>/<int:pk>',views.cheque_alter,name='cheque_alter'),
    #AUTH
    path('login/', views.loginuser, name = 'loginuser'),
    path('logout/', views.logoutuser, name = 'logoutuser'),

]

# only in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


admin.site.index_title = "Web Ledger"
admin.site.site_header = "Only Admin Area"
