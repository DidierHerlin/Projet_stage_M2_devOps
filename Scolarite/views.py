from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from releveNote.models import ReleveNote
from CertificatScolarite.models import CertificatScolarite
from Attestation.models import Attestation
# 1. TABLEAU DE BORD UNIFIÉ - SCOLARITÉ UNIQUEMENT


class ToutesLesDemandesScolariteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'scolarite':
            return Response({
                "erreur": "Accès refusé. Réservé à la scolarité.",
                "votre_role": request.user.role
            }, status=status.HTTP_403_FORBIDDEN)
        statut_filter = request.query_params.get('statut', None)
        type_filter = request.query_params.get('type', None)
        date_debut = request.query_params.get('date_debut', None)
        date_fin = request.query_params.get('date_fin', None)
        demandes_unifiees = []
        # 1. RELEVÉS DE NOTES
        releves = ReleveNote.objects.select_related('etudiant__user').all()
        if statut_filter:
            releves = releves.filter(statut=statut_filter)
        if date_debut:
            try:
                date_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
                releves = releves.filter(date_demande__date__gte=date_obj)
            except ValueError:
                pass

        if date_fin:
            try:
                date_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
                releves = releves.filter(date_demande__date__lte=date_obj)
            except ValueError:
                pass

        for releve in releves:
            demandes_unifiees.append({
                'id': releve.id,
                'type_demande': 'releve',
                'numero': releve.id_releve,
                'etudiant': {
                    'immatricule': releve.etudiant.immatricule,
                    'nom_complet': f"{releve.etudiant.user.nom} {releve.etudiant.user.prenoms}".strip(),
                    'email': releve.etudiant.user.email,
                    'contact': releve.etudiant.contact
                },
                'details': {
                    'annee_universitaire': releve.annee_universitaire,
                    'niveaux': releve.detail_niveaux(),
                    'total_exemplaires': releve.total_exemplaires()
                },
                'statut': releve.statut,
                'statut_display': releve.get_statut_display(),
                'date_demande': releve.date_demande.strftime("%d/%m/%Y %H:%M") if releve.date_demande else None,
                'date_traitement': releve.date_traitement.strftime("%d/%m/%Y %H:%M") if releve.date_traitement else None
            })

        certificats = CertificatScolarite.objects.select_related(
            'etudiant__user').all()

        if statut_filter:
            certificats = certificats.filter(statut=statut_filter)
        if date_debut:
            try:
                date_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
                certificats = certificats.filter(
                    date_demande__date__gte=date_obj)
            except ValueError:
                pass

        if date_fin:
            try:
                date_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
                certificats = certificats.filter(
                    date_demande__date__lte=date_obj)
            except ValueError:
                pass

        for cert in certificats:
            demandes_unifiees.append({
                'id': cert.id,
                'type_demande': 'certificat',
                'numero': cert.id_certificat,
                'etudiant': {
                    'immatricule': cert.etudiant.immatricule,
                    'nom_complet': f"{cert.etudiant.user.nom} {cert.etudiant.user.prenoms}".strip(),
                    'email': cert.etudiant.user.email,
                    'contact': cert.etudiant.contact
                },
                'details': {
                    'nom_pere': cert.nom_pere,
                    'nom_mere': cert.nom_mere,
                    # AJOUTÉ
                    'date_naissance': cert.date_naissance.strftime("%Y-%m-%d") if cert.date_naissance else None,
                    'lieu_naissance': cert.lieu_naissance,  # AJOUTÉ
                    'quantite': cert.quantite
                },
                'statut': cert.statut,
                'statut_display': cert.get_statut_display(),
                'date_demande': cert.date_demande.strftime("%d/%m/%Y %H:%M") if cert.date_demande else None,
                'date_traitement': cert.date_traitement.strftime("%d/%m/%Y %H:%M") if cert.date_traitement else None
            })

        # 3. ATTESTATIONS (CORRIGÉ - avec annee_scolaire au lieu de
        # annee_universitaire)
        attestations = Attestation.objects.select_related(
            'etudiant__user').all()

        if statut_filter:
            attestations = attestations.filter(statut=statut_filter)

        # Filtre par date
        if date_debut:
            try:
                date_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
                attestations = attestations.filter(
                    date_demande__date__gte=date_obj)
            except ValueError:
                pass

        if date_fin:
            try:
                date_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
                attestations = attestations.filter(
                    date_demande__date__lte=date_obj)
            except ValueError:
                pass

        for att in attestations:
            demandes_unifiees.append({
                'id': att.id,
                'type_demande': 'attestation',
                'numero': att.id_attestation,
                'etudiant': {
                    'immatricule': att.etudiant.immatricule,
                    'nom_complet': f"{att.etudiant.user.nom} {att.etudiant.user.prenoms}".strip(),
                    'email': att.etudiant.user.email,
                    'contact': att.etudiant.contact
                },
                'details': {
                    'type_attestation': att.type_attestation,
                    'type_display': att.get_type_attestation_display(),
                    # CORRIGÉ : annee_scolaire au lieu de annee_universitaire
                    'annee_scolaire': att.annee_scolaire,
                    'quantite': att.quantite,  # CORRIGÉ : quantite au lieu de nombre_exemplaires
                    'prix': float(att.prix),
                    'total_paye': float(att.total_paye)
                },
                'statut': att.statut,
                'statut_display': att.get_statut_display(),
                'date_demande': att.date_demande.strftime("%d/%m/%Y %H:%M") if att.date_demande else None,
                'date_traitement': att.date_traitement.strftime("%d/%m/%Y %H:%M") if att.date_traitement else None
            })

        if type_filter:
            demandes_unifiees = [
                d for d in demandes_unifiees if d['type_demande'] == type_filter]

        try:
            demandes_unifiees.sort(
                key=lambda x: datetime.strptime(
                    x['date_demande'],
                    "%d/%m/%Y %H:%M") if x['date_demande'] else datetime.min,
                reverse=True)
        except (ValueError, TypeError):
            demandes_unifiees.sort(key=lambda x: x['id'], reverse=True)

        stats = {
            'total': len(demandes_unifiees),
            'par_type': {
                'releves': len([d for d in demandes_unifiees if d['type_demande'] == 'releve']),
                'certificats': len([d for d in demandes_unifiees if d['type_demande'] == 'certificat']),
                'attestations': len([d for d in demandes_unifiees if d['type_demande'] == 'attestation'])
            },
            'par_statut': {
                'en_attente': len([d for d in demandes_unifiees if d['statut'] == 'en_attente']),
                'en_cours': len([d for d in demandes_unifiees if d['statut'] == 'en_cours']),
                'pret': len([d for d in demandes_unifiees if d['statut'] == 'pret']),
                'retire': len([d for d in demandes_unifiees if d['statut'] == 'retire']),
                'rejete': len([d for d in demandes_unifiees if d['statut'] == 'rejete'])
            }
        }

        return Response({
            "success": True,
            "stats": stats,
            "demandes": demandes_unifiees,
            "filtres_appliques": {
                "statut": statut_filter,
                "type": type_filter,
                "date_debut": date_debut,
                "date_fin": date_fin
            }
        }, status=status.HTTP_200_OK)


# 2. CHANGER LE STATUT D'UNE DEMANDE - SCOLARITÉ UNIQUEMENT

class ChangerStatutDemandeUnifieeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Vérification stricte du rôle
        if request.user.role != 'scolarite':
            return Response({
                "erreur": "Accès refusé. Réservé à la scolarité.",
                "votre_role": request.user.role
            }, status=status.HTTP_403_FORBIDDEN)

        type_demande = request.data.get('type_demande')
        demande_id = request.data.get('id')
        nouveau_statut = request.data.get('nouveau_statut')
        motif = request.data.get('motif', '')

        if not all([type_demande, demande_id, nouveau_statut]):
            return Response({
                "erreur": "Champs manquants",
                "requis": ["type_demande", "id", "nouveau_statut"],
                "exemple": {
                    "type_demande": "releve",
                    "id": 1,
                    "nouveau_statut": "pret"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if type_demande == 'releve':
                demande = ReleveNote.objects.select_related(
                    'etudiant__user').get(id=demande_id)
                statuts_valides = [
                    'en_attente',
                    'en_cours',
                    'pret',
                    'retire',
                    'rejete']
            elif type_demande == 'certificat':
                demande = CertificatScolarite.objects.select_related(
                    'etudiant__user').get(id=demande_id)
                statuts_valides = [
                    'en_attente',
                    'en_cours',
                    'pret',
                    'retire',
                    'rejete']
            elif type_demande == 'attestation':
                demande = Attestation.objects.select_related(
                    'etudiant__user').get(id=demande_id)
                statuts_valides = [
                    'en_attente',
                    'en_cours',
                    'pret',
                    'retire',
                    'rejete']
            else:
                return Response({
                    "erreur": "Type de demande invalide",
                    "types_valides": ["releve", "certificat", "attestation"]
                }, status=status.HTTP_400_BAD_REQUEST)

            if nouveau_statut not in statuts_valides:
                return Response({
                    "erreur": f"Statut invalide. Statuts valides: {', '.join(statuts_valides)}"
                }, status=status.HTTP_400_BAD_REQUEST)

            if nouveau_statut == 'rejete' and not motif:
                return Response({
                    "erreur": "Le motif est obligatoire pour rejeter une demande"
                }, status=status.HTTP_400_BAD_REQUEST)

            ancien_statut = demande.get_statut_display()

            demande.statut = nouveau_statut
            if nouveau_statut in ['pret', 'retire', 'rejete']:
                demande.date_traitement = timezone.now()

            demande.save()

            email_envoye = self._envoyer_notification(
                demande, type_demande, ancien_statut, nouveau_statut, motif)

            return Response({
                "success": True,
                "message": "Statut mis à jour avec succès",
                "demande": {
                    "type": type_demande,
                    "id": demande.id,
                    "numero": self._get_numero(demande, type_demande),
                    "ancien_statut": ancien_statut,
                    "nouveau_statut": demande.get_statut_display()
                },
                "email_envoye": email_envoye
            }, status=status.HTTP_200_OK)

        except (ReleveNote.DoesNotExist, CertificatScolarite.DoesNotExist, Attestation.DoesNotExist):
            return Response({
                "erreur": "Demande introuvable",
                "type": type_demande,
                "id": demande_id
            }, status=status.HTTP_404_NOT_FOUND)

    def _get_numero(self, demande, type_demande):
        if type_demande == 'releve':
            return demande.id_releve
        elif type_demande == 'certificat':
            return demande.id_certificat
        else:
            return demande.id_attestation

    def _envoyer_notification(
            self,
            demande,
            type_demande,
            ancien_statut,
            nouveau_statut,
            motif):
        try:
            user = demande.etudiant.user
            nom = f"{user.nom} {user.prenoms}".strip()
            numero = self._get_numero(demande, type_demande)

            type_labels = {
                'releve': 'relevé de notes',
                'certificat': 'certificat de scolarité',
                'attestation': 'attestation'
            }

            type_label = type_labels.get(type_demande, type_demande)

            if nouveau_statut == 'pret':
                sujet = f" Votre {type_label} {numero} est prêt !"
                message = f"""Bonjour {nom},

                Bonne nouvelle ! Votre {type_label} est maintenant prêt à être retiré.

                Numéro : {numero}
                Date de traitement : {timezone.now().strftime('%d/%m/%Y à %H:%M')}

                Merci de passer à la scolarité pendant les heures d'ouverture pour le récupérer.

                Cordialement,
                Le Service de la Scolarité"""

            elif nouveau_statut == 'en_cours':
                sujet = f" Votre {type_label} {numero} est en cours de traitement"
                message = f"""Bonjour {nom},

                Votre demande de {type_label} est actuellement en cours de traitement.

                 Numéro : {numero}
                 Mise à jour : {timezone.now().strftime('%d/%m/%Y à %H:%M')}

                Nous vous préviendrons dès qu'elle sera prête.

                Cordialement,
                Le Service de la Scolarité"""

            elif nouveau_statut == 'rejete':
                sujet = f" Votre demande {numero} a été refusée"
                message = f"""Bonjour {nom},

            Votre demande de {type_label} a malheureusement été refusée.

            Numéro : {numero}
            Date : {timezone.now().strftime('%d/%m/%Y à %H:%M')}
            Motif : {motif}

            Merci de contacter la scolarité pour plus d'informations.

            Cordialement,
            Le Service de la Scolarité"""

            elif nouveau_statut == 'retire':
                sujet = f" Confirmation de retrait - {type_label} {numero}"
                message = f"""Bonjour {nom},

            Nous confirmons le retrait de votre {type_label}.

            Numéro : {numero}
            Date de retrait : {timezone.now().strftime('%d/%m/%Y à %H:%M')}

            Merci et bonne continuation !

            Cordialement,
            Le Service de la Scolarité"""

            else:
                # Message générique
                sujet = f"Mise à jour - {type_label} {numero}"
                message = f"""Bonjour {nom},

        Le statut de votre {type_label} a été mis à jour.

        Numéro : {numero}
        Ancien statut : {ancien_statut}
        Nouveau statut : {demande.get_statut_display()}
        Date : {timezone.now().strftime('%d/%m/%Y à %H:%M')}

        Cordialement,
        Le Service de la Scolarité"""

            # Envoi de l'email
            send_mail(
                subject=sujet,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'scolarite@ecole.com',
                recipient_list=[
                    user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f" Erreur envoi email : {e}")
            return False


# 3. STATISTIQUES - SCOLARITÉ UNIQUEMENT

class StatistiquesScolariteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'scolarite':
            return Response({
                "erreur": "Accès refusé. Réservé à la scolarité.",
                "votre_role": request.user.role
            }, status=status.HTTP_403_FORBIDDEN)

        aujourd_hui = timezone.now().date()
        debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
        debut_mois = aujourd_hui.replace(day=1)

        stats = {
            'total_demandes': 0,
            'par_type': {
                'releves': ReleveNote.objects.count(),
                'certificats': CertificatScolarite.objects.count(),
                'attestations': Attestation.objects.count()
            },
            'par_statut': {
                'en_attente': 0,
                'en_cours': 0,
                'pret': 0,
                'retire': 0,
                'rejete': 0
            },
            'demandes_recentes': {
                'aujourdhui': 0,
                'cette_semaine': 0,
                'ce_mois': 0
            }
        }

        stats['total_demandes'] = sum(stats['par_type'].values())

        for statut in ['en_attente', 'en_cours', 'pret', 'retire', 'rejete']:
            stats['par_statut'][statut] = (
                ReleveNote.objects.filter(statut=statut).count() +
                CertificatScolarite.objects.filter(statut=statut).count() +
                Attestation.objects.filter(statut=statut).count()
            )

        stats['demandes_recentes']['aujourdhui'] = (
            ReleveNote.objects.filter(
                date_demande__date=aujourd_hui).count() +
            CertificatScolarite.objects.filter(
                date_demande__date=aujourd_hui).count() +
            Attestation.objects.filter(
                date_demande__date=aujourd_hui).count())

        stats['demandes_recentes']['cette_semaine'] = (
            ReleveNote.objects.filter(
                date_demande__date__gte=debut_semaine).count() +
            CertificatScolarite.objects.filter(
                date_demande__date__gte=debut_semaine).count() +
            Attestation.objects.filter(
                date_demande__date__gte=debut_semaine).count())

        stats['demandes_recentes']['ce_mois'] = (
            ReleveNote.objects.filter(
                date_demande__date__gte=debut_mois).count() +
            CertificatScolarite.objects.filter(
                date_demande__date__gte=debut_mois).count() +
            Attestation.objects.filter(
                date_demande__date__gte=debut_mois).count())

        if stats['total_demandes'] > 0:
            pourcentages = {}
            for statut, count in stats['par_statut'].items():
                pourcentages[statut] = round(
                    (count / stats['total_demandes']) * 100, 1)
            stats['pourcentages_statut'] = pourcentages

        evolution = []
        for i in range(4):
            debut = aujourd_hui - timedelta(days=aujourd_hui.weekday() + 7 * i)
            fin = debut + timedelta(days=6)

            total_semaine = (
                ReleveNote.objects.filter(
                    date_demande__date__range=[
                        debut,
                        fin]).count() +
                CertificatScolarite.objects.filter(
                    date_demande__date__range=[
                        debut,
                        fin]).count() +
                Attestation.objects.filter(
                    date_demande__date__range=[
                        debut,
                        fin]).count())

            evolution.append({
                'semaine': f"Sem {4 - i}",
                'debut': debut.strftime("%d/%m"),
                'fin': fin.strftime("%d/%m"),
                'total': total_semaine
            })

        evolution.reverse()

        return Response({
            "success": True,
            "statistiques": stats,
            "evolution_hebdomadaire": evolution,
            "periode": {
                "aujourdhui": aujourd_hui.strftime("%d/%m/%Y"),
                "debut_semaine": debut_semaine.strftime("%d/%m/%Y"),
                "debut_mois": debut_mois.strftime("%d/%m/%Y")
            }
        }, status=status.HTTP_200_OK)


# 4. RECHERCHE D'UNE DEMANDE PAR NUMÉRO - SCOLARITÉ UNIQUEMENT

class RechercherDemandeParNumeroView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'scolarite':
            return Response({
                "erreur": "Accès refusé. Réservé à la scolarité.",
                "votre_role": request.user.role
            }, status=status.HTTP_403_FORBIDDEN)

        numero = request.query_params.get('numero', '').strip()

        if not numero:
            return Response({
                "erreur": "Le paramètre 'numero' est requis",
                "exemples": [
                    "/api/scolarite/rechercher-demande/?numero=REL-0001",
                    "/api/scolarite/rechercher-demande/?numero=CERT-0001",
                    "/api/scolarite/rechercher-demande/?numero=A-0001"
                ]
            }, status=status.HTTP_400_BAD_REQUEST)

        resultats = []

        try:
            releve = ReleveNote.objects.select_related(
                'etudiant__user').get(id_releve__iexact=numero)
            resultats.append({
                'type': 'releve',
                'id': releve.id,
                'numero': releve.id_releve,
                'etudiant': {
                    'immatricule': releve.etudiant.immatricule,
                    'nom_complet': f"{releve.etudiant.user.nom} {releve.etudiant.user.prenoms}".strip(),
                    'email': releve.etudiant.user.email
                },
                'details': {
                    'annee_universitaire': releve.annee_universitaire,
                    'niveaux': releve.detail_niveaux(),
                    'total_exemplaires': releve.total_exemplaires()
                },
                'statut': releve.get_statut_display(),
                'date_demande': releve.date_demande.strftime("%d/%m/%Y %H:%M") if releve.date_demande else None
            })
        except ReleveNote.DoesNotExist:
            pass

        try:
            cert = CertificatScolarite.objects.select_related(
                'etudiant__user').get(id_certificat__iexact=numero)
            resultats.append({
                'type': 'certificat',
                'id': cert.id,
                'numero': cert.id_certificat,
                'etudiant': {
                    'immatricule': cert.etudiant.immatricule,
                    'nom_complet': f"{cert.etudiant.user.nom} {cert.etudiant.user.prenoms}".strip(),
                    'email': cert.etudiant.user.email
                },
                'details': {
                    'nom_pere': cert.nom_pere,
                    'nom_mere': cert.nom_mere,
                    'quantite': cert.quantite
                },
                'statut': cert.get_statut_display(),
                'date_demande': cert.date_demande.strftime("%d/%m/%Y %H:%M") if cert.date_demande else None
            })
        except CertificatScolarite.DoesNotExist:
            pass

        try:
            att = Attestation.objects.select_related(
                'etudiant__user').get(id_attestation__iexact=numero)
            resultats.append({
                'type': 'attestation',
                'id': att.id,
                'numero': att.id_attestation,
                'etudiant': {
                    'immatricule': att.etudiant.immatricule,
                    'nom_complet': f"{att.etudiant.user.nom} {att.etudiant.user.prenoms}".strip(),
                    'email': att.etudiant.user.email
                },
                'details': {
                    'type': att.get_type_attestation_display(),
                    'annee_scolaire': att.annee_scolaire,
                    'quantite': att.quantite,
                    'prix': float(att.prix),
                    'total_paye': float(att.total_paye)
                },
                'statut': att.get_statut_display(),
                'date_demande': att.date_demande.strftime("%d/%m/%Y %H:%M") if att.date_demande else None
            })
        except Attestation.DoesNotExist:
            pass

        if not resultats:
            return Response({
                "success": False,
                "erreur": f"Aucune demande trouvée avec le numéro '{numero}'",
                "suggestions": [
                    "Vérifiez le numéro de la demande",
                    "Les numéros sont sensibles à la casse"
                ]
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "resultats": resultats,
            "total": len(resultats)
        }, status=status.HTTP_200_OK)
