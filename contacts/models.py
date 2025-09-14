from django.db import models
from datetime import datetime, date
from cars.models import Car

# Create your models here.
class Contact(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('accepted', 'Accepté'),
        ('rejected', 'Refusé'),
    )
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    car_id = models.IntegerField()
    customer_need = models.CharField(max_length=100)
    car_title = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    user_id = models.IntegerField(blank=True)
    create_date = models.DateTimeField(blank=True, default=datetime.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Champs pour la location
    rental_start_date = models.DateField(null=True, blank=True, help_text="Date de début de location")
    rental_end_date = models.DateField(null=True, blank=True, help_text="Date de fin de location")
    rental_days = models.IntegerField(null=True, blank=True, help_text="Nombre de jours de location")
    total_rental_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Coût total de la location")

    def calculate_rental_cost(self):
        """Calcule le coût de location basé sur les dates et le prix par jour"""
        if self.rental_start_date and self.rental_end_date and self.car_id:
            try:
                car = Car.objects.get(id=self.car_id)
                # Calculer le nombre de jours
                delta = self.rental_end_date - self.rental_start_date
                self.rental_days = delta.days + 1  # +1 pour inclure le jour de début
                
                # Calculer le coût total en utilisant le prix de vente comme prix journalier
                if car.price:
                    self.total_rental_cost = self.rental_days * car.price
                else:
                    self.total_rental_cost = 0
            except Car.DoesNotExist:
                self.rental_days = 0
                self.total_rental_cost = 0
    
    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement le coût de location"""
        # Normaliser les dates si elles viennent en tant que chaînes (depuis request.POST)
        if isinstance(self.rental_start_date, str):
            try:
                self.rental_start_date = datetime.strptime(self.rental_start_date, '%Y-%m-%d').date()
            except ValueError:
                self.rental_start_date = None
        if isinstance(self.rental_end_date, str):
            try:
                self.rental_end_date = datetime.strptime(self.rental_end_date, '%Y-%m-%d').date()
            except ValueError:
                self.rental_end_date = None

        if self.rental_start_date and self.rental_end_date:
            self.calculate_rental_cost()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
