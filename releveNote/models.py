# releveNote/models.py
from django.db import models
from django.core.exceptions import ValidationError


class ReleveNote(models.Model):
    NIVEAU_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]

    id_releve = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        blank=True,
        db_index=True
    )

    etudiant = models.ForeignKey(
        'api.Etudiant',
        on_delete=models.CASCADE,
        related_name='demandes_releve',
        db_index=True
    )

    demandes = models.JSONField(
        default=list,
        blank=True,
        help_text='Format: [{"niveau": "L1", "quantite": 2}]'
    )

    annee_universitaire = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Années universitaires",
        help_text='Format: [2022, 2023, 2024] ou ["2022", "2023"]'
    )

    date_demande = models.DateTimeField(auto_now_add=True, db_index=True)
    date_traitement = models.DateTimeField(null=True, blank=True)

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('pret', 'Prêt à retirer')
    ]
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='en_attente',
        db_index=True
    )

    class Meta:
        ordering = ['-date_demande']
        verbose_name = "Relevé de notes"
        verbose_name_plural = "Relevés de notes"
        indexes = [
            models.Index(fields=['etudiant', 'statut']),
            models.Index(fields=['date_demande']),
        ]

    def clean(self):
        if not isinstance(self.demandes, list):
            raise ValidationError({'demandes': 'Doit être une liste'})

        for demande in self.demandes:
            if not isinstance(demande, dict):
                raise ValidationError(
                    {'demandes': 'Chaque demande doit être un objet'})
            if 'niveau' not in demande or 'quantite' not in demande:
                raise ValidationError(
                    {'demandes': 'Chaque demande doit avoir "niveau" et "quantite"'})

        if not isinstance(self.annee_universitaire, list):
            raise ValidationError(
                {'annee_universitaire': 'Doit être une liste'})

    def total_exemplaires(self):
        return sum(item.get('quantite', 0) for item in self.demandes)

    def detail_niveaux(self):
        if not self.demandes:
            return "-"
        return " | ".join(
            [f"{d['quantite']}×{d['niveau']}" for d in self.demandes])

    def annees_formatees(self):
        annees = []
        if isinstance(self.annee_universitaire, int):
            return [self.annee_universitaire]
        if not self.annee_universitaire:
            return []
        annees_list = self.annee_universitaire if isinstance(
            self.annee_universitaire, list) else [self.annee_universitaire]
        for annee in annees_list:
            try:
                annees.append(int(annee) if isinstance(annee, str) else annee)
            except (ValueError, TypeError):
                continue
        return sorted(annees)

    def annees_display(self):
        annees = self.annees_formatees()
        if not annees:
            return "-"
        if len(annees) <= 3:
            return ", ".join(map(str, annees))
        return f"{', '.join(map(str, annees[:3]))}... (+{len(annees) - 3})"

    def save(self, *args, **kwargs):
        if not self.id_releve:
            dernier = ReleveNote.objects.order_by('-id').first()
            numero = (dernier.id + 1) if dernier else 1
            self.id_releve = f"R-{numero:04d}"

        self.demandes = self._normaliser_demandes(self.demandes)
        self.annee_universitaire = self._normaliser_annees(
            self.annee_universitaire)

        self.full_clean()

        super().save(*args, **kwargs)

    def _normaliser_demandes(self, demandes):
        if not isinstance(demandes, list):
            return []

        normalized = []
        for d in demandes:
            if isinstance(d, dict) and 'niveau' in d and 'quantite' in d:
                normalized.append({
                    'niveau': str(d['niveau']).upper(),
                    'quantite': int(d['quantite'])
                })
        return normalized

    def _normaliser_annees(self, annees):
        if not isinstance(annees, list):
            return []

        normalized = set()
        for annee in annees:
            if isinstance(annee, dict):
                annee = next(iter(annee.keys()), None)

            if annee:
                try:
                    annee_int = int(str(annee).strip())
                    if 2000 <= annee_int <= 2100:
                        normalized.add(annee_int)
                except (ValueError, TypeError):
                    continue

        return sorted(list(normalized))

    def __str__(self):
        return f"{self.id_releve} - {self.etudiant} ({self.annees_display()})"
