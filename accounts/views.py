from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.models import User
from contacts.models import Contact
from django.contrib.auth.decorators import login_required
from cars.models import Car
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.template.loader import get_template
from datetime import datetime, timedelta
import os
from io import BytesIO
from xhtml2pdf import pisa
from django.conf import settings

# Create your views here.

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')

def register(request):
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists!')
                return redirect('register')
            else:
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'Email already exists!')
                    return redirect('register')
                else:
                    user = User.objects.create_user(first_name=firstname, last_name=lastname, email=email, username=username, password=password)
                    auth.login(request, user)
                    messages.success(request, 'You are now logged in.')
                    return redirect('dashboard')
                    user.save()
                    messages.success(request, 'You are registered successfully.')
                    return redirect('login')
        else:
            messages.error(request, 'Password do not match')
            return redirect('register')
    else:
        return render(request, 'accounts/register.html')


@login_required(login_url = 'login')
def dashboard(request):
    if request.user.is_superuser:
        # Pour les administrateurs, rediriger vers le tableau de bord admin
        return redirect('admin_dashboard')
    else:
        # Pour les utilisateurs normaux, afficher leurs demandes
        user_inquiry = Contact.objects.order_by('-create_date').filter(user_id=request.user.id)
        # count = Contact.objects.order_by('-create_date').filter(user_id=request.user.id).count()

        data = {
            'inquiries': user_inquiry,
        }
        return render(request, 'accounts/dashboard.html', data)

@login_required(login_url = 'login')
def admin_dashboard(request):
    # Vérifier si l'utilisateur est un superutilisateur
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    # Statistiques pour le tableau de bord admin
    total_users = User.objects.count()
    total_inquiries = Contact.objects.count()
    
    # Récupérer les données pour les tableaux CRUD
    users = User.objects.all().order_by('-date_joined')
    inquiries = Contact.objects.all().order_by('-create_date')
    
    # Statistiques des voitures
    total_cars = Car.objects.count()
    cars = Car.objects.all().order_by('-created_date')
    
    context = {
        'total_users': total_users,
        'total_inquiries': total_inquiries,
        'total_cars': total_cars,
        'users': users,
        'inquiries': inquiries,
        'cars': cars,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)

def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        return redirect('home')
    return redirect('home')


# Fonctions CRUD pour les utilisateurs
@login_required(login_url = 'login')
def create_user(request):
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        user_role = request.POST.get('user_role', 'client')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà!')
            return redirect('create_user')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email existe déjà!')
            return redirect('create_user')
        
        # Définir les permissions selon le rôle
        is_staff = (user_role == 'admin')
        is_superuser = (user_role == 'admin')
        
        user = User.objects.create_user(
            first_name=firstname,
            last_name=lastname,
            username=username,
            email=email,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        user.save()
        messages.success(request, 'Utilisateur créé avec succès!')
        return redirect('admin_dashboard')
    
    return render(request, 'accounts/create_user.html')

@login_required(login_url = 'login')
def update_user(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST['firstname']
        user.last_name = request.POST['lastname']
        user.username = request.POST['username']
        user.email = request.POST['email']
        
        # Vérifier si le mot de passe doit être mis à jour
        if 'password' in request.POST and request.POST['password']:
            user.set_password(request.POST['password'])
        
        # Gérer le rôle utilisateur
        user_role = request.POST.get('user_role', 'client')
        user.is_staff = (user_role == 'admin')
        user.is_superuser = (user_role == 'admin')
        user.save()
        
        messages.success(request, 'Utilisateur mis à jour avec succès!')
        return redirect('admin_dashboard')
    
    context = {
        'user_data': user,
    }
    return render(request, 'accounts/update_user.html', context)

@login_required(login_url = 'login')
def delete_user(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, pk=user_id)
    
    # Empêcher la suppression de son propre compte
    if user.id == request.user.id:
        messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte!')
        return redirect('admin_dashboard')
    
    user.delete()
    messages.success(request, 'Utilisateur supprimé avec succès!')
    return redirect('admin_dashboard')


# Fonctions CRUD pour les voitures
@login_required(login_url = 'login')
def create_car(request):
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        car_title = request.POST['car_title']
        state = request.POST['state']
        city = request.POST['city']
        color = request.POST['color']
        model = request.POST['model']
        year = request.POST['year']
        condition = request.POST['condition']
        price = request.POST['price']
        description = request.POST['description']
        
        # Nouveaux champs ajoutés
        miles = request.POST.get('miles', '')
        if miles == '':
            miles = 0  # Valeur par défaut si vide
        else:
            miles = int(miles)
            
        doors = request.POST.get('doors', '')
        passengers = request.POST.get('passengers', '')
        if passengers == '':
            passengers = 0  # Valeur par défaut si vide
        else:
            passengers = int(passengers)
            
        milage = request.POST.get('milage', '')
        if milage == '':
            milage = 0  # Valeur par défaut si vide
        else:
            milage = int(milage)
            
        fuel_type = request.POST.get('fuel_type', '')
        no_of_owners = request.POST.get('no_of_owners', '')
        vin_no = request.POST.get('vin_no', '')
        body_style = request.POST.get('body_style', '')
        engine = request.POST.get('engine', '')
        transmission = request.POST.get('transmission', '')
        interior = request.POST.get('interior', '')
        features = request.POST.getlist('features[]')
        
        # Création de l'objet voiture
        car = Car(
            car_title=car_title,
            state=state,
            city=city,
            color=color,
            model=model,
            year=year,
            condition=condition,
            price=price,
            description=description,
            miles=miles,
            doors=doors,
            passengers=passengers,
            milage=milage,
            fuel_type=fuel_type,
            no_of_owners=no_of_owners,
            vin_no=vin_no,
            body_style=body_style,
            engine=engine,
            transmission=transmission,
            interior=interior,
            features=features,
        )
        
        # Traitement de la photo principale (obligatoire)
        if 'car_photo' in request.FILES:
            car.car_photo = request.FILES['car_photo']
        
        # Traitement des photos additionnelles (optionnelles)
        if 'car_photo_1' in request.FILES:
            car.car_photo_1 = request.FILES['car_photo_1']
            
        if 'car_photo_2' in request.FILES:
            car.car_photo_2 = request.FILES['car_photo_2']
            
        if 'car_photo_3' in request.FILES:
            car.car_photo_3 = request.FILES['car_photo_3']
            
        if 'car_photo_4' in request.FILES:
            car.car_photo_4 = request.FILES['car_photo_4']
            
        car.save()
        messages.success(request, 'Voiture ajoutée avec succès!')
        return redirect('admin_dashboard')
    
    # Récupérer les choix d'états pour le formulaire
    car_states = Car.state_choice
    
    context = {
        'car_states': car_states,
    }
    
    return render(request, 'accounts/create_car.html', context)

@login_required(login_url = 'login')
def update_car(request, car_id):
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    car = get_object_or_404(Car, pk=car_id)
    
    if request.method == 'POST':
        car.car_title = request.POST.get('car_title', '')
        car.state = request.POST.get('state', '')
        car.city = request.POST.get('city', '')
        car.color = request.POST.get('color', '')
        car.model = request.POST.get('model', '')
        car.year = request.POST.get('year', '')
        car.condition = request.POST.get('condition', '')
        car.price = request.POST.get('price', '')
        car.description = request.POST.get('description', '')
        
        # Mise à jour des nouveaux champs
        miles = request.POST.get('miles', '')
        if miles == '':
            car.miles = 0  # Valeur par défaut si vide
        else:
            car.miles = int(miles)
            
        car.doors = request.POST.get('doors', '')
        
        passengers = request.POST.get('passengers', '')
        if passengers == '':
            car.passengers = 0  # Valeur par défaut si vide
        else:
            car.passengers = int(passengers)
            
        milage = request.POST.get('milage', '')
        if milage == '':
            car.milage = 0  # Valeur par défaut si vide
        else:
            car.milage = int(milage)
        car.fuel_type = request.POST.get('fuel_type', '')
        car.no_of_owners = request.POST.get('no_of_owners', '')
        car.vin_no = request.POST.get('vin_no', '')
        car.body_style = request.POST.get('body_style', '')
        car.engine = request.POST.get('engine', '')
        car.transmission = request.POST.get('transmission', '')
        car.interior = request.POST.get('interior', '')
        car.features = request.POST.getlist('features[]')
        
        # Traitement de la photo principale
        if 'car_photo' in request.FILES:
            car.car_photo = request.FILES['car_photo']
        
        # Traitement des photos additionnelles
        if 'car_photo_1' in request.FILES:
            car.car_photo_1 = request.FILES['car_photo_1']
            
        if 'car_photo_2' in request.FILES:
            car.car_photo_2 = request.FILES['car_photo_2']
            
        if 'car_photo_3' in request.FILES:
            car.car_photo_3 = request.FILES['car_photo_3']
            
        if 'car_photo_4' in request.FILES:
            car.car_photo_4 = request.FILES['car_photo_4']
        
        car.save()
        messages.success(request, 'Voiture mise à jour avec succès!')
        return redirect('admin_dashboard')
    
    # Récupérer les choix d'états pour le formulaire
    car_states = Car.state_choice
    
    context = {
        'car': car,
        'car_states': car_states,
    }
    return render(request, 'accounts/update_car.html', context)

@login_required(login_url = 'login')
def delete_car(request, car_id):
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    car = get_object_or_404(Car, pk=car_id)
    car.delete()
    messages.success(request, 'Voiture supprimée avec succès!')
    return redirect('admin_dashboard')


# Fonctions CRUD pour les demandes
@login_required(login_url = 'login')
def inquiry_detail(request, inquiry_id):
    # Admin ou propriétaire peuvent voir la demande
    inquiry = get_object_or_404(Contact, pk=inquiry_id)
    if not request.user.is_superuser and request.user.id != inquiry.user_id:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    context = {
        'inquiry': inquiry,
    }
    return render(request, 'accounts/inquiry_detail.html', context)

@login_required(login_url = 'login')
def update_inquiry_status(request, inquiry_id):
    # Autorisé uniquement pour l'administrateur
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    if request.method != 'POST':
        return redirect('inquiry_detail', inquiry_id=inquiry_id)
    
    inquiry = get_object_or_404(Contact, pk=inquiry_id)
    status = request.POST.get('status')
    
    if status not in ['accepted', 'rejected']:
        messages.error(request, 'Statut invalide.')
        return redirect('inquiry_detail', inquiry_id=inquiry_id)
    
    inquiry.status = status
    inquiry.save()
    
    if status == 'accepted':
        messages.success(request, 'Demande acceptée avec succès!')
    else:
        messages.success(request, 'Demande refusée avec succès!')
    
    return redirect('inquiry_detail', inquiry_id=inquiry_id)

@login_required(login_url = 'login')
def delete_inquiry(request, inquiry_id):
    if not request.user.is_superuser:
        messages.error(request, 'Accès non autorisé. Vous devez être administrateur.')
        return redirect('dashboard')
    
    inquiry = get_object_or_404(Contact, pk=inquiry_id)
    inquiry.delete()
    messages.success(request, 'Demande supprimée avec succès!')
    return redirect('admin_dashboard')

@login_required(login_url = 'login')
def generate_invoice(request, inquiry_id):
    # Vérifier si l'utilisateur est un administrateur ou le propriétaire de la demande
    inquiry = get_object_or_404(Contact, pk=inquiry_id)
    
    if not request.user.is_superuser and request.user.id != inquiry.user_id:
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    # Vérifier que la demande est acceptée
    if inquiry.status != 'accepted':
        messages.error(request, 'Impossible de générer une facture pour une demande non acceptée.')
        return redirect('inquiry_detail', inquiry_id=inquiry_id) if request.user.is_superuser else redirect('dashboard')
    
    # Récupérer les informations de la voiture
    try:
        car = Car.objects.get(pk=inquiry.car_id)
    except Car.DoesNotExist:
        messages.error(request, 'La voiture associée à cette demande n\'existe plus.')
        return redirect('inquiry_detail', inquiry_id=inquiry_id) if request.user.is_superuser else redirect('dashboard')
    
    # Générer un numéro de facture unique
    invoice_number = f"INV-{inquiry.id}-{int(datetime.now().timestamp())}"
    
    # Préparer le contexte pour le template de facture
    context = {
        'inquiry': inquiry,
        'car': car,
        'invoice_number': invoice_number,
        'invoice_date': datetime.now().strftime('%d/%m/%Y'),
        'due_date': (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y'),
        'request': request,
        'STATIC_ROOT': settings.STATIC_ROOT,
    }
    
    # Si le paramètre download est présent, générer un PDF
    if request.GET.get('download'):
        template_path = 'accounts/invoice_pdf.html'
        template = get_template(template_path)
        html = template.render(context)
        
        # Créer un fichier PDF
        result = BytesIO()
        
        # Définir les options de conversion PDF
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
        }
        
        # Convertir HTML en PDF
        # Définir le chemin de base pour les ressources statiques
        base_url = request.build_absolute_uri('/').rstrip('/')
        
        # Fonction de callback pour gérer les chemins des ressources
        def link_callback(uri, rel):
            # Nettoyer l'URI
            if uri.startswith(('http://', 'https://', 'file://')):
                return uri
            
            # Gérer les chemins qui commencent par /accounts/static/ (problème spécifique)
            if uri.startswith('/accounts/static/'):
                uri = uri.replace('/accounts/static/', '/static/')
            
            # Utiliser directement STATIC_ROOT (staticfiles)
            if uri.startswith('/static/'):
                path = os.path.join(settings.STATIC_ROOT, uri.replace('/static/', ''))
            elif uri.startswith('static/'):
                path = os.path.join(settings.STATIC_ROOT, uri.replace('static/', ''))
            else:
                # Pour les chemins relatifs, essayer de les résoudre
                path = os.path.join(settings.STATIC_ROOT, uri)
            
            if not os.path.isfile(path):
                raise Exception('Ressource non trouvée : %s' % uri)
            return path
        
        pisa.CreatePDF(src=html, dest=result, link_callback=link_callback, encoding='utf-8')
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s.pdf"' % invoice_number
        return response
    
    # Sinon, afficher la page de facture HTML
    return render(request, 'accounts/invoice.html', context)
