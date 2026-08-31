from django.db import models


class CertificatScolarite(models.Model):
    id_certificat = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Numéro certificat"
    )
    etudiant = models.ForeignKey(
        'api.Etudiant',
        on_delete=models.CASCADE,
        related_name='certificats_scolarite',
        verbose_name="Étudiant"
    )
    nom_pere = models.CharField(
        max_length=100,
        verbose_name="Nom du père",
        default="Non spécifié"
    )
    nom_mere = models.CharField(
        max_length=100,
        verbose_name="Nom de la mère",
        default="Non spécifiée"
    )
    date_naissance = models.DateField(
        verbose_name="Date de naissance",
        help_text="Format: JJ/MM/AAAA",
        null=True,
        blank=True
    )
    lieu_naissance = models.CharField(
        max_length=150,
        verbose_name="Lieu de naissance",
        help_text="Ville ou commune de naissance",
        null=True,
        blank=True
    )
    quantite = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre d'exemplaires",
        help_text="Nombre de certificats demandés"
    )
    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours de traitement'),
        ('pret', 'Prêt à retirer'),
    ]
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut de la demande"
    )

    def save(self, *args, **kwargs):
        if not self.id_certificat:
            dernier = CertificatScolarite.objects.order_by('-id').first()
            numero = (dernier.id + 1) if dernier else 1
            self.id_certificat = f"CERT-{numero:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_certificat} - {self.etudiant}"

    class Meta:
        verbose_name = "Certificat de scolarité"
        verbose_name_plural = "Certificats de scolarité"
        ordering = ['-date_demande']
