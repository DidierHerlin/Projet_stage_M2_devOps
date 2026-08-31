# attestation/models.py
from django.db import models


class Attestation(models.Model):
    TYPE_ATTESTATION_CHOICES = [
        ('reussite', 'Attestation de Réussite'),
        ('inscription', 'Inscription'),
        ('langue', 'Langue Française d’Apprentissage'),
        ('duree', 'Durée de Formation'),
        ('fin_l3', 'Fin d’Études L3'),
        ('fin_m2', 'Fin d’Études M2'),
    ]

    id_attestation = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
        blank=True)
    etudiant = models.ForeignKey(
        'api.Etudiant',
        on_delete=models.CASCADE,
        related_name='attestations')
    type_attestation = models.CharField(
        max_length=20, choices=TYPE_ATTESTATION_CHOICES)
    annee_scolaire = models.CharField(max_length=9, blank=True, null=True)

    quantite = models.PositiveIntegerField(default=1)
    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=3000.00,
        verbose_name="Prix unitaire (Ariary)"
    )
    total_paye = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False)

    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('pret', 'Prêt à retirer'),
    ]
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='en_attente')

    def save(self, *args, **kwargs):
        if not self.id_attestation:
            dernier = Attestation.objects.order_by('-id').first()
            numero = (dernier.id + 1) if dernier else 1
            self.id_attestation = f"A-{numero:04d}"

        self.total_paye = self.prix * self.quantite
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_attestation} - {self.etudiant}"

    class Meta:
        verbose_name = "Attestation"
        ordering = ['-date_demande']
