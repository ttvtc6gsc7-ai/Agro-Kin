"""Reconstruit la documentation statique, sans modifier le backend ni ses données."""
from pathlib import Path
import ast
import html
import re
import sqlite3
import os

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
BACK = ROOT / 'backend'
esc = html.escape

def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'

def ref(file):
    return '<a class="source" href="#src-'+file.replace('/','-').replace('.','-')+'">Source : '+file+'</a>'

sections=[]
def section(id, title, body):
    sections.append((id,title,body))

section('lecture','Avant de commencer', '''
<p class="lead">Du capteur à la décision d’arroser : comprendre les données, les règles et les limites du système.</p>
<p>Cette documentation décrit le dépôt <strong>RoboAgri-Kin</strong>, confirmé comme le projet à analyser. Elle est fondée sur les fichiers locaux examinés le <strong>18 novembre 2026</strong>. Les comportements décrits viennent du code exécutable ; les anciens README ne font pas autorité lorsqu’ils le contredisent.</p>
<div class="callout"><strong>Ce que le système fait.</strong> Il organise les parcelles et les missions d’un robot agricole, reçoit des mesures d’humidité, les convertit grâce à un étalonnage et propose une irrigation. Un humain autorise l’opération ; le robot rapporte ensuite son résultat.</div>
<p>Il s’agit d’un monolithe Django : une application serveur, plusieurs modules métier, une base SQLite et une API REST. Aucun moteur d’intelligence artificielle, broker MQTT, ordonnanceur de tâches ou firmware ESP32 n’est implémenté dans le périmètre Python examiné. Le dossier <code>robot/</code> ne contient que <code>.gitkeep</code>.</p>
<p><strong>Parcours conseillé :</strong> lire l’architecture, les relations, puis les trois parcours métier. Les développeurs peuvent ensuite ouvrir le dictionnaire de tous les champs et l’explorateur de code. Les responsables de projet trouveront les écarts et travaux restants dans « Limites et priorités ».</p>
<p>La documentation fonctionne hors ligne, sans serveur, bibliothèque externe ni appel à la base. Le code intégré est un instantané ; la clé secrète Django a été retirée. Aucun mot de passe de compte, jeton de robot ou contenu de session n’a été extrait de la base.</p>
''')

section('architecture','Architecture et trajet d’une requête', '''
<div class="flow"><span>Navigateur<br><small>session + CSRF</small></span><b>→</b><span>Routes Django<br><small>API / pages</small></span><b>→</b><span>Vues et serializers<br><small>identité, droits, entrée</small></span><b>→</b><span>Services métier<br><small>règles et transactions</small></span><b>→</b><span>ORM → SQLite<br><small>persistance</small></span></div>
<p>Le robot utilise les mêmes routes serveur sous <code>/api/robot/</code>, avec une authentification distincte. Une requête arrive dans <code>roboagri_config/urls.py</code>, puis dans <code>api/urls.py</code>. DRF authentifie l’appelant, contrôle ses droits, puis exécute la vue. Un serializer transforme et valide les données JSON. Les opérations métier complexes appellent un service ; les CRUD simples utilisent directement le ModelViewSet et l’ORM.</p>
<p>L’ORM traduit les opérations Python en requêtes SQL. La réponse repasse par un serializer pour obtenir un JSON. Les exceptions métier prévues sont souvent converties en erreurs HTTP 400. Les erreurs non traitées peuvent produire une erreur serveur : toute erreur n’est donc pas automatiquement normalisée.</p>
<h3>Responsabilité de chaque dossier</h3>
'''+table(['Dossier','Responsabilité'],[
('roboagri_config','Configuration, routage général, connexion, déconnexion, service des pages et ressources frontend.'),
('api','Contrats JSON, droits, identité des robots, routes REST et adaptation HTTP des services.'),
('parcelles','Culture, Parcelle, Zone et Seuil. Le domaine géographique et agronomique.'),
('missions','Robot, Mission, EtapeMission ; préparation, envoi logique, accusé, interruption et fin.'),
('mesures','Etalonnage, Mesure ; réception, déduplication, validation et conversion en humidité.'),
('irrigation','RecommandationIrrigation, Irrigation ; décision, autorisation et suivi du résultat.'),
('incidents','Incident et service commun d’enregistrement des anomalies.'),
('templates','Page de connexion rendue par Django ; le reste du frontend est servi depuis le dossier voisin.'),
('frontend','Nouvelle interface HTML, CSS et JavaScript, entièrement reliée aux données du serveur.'),
('venv / packages','Environnements Python et distributions locales de dépendances : ce ne sont pas les sources métier.'),
('documentation','Documents de conception existants ; cette analyse porte sur l’implémentation, pas sur leur conformité détaillée.')
])+'''<h3>Comment lire un module Django</h3><p><code>models.py</code> définit le stockage ; <code>services.py</code> exprime les règles ; <code>admin.py</code> configure l’administration ; <code>apps.py</code> déclare l’application ; <code>migrations/</code> versionne le schéma ; <code>tests.py</code> vérifie certains scénarios. Les <code>views.py</code> des cinq domaines sont des squelettes : les véritables vues API sont centralisées dans <code>api/views.py</code>. Les fichiers <code>__init__.py</code> marquent les paquets Python.</p>
<p><code>manage.py</code> sélectionne les réglages et transmet les commandes à Django. <code>wsgi.py</code> et <code>asgi.py</code> exposent chacun une application serveur. La présence d’ASGI ne signifie pas qu’un canal WebSocket ou un traitement asynchrone métier existe.</p>'''+ref('api/views.py'))

section('relations','Base de données : relations et garanties', '''
<p>Le serveur utilise <code>backend/db.sqlite3</code>. Les 12 modèles métier ont chacun une table. Django ajoute ses tables de comptes, groupes, permissions, sessions, journal d’administration et migrations. Les identifiants <code>id</code> sont des clés primaires numériques automatiques.</p>
<pre class="diagram">Culture ──1:N── Zone ──N:1── Parcelle
                  │
                  ├──1:N── Seuil (un seul actif)
                  ├──1:N── EtapeMission ──N:1── Mission ──N:1── Robot
                  │                                │              │
                  └──1:N── Mesure ──N:1─────────────┘              └──1:N── Etalonnage
                              │  └──N:1── Robot                            (un seul actif)
                              ├──1:N── RecommandationIrrigation ──1:N── Irrigation
                              └──1:N── Incident
Utilisateur ──1:N── Mission (créateur)
Utilisateur ──1:N── RecommandationIrrigation (autorisateur facultatif)
Incident → Mission, Mesure, Robot : trois liens facultatifs
Irrigation → Zone, Mesure, Recommandation ; Mission facultative</pre>
<p><strong>1:N</strong> signifie qu’un parent peut être associé à plusieurs enfants. Une zone appartient à exactement une parcelle et une culture. Une mission contient des étapes ordonnées. Une mesure conserve simultanément sa zone, sa mission et son robot : les services doivent vérifier la cohérence de ces liens, car une clé étrangère garantit surtout l’existence de la cible.</p>
<h3>Les protections inscrites dans le schéma</h3>
'''+table(['Garantie','Effet'],[
('Noms uniques','Culture.nom, Parcelle.nom et Robot.nom ne peuvent pas être dupliqués.'),
('Zone unique dans sa parcelle','Le couple parcelle + nom est unique ; deux parcelles peuvent avoir une zone de même nom.'),
('Ordre unique','Deux étapes d’une mission ne peuvent pas partager le même ordre. Rien n’impose des ordres consécutifs ni quatre zones différentes.'),
('Seuil actif unique','Un index unique conditionnel autorise plusieurs anciens seuils, mais un seul actif par zone. valeur_min ≤ valeur_max.'),
('Étalonnage actif unique','Un seul étalonnage actif par robot ; valeur_min &lt; valeur_max évite une division par zéro.'),
('Messages uniques','Mesure.message_id est obligatoire et unique globalement. Incident.message_id est facultatif et unique lorsqu’il est renseigné.'),
('Recommandation unique','Le couple mesure_source + zone ne peut produire qu’une recommandation.'),
('Opération en attente unique','Une seule irrigation autorisee, commande_envoyee ou non_confirmee par couple mesure_source + zone. Les états terminaux sortent de cette contrainte.'),
('Identifiants techniques','Robot.identifiant et Irrigation.operation_id sont des UUID uniques ; ils ne remplacent pas les id numériques utilisés par les routes.')
])+'''<h3>Suppression et historique</h3><p>Les relations métier utilisent presque toutes <code>PROTECT</code> : Django empêche la suppression d’une cible encore référencée. La relation étape → mission utilise <code>CASCADE</code> : supprimer une mission supprimable entraîne ses étapes. Une mission déjà référencée par une mesure reste protégée. Ces règles de suppression sont prises en charge par Django et ne doivent pas être assimilées à toutes les actions SQL natives possibles.</p>
<p><code>null=True</code> permet une valeur SQL NULL ; <code>blank=True</code> autorise un champ vide dans la validation. <code>DecimalField</code> représente les valeurs avec précision décimale ; <code>max_digits</code> inclut les décimales. Les validateurs Python ne sont pas tous des contraintes SQL et <code>objects.create()</code> n’appelle pas automatiquement <code>full_clean()</code>.</p>
<h3>Transactions et accès concurrents</h3><p>Les services utilisent <code>transaction.atomic</code> pour valider ou annuler ensemble plusieurs écritures. Certains relisent l’objet avec <code>select_for_update()</code>. Sur SQLite, cela ne fournit pas le verrouillage de ligne attendu sur un moteur qui le supporte ; les tests séquentiels ne prouvent donc pas la résistance à des appels simultanés. Les index uniques restent importants.</p>
<h3>Évolution du schéma</h3><p>Les migrations initiales créent les tables. La deuxième migration d’incidents ajoute <code>message_id</code> ; celle d’irrigation ajoute l’unicité de recommandation. Ordre des dépendances : parcelles → missions → mesures → irrigation/incidents, avec dépendance au modèle utilisateur. Toutes les migrations existantes sont marquées appliquées dans la base observée. Un écart supplémentaire de validation sur <code>Parcelle.superficie</code> est détaillé dans les contrôles.</p>''')

section('auth','Connexion, rôles et sécurité des accès', '''
<h3>Humain : session Django</h3><ol><li>Le navigateur ouvre <code>/connexion/</code> : LoginView rend le formulaire avec CSRF.</li><li>Le formulaire POST valide les identifiants et ouvre une session. Le cookie de session accompagne les requêtes suivantes.</li><li>Une page protégée est servie par <code>page_frontend</code>. Un visiteur anonyme est redirigé vers la connexion.</li><li><code>GET /api/auth/me/</code> retourne le profil et les groupes. Les écritures fetch incluent <code>X-CSRFToken</code>, lu depuis le cookie <code>csrftoken</code>.</li><li>La déconnexion passe par POST avec CSRF sur <code>/deconnexion/</code>.</li></ol>
<p>Les réglages actuels n’activent que <code>SessionAuthentication</code> pour l’API humaine. <strong>Ni Basic Auth ni JWT</strong> ne sont configurés. Le frontend et l’API partagent la même origine ; aucun middleware CORS n’est configuré.</p>
'''+table(['Action','Humain connecté sans rôle','Operateur','Administrateur / superuser'],[
('Lire cultures, parcelles, zones, seuils, missions, étapes, étalonnages et incidents','Oui','Oui','Oui'),
('Créer/modifier/supprimer les ressources CRUD ordinaires','Non','Oui','Oui'),
('Lister ou gérer les robots','Non','Non','Oui'),
('Lister les utilisateurs','Non','Non','Oui'),
('Lire recommandations et irrigations, autoriser et envoyer','Non','Oui','Oui'),
('Profil, tableau de bord et rapport','Oui','Oui','Oui')
])+'''<p>Les permissions vérifient les noms exacts des groupes. Être dans « Administrateur » ne donne pas automatiquement accès à <code>/admin/</code> : l’administration Django utilise notamment <code>is_staff</code> et ses permissions propres. <code>creer_groupes</code> crée les groupes, sans leur attribuer des permissions de modèles. <code>creer_compte</code> crée ou met à jour un mot de passe et ajoute le groupe ; il ne retire pas les anciens groupes et ne valide pas explicitement la force du mot de passe.</p>
<h3>Robot : une identité séparée</h3><p><code>X-Robot-Id</code> contient l’UUID public du robot et <code>X-Robot-Token</code> son secret. L’authentificateur charge le robot, compare le secret avec <code>check_password</code> et construit un <code>RobotPrincipal</code>. Ce principal est authentifié mais n’est pas un utilisateur Django. Les routes humaines le refusent ; les routes robot exigent précisément ce type de principal.</p>
<p>Le jeton est enregistré avec <code>make_password</code> dans <code>jeton_hash</code>, jamais renvoyé par RobotSerializer. Le formulaire admin exige un jeton à la création et permet son remplacement. À l’inverse, le CRUD API des robots ne propose aucun champ jeton : créer un robot par cette API ne suffit pas à le rendre authentifiable.</p>
<p>Les routes robot limitent les lectures de missions et de commandes au robot connecté. Une mesure entrante doit citer son propre id numérique et une de ses missions. Cette protection ne règle pas tous les cas de déduplication globale, détaillés plus loin.</p>'''+ref('api/authentication.py')+ref('api/permissions.py')+ref('roboagri_config/views.py'))

section('missions','Parcours 1 — préparer et lancer une mission', '''
<ol><li><strong>Préparer les références :</strong> créer culture, parcelle, zones et robot ; configurer son jeton par l’administration. Son état doit être <code>connecte</code> pour l’envoi.</li><li><strong>Créer la mission :</strong> POST sur <code>/api/missions/</code> avec robot, date_mission, éventuellement description et une liste ordonnée zones. Si zones est fournie, la mission et ses étapes sont créées dans une transaction unique. <code>creer_mission</code> attribue le créateur connecté ; statut initial <code>planifiee</code> et transmission <code>en_attente</code>.</li><li><strong>Ajouter les étapes :</strong> POST sur <code>/api/etapes/</code> avec mission, zone, ordre et description facultative. <code>ajouter_etape</code> refuse une mission non planifiée.</li><li><strong>Envoyer :</strong> POST sur <code>/api/missions/{id}/envoyer/</code>. Le service exige au moins quatre étapes, un robot déclaré connecté et aucune autre mission en cours pour lui.</li><li><strong>Consulter côté robot :</strong> GET <code>/api/robot/missions/</code> puis éventuellement la route des étapes. La liste comprend toutes ses missions, sans filtrage d’état ; le firmware devra interpréter <code>etat_transmission</code>.</li><li><strong>Accuser réception :</strong> POST sur <code>/api/robot/missions/{id}/accuse/</code>. Une transmission <code>envoyee</code> devient <code>accusee_reception</code>, le statut passe à <code>en_cours</code> et <code>date_debut</code> est enregistré.</li></ol>
<div class="callout"><strong>« Envoyer » est une transition en base.</strong> Le service n’ouvre pas une connexion vers l’adresse IP du robot. Il prépare un état que le robot vient consulter en HTTP. Aucun dispositif de polling du firmware n’est fourni ici.</div>
<h3>Deux états, deux significations</h3><p><code>statut</code> décrit l’exécution métier ; <code>etat_transmission</code> décrit la communication. Une perte de communication positionne <code>non_confirmee</code> mais ne termine pas la mission.</p>
'''+table(['Fonction','Condition / résultat','Exposition'],[
('creer_mission','Crée la mission et ses valeurs initiales','POST missions/'),
('ajouter_etape','Mission planifiée et zone existante ; ajoute une étape','POST etapes/'),
('preparer_envoi_mission','Vérifie quatre étapes, disponibilité et absence de mission en cours ; transmission envoyee','POST missions/{id}/envoyer/'),
('enregistrer_accuse_reception','Transmission envoyee ; démarre la mission','POST robot/missions/{id}/accuse/'),
('interrompre_pour_obstacle','Crée un incident ; interrompt une mission en cours seulement si incident nouveau','Service Python uniquement'),
('terminer_mission','Exige en_cours ; positionne terminee et date_fin','Service Python uniquement'),
('signaler_perte_communication','Transmission non_confirmee et incident ; statut métier conservé','Service Python uniquement')
])+'''<p>Il n’y a pas de route dédiée pour achever une étape, terminer une mission, reprendre une mission interrompue ou signaler un obstacle. Les valeurs <code>annulee</code>, <code>ignoree</code> ou <code>echec</code> dans les choix des modèles ne prouvent pas l’existence d’un parcours complet pour les atteindre. La date planifiée ne déclenche pas automatiquement une mission.</p>'''+ref('missions/services.py'))

section('mesures','Parcours 2 — recevoir et comprendre une mesure', '''
<p>Le robot envoie les six champs ci-dessous. Les nombres et UUID sont des exemples fictifs ; les références doivent exister dans la base du serveur.</p>
<pre><code>POST /api/robot/mesures/
X-Robot-Id: UUID_PUBLIC_DU_ROBOT
X-Robot-Token: SECRET_DU_ROBOT
Content-Type: application/json

{
  "robot": 1,
  "mission": 1,
  "zone": 1,
  "valeur_brute": "100.00",
  "date_heure": "2026-11-18T09:00:00Z",
  "message_id": "00000000-0000-4000-8000-000000000001"
}</code></pre>
<ol><li><code>RobotMesureInputSerializer</code> valide les clés étrangères, le nombre décimal, la date et l’UUID. La vue compare le robot et le propriétaire de la mission à l’identité authentifiée.</li><li><code>recevoir_mesure</code> normalise l’UUID. Si une mesure existe avec ce message_id, il renvoie l’ancienne sans la recalculer, même si le contenu a changé.</li><li>Le service exige une date consciente du fuseau. Il sait refuser un âge maximal, mais la route HTTP ne fournit pas ce paramètre : aucune expiration n’est donc appliquée par ce chemin.</li><li>Il crée une mesure reçue puis vérifie l’accord robot/mission, la présence de la zone dans les étapes et l’existence d’un étalonnage actif.</li><li>Une erreur métier de validation conserve la mesure avec <code>invalide</code>, son motif, une humidité non calculée et un incident <code>mesure_invalide</code>. Elle ne produit pas de recommandation.</li><li>Sinon, il calcule l’humidité, marque la mesure valide et appelle immédiatement l’analyse d’irrigation dans la transaction.</li></ol>
<h3>La formule réellement implémentée</h3>
<pre>humidité = (valeur_brute − minimum) × 100 / (maximum − minimum)
Exemple : (100 − 0) × 100 / (1000 − 0) = 10,00 %</pre>
<p>La valeur brute doit appartenir à la plage fermée [minimum, maximum]. Le résultat est arrondi avec Decimal à deux décimales. La formule est croissante : elle ne modélise pas automatiquement un capteur dont la réponse diminue lorsque l’humidité augmente. Aucun traitement de température, correction de sol ou moyenne temporelle n’est présent.</p>
<div class="simulator"><h3>Essayer le calcul</h3><p>Simulation pédagogique locale, sans envoyer de commande.</p><div class="inputs"><label>Minimum brut<input id="sim-min" type="number" value="0" step="any"></label><label>Maximum brut<input id="sim-max" type="number" value="1000" step="any"></label><label>Valeur brute<input id="sim-value" type="number" value="100" step="any"></label><label>Seuil minimal (%)<input id="sim-threshold" type="number" value="30" step="any"></label></div><output id="sim-result" aria-live="polite"></output><p class="muted">Illustration numérique JavaScript : l’arrondi serveur utilise Decimal et peut différer aux frontières d’arrondi.</p></div>
<h3>Réponse et répétition réseau</h3><p>La réponse contient <code>mesure</code> et <code>recommandation_id</code>. Le premier enregistrement retourne HTTP 201, même si la mesure a été conservée invalide. Un doublon retourne 200 et <code>recommandation_id: null</code>, y compris si la première mesure avait généré une recommandation. Il faut lire les champs métier, pas seulement le code HTTP.</p>
<p>Le service n’exige pas une mission <code>en_cours</code> et n’interdit pas explicitement une date future. Le test de déduplication a lieu avant les validations internes : son périmètre global mérite un durcissement.</p>'''+ref('mesures/services.py')+ref('api/serializers.py'))

section('irrigation','Parcours 3 — de la recommandation au résultat', '''
<div class="flow"><span>Mesure valide</span><b>→</b><span>Humidité &lt; minimum</span><b>→</b><span>Recommandation</span><b>→</b><span>Autorisation humaine</span><b>→</b><span>Commande consultable</span><b>→</b><span>Résultat robot</span></div>
<h3>1. Analyse automatique</h3><p><code>analyser_mesure_pour_irrigation</code> refuse une mesure invalide. Sans seuil actif, il crée un incident <code>seuil_absent</code>. Si l’humidité est supérieure ou égale au minimum, il ne recommande rien. Sinon, <code>get_or_create</code> crée ou retrouve une recommandation par mesure et zone, avec la durée maximale du seuil et une justification textuelle. <strong>Le maximum du seuil n’est pas utilisé dans la décision.</strong></p>
<h3>2. Autorisation humaine</h3><p>POST <code>/api/recommandations/{id}/autoriser/</code> avec <code>{"duree_max": 10}</code>. Le service vérifie le rôle, la validité de la mesure et une durée strictement positive ne dépassant pas celle recommandée. Il refuse une recommandation déjà autorisée. Il enregistre l’auteur et l’heure, puis crée une irrigation <code>autorisee</code> avec un UUID d’opération.</p>
<p>Le champ de justification d’opérations supplémentaires existe, mais une recommandation déjà autorisée est refusée avant la vérification de cette justification. Il ne faut donc pas présenter ce champ comme un mécanisme opérationnel de réautorisation.</p>
<h3>3. Mise à disposition de la commande</h3><p>POST <code>/api/irrigations/{id}/envoyer/</code> exige l’état <code>autorisee</code> et le transforme en <code>commande_envoyee</code>. GET <code>/api/robot/irrigations/</code> retourne uniquement ces commandes, filtrées par le robot de la mesure source.</p>
<h3>4. Confirmation</h3><p>POST <code>/api/robot/irrigations/{id}/resultat/</code> reçoit par exemple <code>{"succes": true, "duree_reelle": 8, "volume": "1.20"}</code>. L’identifiant d’URL est l’id numérique, pas operation_id. Le serveur exige une commande envoyée ; pour un succès, la durée réelle doit être présente et ne pas dépasser la durée autorisée. Un échec crée un incident <code>irrigation_echec</code>. Le volume est stocké, sans calcul automatique ; son unité n’est pas définie explicitement par le modèle.</p>
<h3>5. Absence de confirmation</h3><p><code>signaler_irrigation_non_confirmee</code> transforme une commande envoyée en <code>non_confirmee</code> et crée un incident. Le champ de délai vaut 30 secondes par défaut, mais aucun ordonnanceur ne l’exploite automatiquement et aucune route ne déclenche ce service. Un résultat tardif sera refusé par le service normal puisqu’il exige <code>commande_envoyee</code>.</p>
<p>Une confirmation répétée après succès est également refusée : l’idempotence des mesures n’est pas implémentée pour les résultats d’irrigation. Aucun code Python ne coupe physiquement une pompe ; cette responsabilité doit être réalisée dans le firmware.</p>'''+ref('irrigation/services.py'))

crud=['cultures','parcelles','zones','seuils','robots','missions','etapes','etalonnages']
apirows=[('/api/'+x+'/', 'GET, POST', 'Administrateur' if x=='robots' else 'Lecture humain ; écriture opérateur/admin', 'Liste et création') for x in crud]
apirows += [('/api/'+x+'/{id}/','GET, PUT, PATCH, DELETE','Administrateur' if x=='robots' else 'Lecture humain ; écriture opérateur/admin','Détail, remplacement, modification partielle, suppression') for x in crud]
apirows += [('/api/'+x+'/', 'GET', role, 'Liste ; détail GET /{id}/ également disponible') for x,role in [('recommandations','Opérateur/admin'),('irrigations','Opérateur/admin'),('incidents','Humain connecté')]]
apirows += [(r,m,a,d) for r,m,a,d in [
('/api/auth/me/','GET','Humain','Profil de la session'),('/api/utilisateurs/','GET','Administrateur','Liste des profils'),('/api/tableau-de-bord/','GET','Humain','Comptes par statut et incidents ouverts'),('/api/rapports/','GET','Humain','Intention : mêmes agrégats ; appel imbriqué problématique à vérifier'),('/api/missions/{id}/envoyer/','POST','Opérateur/admin','Préparation logique de l’envoi'),('/api/recommandations/{id}/autoriser/','POST','Opérateur/admin','Crée une irrigation ; HTTP 201'),('/api/irrigations/{id}/envoyer/','POST','Opérateur/admin','Rend la commande consultable'),('/api/robot/mesures/','POST','Robot','201 nouvelle mesure ; 200 doublon'),('/api/robot/missions/','GET','Robot','Toutes ses missions et étapes imbriquées'),('/api/robot/missions/{id}/etapes/','GET','Robot','Étapes de sa mission, triées par ordre'),('/api/robot/missions/{id}/accuse/','POST','Robot','Démarrage après envoi'),('/api/robot/irrigations/','GET','Robot','Ses commandes envoyées'),('/api/robot/irrigations/{id}/resultat/','POST','Robot','Succès ou échec signalé')]]
section('api','Référence des routes et contrats', '''<p>Les routes finissent par un slash. Les ressources CRUD acceptent les méthodes de liste et détail indiquées ; HEAD et OPTIONS sont également disponibles selon la vue. Les listes ne sont pas paginées par une configuration DRF explicite. Aucun filtre métier de liste n’est déclaré.</p>'''+table(['Route','Méthodes','Identité / rôle','Comportement'],apirows)+'''
<h3>Champs modifiables et champs calculés</h3><p>Les serializers de culture, parcelle et zone exposent tous les champs, avec id automatiquement en lecture seule. Seuil et Etalonnage protègent leurs dates de création. Robot protège identifiant et derniere_connexion, omet jeton_hash et laisse modifier etat_connexion. Mission protège createur, statut, transmission et dates réelles ; les étapes imbriquées sont en lecture seule. EtapeMission protège statut et dates réelles. Les recommandations et irrigations sont exposées par des ViewSets en lecture seule, complétés par les actions métier POST.</p>
<p><code>MesureSerializer</code> sait rendre une mesure, mais aucun routeur <code>/api/mesures/</code> humain n’est enregistré. <code>/api/historique/</code>, <code>/api/robot/etat/</code> et <code>/api/configurations-irrigation/</code> n’existent pas dans les routes, Ces données sont maintenant consultables via <code>GET /api/supervision/</code> pour les opérateurs et administrateurs.</p>
<h3>Interpréter les erreurs</h3><p>400 : données rejetées ou erreur métier convertie en ValidationError. 403 : absence de session, rôle insuffisant ou authentification robot refusée dans les cas couverts par les tests. 404 : ressource absente ou inaccessible au robot. 405 : méthode non autorisée. 500 : défaut non géré possible. Ne pas supposer que toutes les erreurs d’authentification produisent 401.</p>
<p>Le dashboard renvoie <code>missions_par_statut</code> (liste statut/total), <code>incidents_ouverts</code> et <code>irrigations_non_confirmees</code>. Il ne calcule ni tendance d’humidité ni consommation d’eau. Le rapport tente de réutiliser la vue dashboard décorée ; ce point figure dans les limites.</p>'''+ref('api/urls.py')+ref('api/serializers.py'))

section('frontend','Ce que l’interface affiche réellement', """
<p><strong>Intégration du 20 novembre 2026.</strong> L’accueil <code>/</code> est public. Le tableau de bord <code>/dashboard.html</code>, les écrans de supervision et <code>/documentation/</code> demandent une session. Les ressources locales CSS, JS, images et bibliothèques permettent de consulter l’application sans CDN.</p>
<p><code>GET /api/supervision/</code>, réservé aux opérateurs et administrateurs, fournit un instantané des cultures, parcelles, zones, robots, missions avec étapes, mesures, incidents et irrigations. Aucun jeton ou hachage robot n’est exposé. Les écrans relisent cet instantané toutes les dix secondes. Les valeurs précédentes sont signalées comme potentiellement périmées si l’actualisation échoue.</p>
<p>Les formulaires écrivent dans les routes <code>/api/cultures/</code>, <code>/api/parcelles/</code>, <code>/api/zones/</code> et <code>/api/missions/</code>, avec session et CSRF. Une mission et sa liste ordonnée de zones sont enregistrées ensemble. Aucun envoi au robot n’est déclenché par le formulaire de préparation.</p>
<p>Les graphiques montrent les valeurs brutes des mesures valides. L’historique réunit les mesures, incidents, dates de mission, étapes et opérations réellement enregistrées. Les opérations autorisées, envoyées, exécutées, échouées et non confirmées restent distinctes. Les statistiques d’arrosage comptent uniquement les exécutions confirmées.</p>
<p>Batterie, position, vitesse, température et humidité après arrosage restent non communiquées tant que le serveur ne dispose pas de ces données. L’état de connexion du robot est l’état déclaré en base : aucun heartbeat matériel n’est ajouté par cette intégration. Les seuils et étalonnages restent gérés par l’administration ou l’API.</p>
<p>Le fichier de données de démonstration n’est plus chargé. Les guides de la maquette d’origine sont archivés sous <code>documentation/frontend/</code> et ne décrivent pas le comportement actuel. L’ancien front-end est conservé dans <code>documentation/archives/frontend-avant-integration.zip</code>.</p>
""")

section('limites','Limites observées et priorités pour l’équipe', '''
<p>Les points ci-dessous viennent de la lecture du code. Sauf mention de contrôle exécuté, il s’agit de constats statiques à reproduire par des tests ciblés avant correction. Le backend n’a pas été modifié dans le cadre de cette documentation.</p>
'''+table(['Priorité','Observation et effet','Piste de travail'],[
('Avant production','SECRET_KEY en dur, DEBUG=True, ALLOWED_HOSTS=["*"], cookies non Secure : réglages locaux.','Externaliser la configuration et renouveler la clé pour un déploiement ; HTTPS, hôtes explicites et cookies sécurisés.'),
('Intégrité / accès','recevoir_mesure cherche message_id globalement avant de vérifier le propriétaire de la mesure existante. Un UUID connu appartenant à un autre robot pourrait faire renvoyer sa mesure malgré une nouvelle charge autorisée.','Vérifier propriétaire et charge du doublon ; définir une portée de déduplication et tester les collisions inter-robots.'),
('Validation','Le résultat d’irrigation lit request.data directement : une chaîne "false" est vraie en Python ; une durée de mauvais type peut provoquer TypeError.','Créer des serializers d’entrée pour autorisation et résultat, avec booléen strict, entiers, minima et volume validés.'),
('Cycle de mission','Deux missions peuvent être envoyées avant le premier accusé : aucune n’est encore en_cours. L’accusé ne revérifie pas l’occupation.','Définir une réservation du robot et une contrainte/transaction cohérente couvrant envoi et accusé.'),
('Règles contournables','Le service protège la création d’étapes, mais PUT/PATCH/DELETE utilisent le CRUD standard sans contrôle identique sur les missions déjà lancées.','Protéger toutes les mutations et vérifier aussi l’administration, qui écrit directement dans les modèles.'),
('Rapport','rapport(request) appelle dashboard(request), lui-même décoré par @api_view. Le wrapper DRF attend normalement un HttpRequest Django et reçoit ici une Request DRF.','Extraire un helper d’agrégation commun ; ajouter un test GET /api/rapports/.'),
('Traçabilité','En cas de références inconnues, recevoir_mesure crée un incident puis lève une exception dans atomic : l’écriture d’incident est annulée avec la transaction.','Définir une stratégie de journalisation hors transaction annulée. La validation HTTP rejette déjà les références absentes plus tôt.'),
('Horodatage','Aucun âge maximal envoyé par la vue, pas de refus explicite des dates futures ou missions non actives.','Définir et tester les règles temporelles et les états acceptés.'),
('Réseau et robot','Pas de mise à jour automatique derniere_connexion/etat_connexion, ni firmware, ni timeout automatique, ni route de fin de mission.','Implémenter le protocole de vie du robot, les retours d’étapes et la gestion des échéances.'),
('Reprise réseau','Les doublons de mesures sont gérés séquentiellement ; les insertions concurrentes peuvent encore rencontrer un conflit unique. Accusés/résultats répétés sont refusés.','Tester la concurrence, normaliser les conflits et définir les réponses idempotentes attendues.'),
('Modèle agronomique','valeur_max du seuil n’intervient pas ; aucune unité explicite pour superficie/volume ; aucune borne haute 100 sur les seuils ; durée de seuil 0 possible au niveau modèle.','Documenter les unités, valider les bornes et confirmer la formule avec des essais de capteur.'),
('Exploitation','Aucune pagination globale, pas de mécanisme de limitation de débit configuré, pas de sauvegarde automatisée ni processus de production fourni.','Planifier performances, sauvegardes/restauration, supervision et déploiement selon l’usage réel.')
])+'''<p>Les mécanismes utiles existent déjà : identité robot distincte, secrets hachés, contrôle de propriété sur plusieurs routes, CSRF, transactions, conservation des mesures invalides et contraintes uniques. Ils constituent une base, sans prouver à eux seuls le fonctionnement complet sur matériel ou en production.</p>''')

section('exploitation','Démarrage et mode d’emploi technique', '''
<p>Les versions déclarées dans <code>requirements.txt</code> sont Django 6.1.3 et djangorestframework 3.18.3. Ce sont les versions du dépôt, pas une recommandation de mise à niveau. Les environnements virtuels et wheels locaux sont des dépendances, à distinguer du code métier.</p>
<pre><code># Depuis un terminal PowerShell, dans backend
.\\venv\\Scripts\\python.exe manage.py check
.\\venv\\Scripts\\python.exe manage.py showmigrations
.\\venv\\Scripts\\python.exe manage.py migrate
.\\venv\\Scripts\\python.exe manage.py creer_groupes
.\\venv\\Scripts\\python.exe manage.py createsuperuser
.\\venv\\Scripts\\python.exe manage.py runserver

# Contrôles sur une base de test distincte
.\\venv\\Scripts\\python.exe manage.py test --noinput
.\\venv\\Scripts\\python.exe manage.py makemigrations --check --dry-run</code></pre>
<p>Ces commandes sont des instructions de démarrage : aucune migration réelle ni création de compte n’a été effectuée pour produire cette documentation. Sur un nouvel ordinateur, recréer un environnement Python compatible et installer les dépendances du fichier requirements avant de lancer Django.</p>
<p>Ouvrir <code>http://127.0.0.1:8000/connexion/</code> pour la session, et <code>/admin/</code> pour configurer les références et le jeton du robot avec un compte autorisé. Créer un étalonnage actif et un seuil actif avant les mesures. Sans étalonnage, la mesure sera invalide ; sans seuil, elle pourra être valide mais ne produira pas de recommandation.</p>
<h3>Diagnostic par symptôme</h3>'''+table(['Symptôme','Vérification'],[
('403 sur API humaine','Session active ? Rôle adapté ? Cookie et en-tête CSRF pour une écriture ?'),
('Impossible d’envoyer une mission','Quatre étapes ? Statut planifié ? Robot connecté ? Autre mission en cours ?'),
('Mesure invalide','Étape dans cette zone ? Bon robot ? Étalonnage actif ? Valeur brute dans la plage ?'),
('Pas de recommandation','Mesure valide ? Seuil actif ? Humidité strictement inférieure au minimum ? Doublon renvoyant recommandation_id null ?'),
('Commande absente côté robot','Irrigation autorisée puis envoyée ? Même robot que celui de la mesure source ?'),
('Écran rempli alors que base vide','Vérifier si la page utilise encore les données de démonstration.')
])+'''<h3>Partager cette documentation</h3><p>Copier le contenu du dossier « Explication Backend » à la racine d’un dépôt dédié permet de disposer d’un site statique avec index.html, style.css et script.js. Il ne faut pas publier db.sqlite3, les environnements virtuels ou les paramètres secrets du projet. Aucune publication ni création de lien distant n’a été effectuée ici.</p><p>Le bouton « Imprimer / PDF » ouvre l’impression du navigateur avec tous les détails développés. Choisir « Enregistrer au format PDF » pour une copie figée. Les instructions de partage détaillées sont aussi dans README.md.</p>''')

# Métadonnées lues uniquement ; aucune ligne métier ou identité exportée.
db=sqlite3.connect((BACK/'db.sqlite3').as_uri()+'?mode=ro',uri=True)
names=[r[0] for r in db.execute("select name from sqlite_master where type='table' order by name")]
counts=[(n,str(db.execute('SELECT count(*) FROM "'+n+'"').fetchone()[0])) for n in names]
integrity=db.execute('pragma integrity_check').fetchone()[0]
fk=len(db.execute('pragma foreign_key_check').fetchall())
schema={n:db.execute('PRAGMA table_info("'+n+'")').fetchall() for n in names}
db.close()
section('controles','État local et contrôles exécutés', '<p>Instantané local du 18 novembre 2026. La base a été ouverte en lecture seule. Aucun compte, secret, détail de session ou libellé de donnée métier n’est reproduit.</p>'+table(['Table','Nombre de lignes observé'],counts)+f'<p>Contrôle SQLite integrity_check : <strong>{esc(integrity)}</strong>. Nombre de violations signalées par foreign_key_check : <strong>{fk}</strong>. Ces contrôles ne valident pas les règles agronomiques.</p>'+'''
<p>La base contient des cultures, parcelles et zones, mais aucun robot, étalonnage, mission, seuil, mesure ou irrigation au moment du contrôle. Un cycle matériel complet n’a donc pas été constaté dans les données locales.</p>
<div id="test-status">TEST_STATUS_PLACEHOLDER</div>
<p><code>manage.py check</code> ne signale aucun problème. <code>makemigrations --check --dry-run</code> détecte une migration manquante <code>parcelles/0002_alter_parcelle_superficie.py</code> : le modèle utilise MinValueValidator(Decimal("0.01")) tandis que la migration initiale utilise un flottant 0.01. Le contrôle de synchronisation n’est donc pas entièrement vert. La migration n’a pas été créée.</p>
<p>Les tests couvrent l’authentification/session/CSRF, l’isolation de certaines ressources robot, l’envoi et l’accusé des missions, la conversion et la déduplication de mesures, l’autorisation et les durées d’irrigation et la déduplication des incidents. Le fichier de tests parcelles est un squelette. Le test API intitulé « valid duration » vérifie en réalité le refus d’une durée trop longue. Les tests ne démontrent ni une intégration ESP32, ni un vrai réseau, ni les appels simultanés, ni la couverture exhaustive de toutes les routes.</p>''')

meaning={
'Culture':'Référentiel de cultures ; nom unique, description facultative et catégorie libre.',
'Parcelle':'Surface géographique nommée ; unité de superficie non fixée dans le modèle.',
'Zone':'Sous-ensemble d’une parcelle associé à une culture ; unité utilisée pour mesurer et décider.',
'Seuil':'Configuration historisable d’une zone ; seul le minimum et la durée servent à la recommandation actuelle.',
'Robot':'Identité matérielle indépendante des utilisateurs ; UUID public et secret haché.',
'Mission':'Plan de travail attribué à un robot et créé par un humain ; exécution et transmission séparées.',
'EtapeMission':'Visite ordonnée d’une zone dans une mission ; aucun mécanisme HTTP ne fait progresser son statut.',
'Etalonnage':'Plage brute du capteur, par robot ; conversion linéaire croissante en 0–100 %.',
'Mesure':'Observation horodatée, conservée même invalide ; clé globale message_id pour éviter une insertion répétée.',
'RecommandationIrrigation':'Proposition issue d’une mesure valide et sèche ; mémorise justification, durée et autorisateur.',
'Irrigation':'Opération autorisée, envoyée puis confirmée ; conserve durée réelle et volume déclarés.',
'Incident':'Anomalie horodatée ; rattachements métier facultatifs et déduplication facultative par UUID.'}
field_meanings={
'id':'Clé primaire numérique automatique.', 'nom':'Nom lisible de la ressource.', 'description':'Texte descriptif libre.', 'type_culture':'Catégorie de culture libre.', 'superficie':'Surface déclarée ; unité à convenir.', 'localisation':'Localisation textuelle, sans géométrie GPS.', 'parcelle':'Parcelle parente.', 'culture':'Culture associée.', 'zone':'Zone concernée.', 'valeur_min':'Minimum de configuration (pourcentage pour Seuil, valeur brute pour Etalonnage).', 'valeur_max':'Maximum de configuration (pourcentage pour Seuil, valeur brute pour Etalonnage).', 'duree_max_arrosage':'Plafond d’arrosage en secondes.', 'date_configuration':'Date de création automatique du seuil.', 'actif':'Indique la configuration active.', 'identifiant':'UUID public du robot pour X-Robot-Id.', 'adresse_ip':'Adresse IPv4 facultative ; pas utilisée pour un envoi sortant.', 'etat_connexion':'État déclaré ; pas de heartbeat automatique.', 'derniere_connexion':'Horodatage prévu, non mis à jour automatiquement par l’authentificateur.', 'jeton_hash':'Hachage du secret ; le secret brut ne doit pas être exposé.', 'createur':'Compte humain qui crée la mission.', 'robot':'Robot associé, référencé par son id numérique.', 'date_mission':'Date planifiée ; ne programme pas un déclenchement automatique.', 'date_debut':'Début réel facultatif.', 'date_fin':'Fin réelle facultative.', 'statut':'État métier ; voir les choix dans le code source.', 'etat_transmission':'État de communication distinct du statut d’exécution.', 'mission':'Mission liée.', 'ordre':'Position dans la mission, unique au sein de celle-ci.', 'date_etalonnage':'Date de création automatique.', 'etat':'Actif ou inactif.', 'valeur_brute':'Lecture numérique reçue du capteur.', 'humidite':'Pourcentage calculé, NULL si non calculé.', 'date_heure':'Horodatage de la mesure fourni par le robot.', 'est_valide':'NULL avant validation, puis vrai ou faux.', 'message_id':'UUID de déduplication.', 'motif_invalidation':'Explication des erreurs de validation.', 'mesure_source':'Mesure à l’origine de la décision.', 'creee_le':'Horodatage automatique de création.', 'justification':'Motif textuel de la recommandation.', 'duree_max':'Plafond en secondes.', 'autorisee_par':'Compte autorisateur ; NULL avant autorisation.', 'autorisee_le':'Heure de l’autorisation.', 'recommandation':'Proposition qui a conduit à l’opération.', 'operation_id':'UUID d’opération ; distinct de l’id de route.', 'date_irrigation':'Date de création de l’opération, pas nécessairement début physique.', 'duree_reelle':'Durée déclarée par le robot, en secondes.', 'volume':'Volume déclaré ; unité non explicite dans le modèle.', 'origine':'Origine textuelle, recommandation par défaut.', 'delai_confirmation_secondes':'Délai prévu, 30 secondes par défaut, sans traitement automatique.', 'justification_operations_multiples':'Motif prévu pour plusieurs opérations ; parcours limité par le refus de réautorisation.', 'date_incident':'Heure serveur de création par le service.', 'type_incident':'Catégorie libre de l’anomalie.', 'mesure':'Mesure liée à l’incident, facultative.'}
body='<p>Dictionnaire extrait des déclarations actuelles, complété par leur rôle. Chaque modèle possède aussi id. La déclaration Python précise null, blank, default, choices, max_digits, related_name et la politique de suppression sans simplification des options.</p>'
for app in ['parcelles','missions','mesures','irrigation','incidents']:
    p=BACK/app/'models.py'; source=p.read_text(encoding='utf-8-sig'); tree=ast.parse(source)
    for cls in tree.body:
        if not isinstance(cls,ast.ClassDef): continue
        rows=[('id','Clé primaire numérique automatique.','BigAutoField (migration)')]
        for node in cls.body:
            if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='models':
                name=node.targets[0].id
                rows.append((esc(name),esc(field_meanings.get(name,'Voir le parcours métier.')),'<code>'+esc(ast.get_source_segment(source,node.value))+'</code>'))
        body+='<details class="model"><summary>'+cls.name+' <small>'+app+'_'+cls.name.lower()+'</small></summary><p>'+meaning[cls.name]+'</p>'+table(['Champ','Sens','Déclaration exacte'],rows)+ref(app+'/models.py')+'</details>'
section('dictionnaire','Dictionnaire complet des 12 modèles',body)

roles={'models.py':'Définit les champs, relations, états, contraintes et représentations lisibles des objets. Les détails de chaque champ figurent dans le dictionnaire.', 'services.py':'Implémente les opérations métier détaillées dans les parcours ; les transactions encadrent les écritures.', 'admin.py':'Enregistre les modèles dans l’administration, configure colonnes, filtres et formulaires. Les actions admin ne passent pas systématiquement par les services.', 'apps.py':'Déclare le nom de l’application à Django.', '__init__.py':'Marque un paquet Python ; aucun comportement lorsque le fichier est vide.', 'tests.py':'Scénarios de validation utilisant une base de test isolée ; ce fichier ne s’exécute pas lors des requêtes normales.', 'views.py':'Squelette Django non utilisé par le routage API central.'}
special={'api/views.py':'Adaptateur HTTP central : ViewSets CRUD, actions envoyer/autoriser, agrégats et six vues robot. Fait le lien entre identité, serializers et services.', 'api/urls.py':'Enregistre onze ressources dans DefaultRouter et dix routes explicites ; les actions des ViewSets ajoutent leurs propres routes.', 'api/serializers.py':'Contrats de lecture et écriture : convertit modèles et JSON, définit champs protégés et valide les mesures entrantes.', 'api/permissions.py':'Cinq politiques : humain, opérateur/admin, consultation humaine avec écriture restreinte, administrateur et robot.', 'api/authentication.py':'Authentificateur à deux en-têtes et principal robot distinct des comptes Django.', 'roboagri_config/settings.py':'Configuration effective : applications, middleware, session/CSRF, SQLite, UTC et fichiers frontend. Clé secrète retirée de cet instantané.', 'roboagri_config/urls.py':'Racine du routage : admin, API, connexion, déconnexion, pages et ressources frontend.', 'roboagri_config/views.py':'LoginView/LogoutView, pages sous session, cookie CSRF et lecture de fichiers confinée à une racine autorisée.', 'manage.py':'Point d’entrée des commandes Django : choisit les réglages puis délègue à execute_from_command_line.', 'roboagri_config/asgi.py':'Expose application pour un serveur ASGI ; ne définit aucun WebSocket.', 'roboagri_config/wsgi.py':'Expose application pour un serveur WSGI.', 'missions/management/commands/creer_groupes.py':'Crée les deux groupes de rôles de façon idempotente, sans permissions admin automatiques.', 'missions/management/commands/creer_compte.py':'Crée ou retrouve un compte, remplace son mot de passe et lui ajoute un groupe ; les autres groupes sont conservés.', 'requirements.txt':'Versions exactes déclarées des deux dépendances principales.', 'templates/connexion.html':'Formulaire de session Django, jeton CSRF et affichage des erreurs ; utilise les ressources locales du frontend.'}
body='<p>Inventaire des fichiers Python du backend, de son formulaire et de ses dépendances directes. Ouvrir un fichier affiche ses symboles, puis son code numéroté. Les lignes sont celles de l’instantané analysé ; les références restent utilisables hors ligne. Les bibliothèques tierces, fichiers compilés et données SQLite ne sont pas reproduits.</p>'
paths=[]
for directory, dirs, files in os.walk(BACK):
    dirs[:] = [d for d in dirs if not d.lower().startswith(('venv', '.venv')) and d not in {'__pycache__', 'packages'}]
    paths.extend(Path(directory)/name for name in files if Path(name).suffix in {'.py', '.html'} or name=='requirements.txt')
paths.sort()
for p in paths:
    rel=p.relative_to(BACK).as_posix(); source=p.read_text(encoding='utf-8-sig'); id='src-'+rel.replace('/','-').replace('.','-')
    role=special.get(rel,roles.get(p.name,'Fichier de support.'))
    if '/migrations/' in rel and p.name!='__init__.py': role='Migration versionnée : ses dépendances fixent l’ordre d’application et ses opérations décrivent les créations ou modifications de schéma. Elle ne s’exécute que via la gestion des migrations.'
    symbols=[]
    if p.suffix=='.py':
        tree=ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
                symbols.append((node.lineno,node.name,'classe' if isinstance(node,ast.ClassDef) else 'fonction'))
    source=re.sub(r"(?m)^SECRET_KEY\s*=.*$", "SECRET_KEY = '[SECRET RETIRÉ DE LA DOCUMENTATION]'",source)
    body+='<details class="source-file" id="'+id+'"><summary>'+esc(rel)+'</summary><p>'+role+'</p>'
    if symbols: body+='<p class="symbols">'+ ' · '.join('<a href="#'+id+'-L'+str(n)+'">'+esc(name)+' <small>L'+str(n)+'</small></a>' for n,name,kind in sorted(symbols))+'</p>'
    if source.strip(): body+='<pre class="source-code"><code>'+''.join('<span id="'+id+'-L'+str(i)+'"><i>'+str(i)+'</i>'+esc(line)+'\n</span>' for i,line in enumerate(source.splitlines(),1))+'</code></pre>'
    else: body+='<p class="muted">Fichier vide : aucun code exécutable.</p>'
    body+='</details>'
section('sources','Explorateur des fichiers et du code',body)

section('glossaire','Glossaire et lecture critique',table(['Terme','Explication'],[
('API REST','Interface HTTP qui expose des ressources et des actions en JSON.'),('CRUD','Créer, lire, modifier et supprimer une ressource.'),('ORM','Couche Python qui manipule des modèles et produit des requêtes SQL.'),('Serializer','Convertisseur et validateur entre JSON et objets Python/modèles.'),('ViewSet','Ensemble de vues DRF pour une ressource, généralement liste, détail et mutations.'),('Clé étrangère','Lien vers la clé primaire d’un autre enregistrement.'),('Migration','Étape versionnée d’évolution du schéma de données.'),('Transaction atomique','Groupe d’écritures validé ensemble ou annulé en cas d’exception.'),('Idempotence','Un même message répété ne produit pas une deuxième opération métier.'),('CSRF','Protection des requêtes d’écriture faites avec une session de navigateur.'),('Hachage','Transformation à sens unique permettant de vérifier un secret sans le stocker en clair.'),('Polling','Le client interroge périodiquement le serveur pour récupérer les commandes.'),('Service métier','Fonction qui applique une règle du domaine indépendamment du format HTTP.'),('Constat statique','Conclusion tirée du code, à distinguer d’un scénario effectivement exécuté.')
])+'''<p>Pour modifier ce système, commencer par formuler la règle métier, choisir le niveau où elle doit être garantie (serializer, service, modèle ou base), puis vérifier tous les chemins d’écriture, y compris l’administration. Un champ dans un modèle ne signifie pas qu’un processus l’alimente ; une route ne signifie pas qu’un écran l’utilise ; un test passant ne signifie pas que le robot physique a exécuté l’action.</p>''')

nav=''.join('<a href="#'+id+'"><small>'+str(i).zfill(2)+'</small>'+title+'</a>' for i,(id,title,b) in enumerate(sections,1))
main=''.join('<section id="'+id+'" data-chapter><div class="eyebrow">CHAPITRE '+str(i).zfill(2)+'</div><h2>'+title+'</h2>'+b+'</section>' for i,(id,title,b) in enumerate(sections,1))
page='''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Documentation détaillée du backend Django RoboAgri-Kin : architecture, données, API, services et limites."><title>RoboAgri-Kin — Explication du backend</title><link rel="stylesheet" href="style.css"><script src="script.js" defer></script></head><body><a class="skip" href="#contenu">Aller au contenu</a><aside><a class="brand" href="#top">R<span> / </span>K<span class="brand-sub">ROBOAGRI-KIN</span></a><p class="aside-label">LE BACKEND EXPLIQUÉ</p><label class="search-label" for="search">Rechercher dans le guide</label><input type="search" id="search" placeholder="Ex. étalonnage, CSRF…"><p id="search-status" role="status"></p><nav aria-label="Chapitres">'''+nav+'''</nav><p class="aside-footer">Django · SQLite · API REST<br>Analyse du 18.11.2026</p></aside><main id="contenu"><header id="top"><p><a href="/dashboard.html">← Retour à l’application</a></p><p class="callout">Interface intégrée le 20 novembre 2026 : voir le chapitre « Ce que l’interface affiche réellement ». Les constats d’audit et contrôles datés du 18 novembre restent un historique.</p><div class="topline"><span>DOCUMENTATION TECHNIQUE / ÉQUIPE</span><button id="print" type="button">Imprimer / PDF</button></div><p class="eyebrow">ROBOAGRI-KIN — GUIDE DE RÉFÉRENCE</p><h1>Comprendre<br>le <em>backend.</em></h1><p class="hero-copy">Une lecture complète du système : ce qu’il stocke, comment il décide et comment ses composants communiquent.</p><div class="metrics"><span><strong>12</strong> modèles métier</span><span><strong>5</strong> domaines</span><span><strong>3</strong> parcours expliqués</span><span><strong>100 %</strong> lecture hors ligne</span></div></header><div id="chapters">'''+main+'''</div><p id="empty" hidden>Aucun chapitre ne correspond. Essayez un autre terme.</p><footer>RoboAgri-Kin · Documentation de l’implémentation locale · 18 novembre 2026<br>Les exemples sont pédagogiques ; aucun contrôle du robot depuis cette page.</footer></main></body></html>'''
status=(OUT/'verification.html').read_text(encoding='utf-8') if (OUT/'verification.html').exists() else '<p>Exécution de la suite de tests en cours lors de la génération ; consulter le compte rendu de livraison.</p>'
page=page.replace('TEST_STATUS_PLACEHOLDER',status)
(OUT/'index.html').write_text(page,encoding='utf-8')
print(f'Documentation générée : {len(sections)} chapitres, {len(paths)} fichiers sources, {len(page)} caractères.')
