import json
import datetime, csv
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import dateutil.relativedelta as delta
import dateutil.parser as parser
from django.contrib import messages
from django import forms
from .forms import AddUserForm, UpdateUserInForm, UpdateUserForm
from django.db.models.signals import post_save
from django.db.models import Q

class SearchForm(forms.Form):
    search = forms.CharField(label='Search User', max_length=100, required=False)
    def clean_search(self, *args, **kwargs):
        search = self.cleaned_data.get('search')
        if search == '':
            raise forms.ValidationError('Please enter a name in search box')
        return search

def my_handler(sender, instance, created, **kwargs):
    query = Q(
            Q(registration_upto__gte=datetime.datetime.today()),
            Q(registration_upto__lte=datetime.datetime.today() + datetime.timedelta(days=1)),
            Q(Q(notification=2) | Q(notification=0)))
    # last five days = datetime.date.today() - datetime.timedelta(days=5)
    users_before = User.objects.filter(
        registration_upto__lte=datetime.datetime.today())
    users_today = User.objects.filter(query)
    count = 0
    # make notification flag to 1
    for user in users_today | users_before:
        if user.notification != 0:
            user.notification = 1
            user.fee_status = 'pending'
            user.save()
    return

post_save.connect(my_handler, sender=User)

def model_save(model):
    post_save.disconnect(my_handler, sender=User)
    model.save()
    post_save.connect(my_handler, sender=User)

def check_status(request, object):
    object.stop = 1 if request.POST.get('stop') == '1' else 0
    return object

def index(request):
    return render(request, 'membership/index.html')

def search_user(request):
    if request.method == 'POST':
        if 'clear' in request.POST:
            return redirect('view_user')
        search_form = SearchForm(request.POST)
        result = 0
        if search_form.is_valid():
            first_name = request.POST.get('search')
            result = User.objects.filter(first_name__icontains=first_name)
        view_all = User.objects.all()
        context = {
            'all': view_all,
            'search_form': search_form,
            'result': result,
            }
        return render(request, 'membership/view_user.html', context)
    else:
        search_form = SearchForm()
    return render(request, 'membership/view_user.html', {'search_form': search_form})
# Export user information.
def export_all(user_obj):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['First name', 'Last name', 'Email', 'Dob', 'registration_date', 'amount', 'subscription_type'])
    users = user_obj.values_list('first_name', 'last_name', 'email', 'birth_date', 'registration_date', 'amount', 'subscription_type')
    for user in users:
        first_name = user[0]
        last_name = user[1]
        writer.writerow(user)
    response['Content-Disposition'] = 'attachment; filename="' + first_name + ' ' + last_name + '.csv"'
    return response

def users(request):
    form = AddUserForm()
    context = {
        'form': form,
        }
    return render(request, 'membership/add_user.html', context)

@login_required
def view_user(request):
    view_all = User.objects.filter(stop=0).order_by('id')
    paginator = Paginator(view_all, 10)
    try:
        page = request.GET.get('page', 1)
        view_all = paginator.page(page)
    except PageNotAnInteger:
        view_all = paginator.page(1)
    except EmptyPage:
        view_all = paginator.page(paginator.num_pages)
    search_form = SearchForm()
    stopped = User.objects.filter(stop=1).order_by('id')
    context = {
        'all': view_all,
        'stopped': stopped,
        'search_form': search_form,
    }
    return render(request, 'membership/view_user.html', context)

@login_required
def add_user(request):
    success = 0
    current_user = request.user
    if request.method == 'POST':
        user = User.objects.get(pk=current_user.id)
        form = AddUserForm(request.POST, instance=user)
        if form.is_valid():
            temp = form.save(commit=False)
            temp.first_name = request.POST.get('first_name').capitalize()
            temp.last_name = request.POST.get('last_name').capitalize()
            temp.registration_date = parser.parse(request.POST.get('registration_date'))
            temp.registration_upto = parser.parse(request.POST.get('registration_date')) + delta.relativedelta(months=1)
            if request.POST.get('fee_status') == 'pending':
                temp.notification = 1
            else:
                temp.notification = 2
            model_save(temp)
            success = 'Succesfully added user'
            form = AddUserForm()
            user = User.objects.last()
            context = {
            'add_success': success,
                'form': form,
                'user': user,
            }
            return render(request, 'membership/add_user.html', context)
        else:
            form = AddUserForm()
            context = {
                'form': form,
        }
    return render(request, 'membership/add_user.html', context)

@csrf_exempt
def register(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        if User.objects.filter(username=username).exists():
            return JsonResponse({"message": "username exists"})
        email = data.get("email")
        password = data.get("password")
        confirm = data.get("confirm")
        if password != confirm:
            return JsonResponse({"message": "Passwords must match."})
        try:
            new_user = User.objects.create_user(username, email, password)
            new_user.save()
        except IntegrityError:
            return JsonResponse({"message": "Username already taken."})

        login(request, new_user)
        return JsonResponse({"message": "User created successfully."}, status=201)

    else:
        return JsonResponse({"error": "POST request required."}, status=400)

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"message": "User logged in successfully."}, status=201)
        else:
            return JsonResponse({"message": "Invalid username and/or password."})
    else:
        return JsonResponse({"error": "POST request required."}, status=400)

def delete_user(request, id):
    print(id)
    User.objects.filter(pk=id).delete()
    return render(request, 'membership/view_user.html')

@login_required
def update_user(request, id):
    if request.method == 'POST' and request.POST.get('export'):
        return export_all(User.objects.filter(pk=id))
    if request.method == 'POST' and request.POST.get('no'):
        return redirect('/')
    if request.method == 'POST' and request.POST.get('membership'):
            isk_form = UpdateUserForm(request.POST)
            if isk_form.is_valid():
                object = User.objects.get(pk=id)
                amount = request.POST.get('amount')
                day = (parser.parse(request.POST.get('registration_upto')) - delta.relativedelta(months=+1)).day
                last_day = parser.parse(str(object.registration_upto)).day
                month = parser.parse(request.POST.get('registration_upto')).month
                last_month = parser.parse(str(object.registration_upto)).month
                # if status is stopped then do not update anything
                if object.stop == 1 and not request.POST.get('stop') == '0' and request.POST.get('membership'):
                    messages.error(request, 'Please start the status of user to update the record')
                    return redirect('update_user', id=object.pk)
                # if user has modified only the date
                elif (datetime.datetime.strptime(str(object.registration_date), "%Y-%m-%d") != datetime.datetime.strptime(request.POST.get('registration_date'), "%Y-%m-%d")):
                    object.registration_date =  parser.parse(request.POST.get('registration_date'))
                    object.registration_upto =  parser.parse(request.POST.get('registration_date')) + delta.relativedelta(months=+1)
                    object.fee_status = request.POST.get('fee_status')
                    object = check_status(request, object)
                    model_save(object)
                # if  amount and types are changed
                elif (object.amount != amount) and (object.subscription_type != request.POST.get('subscription_type')):
                    object.subscription_type =  request.POST.get('subscription_type')
                    object.registration_date =  parser.parse(request.POST.get('registration_upto'))
                    object.registration_upto =  parser.parse(request.POST.get('registration_upto')) + delta.relativedelta(months=+1)
                    object.fee_status = request.POST.get('fee_status')
                    object.amount =  request.POST.get('amount')
                    object = check_status(request, object)
                    model_save(object)
                    #if amount and fee status are changes
                elif (object.amount != amount) and ((request.POST.get('fee_status') == 'paid') or (request.POST.get('fee_status') == 'pending')):
                    object.amount = amount
                    object.fee_status = request.POST.get('fee_status')
                    object = check_status(request, object)
                    model_save(object)
                # if only amount is channged
                elif (object.amount != amount):
                    object.registration_date =  parser.parse(request.POST.get('registration_upto'))
                    object.registration_upto =  parser.parse(request.POST.get('registration_upto')) + delta.relativedelta(months=+1)
                    object.fee_status = request.POST.get('fee_status')
                    object.amount =  request.POST.get('amount')
                    if request.POST.get('fee_status') == 'pending':
                        object.notification =  1
                    elif request.POST.get('fee_status') == 'paid':
                        object.notification = 2
                    object = check_status(request, object)
                    model_save(object)
                    # nothing is changed
                else:
                    if not request.POST.get('stop') == '1':
                        object.registration_date =  parser.parse(request.POST.get('registration_date'))
                        object.registration_upto =  parser.parse(request.POST.get('registration_upto')) + delta.relativedelta(months=+1)
                        object.amount =  request.POST.get('amount')
                        if request.POST.get('fee_status') == 'pending':
                            object.notification =  1
                        elif request.POST.get('fee_status') == 'paid':
                            object.notification = 2
                    object.fee_status = request.POST.get('fee_status')
                    object = check_status(request, object)
                    model_save(object)

                user = User.objects.get(pk=id)
                isk_form = UpdateUserForm(initial={
                                    'registration_upto': user.registration_upto,
                                    'subscription_type': user.subscription_type,
                                    'registration_date': user.registration_date,
                                    'amount': user.amount,
                                    'fee_status': user.fee_status,
                                    'stop': user.stop,
                                    })

                info_form = UpdateUserInForm(initial={
                                    'first_name': user.first_name,
                                    'last_name': user.last_name,
                                    'birth_date': user.birth_date,
                                    'email': user.email,
                                    })
                messages.success(request, 'Record updated successfully!')
                return redirect('update_user', id=object.pk)
            else:
                user = User.objects.get(pk=id)
                info_form = UpdateUserInForm(initial={
                                    'first_name': user.first_name,
                                    'last_name': user.last_name,
                                    'birth_date': user.birth_date,
                                    'email': user.email,
                                    })
                return render(request,
                    'membership/update.html',
                    {
                        'isk_form': isk_form,
                        'info_form': info_form,
                        'user': user,
                    })
    elif request.method == 'POST' and request.POST.get('info'):
        object = User.objects.get(pk=id)
        object.first_name = request.POST.get('first_name')
        object.last_name = request.POST.get('last_name')
        object.birth_date = request.POST.get('birth_date')
        object.email = request.POST.get('email')
        model_save(object)

        user = User.objects.get(pk=id)
        isk_form = UpdateUserForm(initial={
                                'registration_upto': user.registration_upto,
                                'subscription_type': user.subscription_type,
                                'registration_date': user.registration_date,
                                'stop': user.stop,
                                'amount': user.amount,
                                'fee_status': user.fee_status,
                                })
        info_form = UpdateUserInForm(initial={
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'birth_date': user.birth_date,
                                'email': user.email,
                                })
        return render(request,
            'membership/update.html',
            {
                'isk_form': isk_form,
                'info_form': info_form,
                'user': user,
                'updated': 'Record Updated Successfully',
            })
    else:
        user = User.objects.get(pk=id)

        isk_form = UpdateUserForm(initial={
                                'registration_upto': user.registration_upto,
                                'subscription_type': user.subscription_type,
                                'registration_date': user.registration_date,
                                'amount': user.amount,
                                'fee_status': user.fee_status,
                                'stop': user.stop,
                                })

        info_form = UpdateUserInForm(initial={
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'birth_date': user.birth_date,
                                'email': user.email,
                                })
        return render(request,
            'membership/update.html',
            {
                'isk_form': isk_form,
                'info_form': info_form,
                'user': user,
            })

def logout_view(request):
    request.session.flush()
    logout(request)
    return HttpResponseRedirect(reverse("index"))
