# ============================================
# GESTION DES DOUBLONS ENTRE TRAIN ET TEST
# ============================================
import hashlib
from collections import defaultdict

def get_file_hash(file_path):
    """Calcule le hash MD5 d'un fichier"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Erreur lors du calcul du hash pour {file_path}: {e}")
        return None

# Liste des émotions (sous-dossiers)
EMOTIONS = ['angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised']

def get_file_hash_fast(file_path):
    """Calcule le hash MD5 d'un fichier (version optimisée avec chunks plus grands)"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):  # 64KB chunks (plus rapide)
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        return None

def find_duplicates(train_dir, test_dir, remove_from_test=True):
    """
    Détecte et supprime les doublons entre train et test (VERSION OPTIMISÉE)
    
    IMPORTANT: Seuls les fichiers avec le MÊME CONTENU (même hash) sont considérés comme doublons.
    Les fichiers avec le même nom mais contenu différent ne sont PAS supprimés.
    
    Stratégie d'optimisation:
    1. Filtre par taille de fichier (RAPIDE - réduit le nombre de candidats)
    2. Vérifie par hash MD5 (PRÉCIS - seule méthode de confirmation)
    
    Args:
        train_dir: Dossier d'entraînement
        test_dir: Dossier de test
        remove_from_test: Si True, supprime les doublons du test (recommandé)
    """
    print("🔍 Recherche des vrais doublons entre train et test...")
    print("   ⚠️  Seuls les fichiers avec le MÊME CONTENU seront supprimés")
    print("   (Méthode: taille → hash MD5 pour confirmation)")
    
    train_path = Path(train_dir)
    test_path = Path(test_dir)
    
    if not train_path.exists():
        print(f"❌ Dossier train introuvable: {train_dir}")
        return []
    if not test_path.exists():
        print(f"❌ Dossier test introuvable: {test_dir}")
        return []
    
    # Étape 1: Collecter tous les fichiers par nom (pour statistiques)
    print("\n⚡ Étape 1: Collecte des fichiers...")
    train_files_by_name = defaultdict(list)
    test_files_by_name = defaultdict(list)
    
    for emotion in EMOTIONS:
        train_emotion_dir = train_path / emotion
        test_emotion_dir = test_path / emotion
        
        if train_emotion_dir.exists():
            for img_file in list(train_emotion_dir.glob("*.jpg")) + list(train_emotion_dir.glob("*.png")):
                train_files_by_name[img_file.name].append(img_file)
        
        if test_emotion_dir.exists():
            for img_file in list(test_emotion_dir.glob("*.jpg")) + list(test_emotion_dir.glob("*.png")):
                test_files_by_name[img_file.name].append(img_file)
    
    # Statistiques sur les noms similaires (information uniquement)
    potential_by_name = 0
    for filename in test_files_by_name:
        if filename in train_files_by_name:
            potential_by_name += len(test_files_by_name[filename]) * len(train_files_by_name[filename])
    
    print(f"   📋 {potential_by_name} paires avec même nom (à vérifier par hash)")
    
    # Étape 2: Comparaison par taille pour optimiser (filtre rapide)
    print("\n⚡ Étape 2: Filtrage par taille de fichier...")
    
    # Grouper tous les fichiers par taille
    train_files_by_size = defaultdict(list)
    test_files_by_size = defaultdict(list)
    
    for files_list in train_files_by_name.values():
        for img_file in files_list:
            try:
                size = img_file.stat().st_size
                train_files_by_size[size].append(img_file)
            except:
                pass
    
    for files_list in test_files_by_name.values():
        for img_file in files_list:
            try:
                size = img_file.stat().st_size
                test_files_by_size[size].append(img_file)
            except:
                pass
    
    # Candidats pour vérification par hash (même taille)
    candidates_for_hash = []
    for size in test_files_by_size:
        if size in train_files_by_size:
            for test_file in test_files_by_size[size]:
                for train_file in train_files_by_size[size]:
                    candidates_for_hash.append((train_file, test_file))
    
    print(f"   📋 {len(candidates_for_hash)} candidats à vérifier par hash (même taille)...")
    
    # Étape 3: Vérification par hash (SEULE MÉTHODE DE CONFIRMATION)
    # On vérifie par hash TOUS les candidats, même ceux avec le même nom
    # car les noms peuvent se dupliquer sans que les fichiers soient identiques
    print("\n⚡ Étape 3: Vérification par hash (confirmation des vrais doublons)...")
    print("   ⚠️  Seuls les fichiers avec le MÊME CONTENU seront considérés comme doublons")
    
    duplicates_confirmed = []  # Seuls les vrais doublons (même hash)
    checked = 0
    
    for train_file, test_file in candidates_for_hash:
        checked += 1
        if checked % 1000 == 0:
            print(f"   Progression: {checked}/{len(candidates_for_hash)} vérifiés...")
        
        train_hash = get_file_hash_fast(train_file)
        test_hash = get_file_hash_fast(test_file)
        
        if train_hash and test_hash and train_hash == test_hash:
            duplicates_confirmed.append({
                'train_file': train_file,
                'test_file': test_file,
                'hash': train_hash
            })
    
    print(f"   ✅ {len(duplicates_confirmed)} vrais doublons confirmés (même contenu)")
    
    total_train = sum(len(files) for files in train_files_by_name.values())
    total_test = sum(len(files) for files in test_files_by_name.values())
    
    print(f"\n📊 Statistiques finales:")
    print(f"   - Fichiers dans train: {total_train}")
    print(f"   - Fichiers dans test: {total_test}")
    print(f"   - Paires avec même nom: {potential_by_name} (information)")
    print(f"   - Vrais doublons confirmés (même contenu): {len(duplicates_confirmed)}")
    
    if len(duplicates_confirmed) == 0:
        print("\n✅ Aucun doublon détecté (fichiers avec contenu identique)!")
        return []
    
    # Afficher quelques exemples
    print(f"\n📋 Exemples de vrais doublons (premiers 5):")
    for i, dup in enumerate(duplicates_confirmed[:5]):
        print(f"   {i+1}. Train: {dup['train_file'].name} | Test: {dup['test_file'].name}")
        print(f"       Hash: {dup['hash'][:16]}...")
    
    if len(duplicates_confirmed) > 5:
        print(f"   ... et {len(duplicates_confirmed) - 5} autres")
    
    # Supprimer UNIQUEMENT les vrais doublons (confirmés par hash)
    if remove_from_test:
        print(f"\n🗑️  Suppression des {len(duplicates_confirmed)} vrais doublons du dossier test...")
        print("   (Seuls les fichiers avec le MÊME CONTENU sont supprimés)")
        removed_count = 0
        removed_files = set()  # Pour éviter les suppressions multiples
        
        for dup in duplicates_confirmed:
            test_file = dup['test_file']
            # Vérifier que le fichier existe et n'a pas déjà été supprimé
            if test_file.exists() and str(test_file) not in removed_files:
                try:
                    test_file.unlink()  # Supprime le fichier
                    removed_files.add(str(test_file))
                    removed_count += 1
                except Exception as e:
                    print(f"   ⚠️ Erreur lors de la suppression de {test_file.name}: {e}")
        
        print(f"✅ {removed_count} fichiers supprimés du test")
        print(f"   - Fichiers restants dans test: {total_test - removed_count}")
    else:
        print("\n⚠️ Suppression désactivée. Les doublons sont conservés.")
        print("   Pour supprimer, exécutez: find_duplicates(train_dir, test_dir, remove_from_test=True)")
    
    return duplicates_confirmed

# Exécuter la détection et suppression des doublons
# Décommentez la ligne suivante pour activer la suppression automatique
# find_duplicates(train_dir, test_dir, remove_from_test=True)

Exécuter la détection RAPIDE des doublons (sans suppression)
print("=" * 60)
print("DÉTECTION RAPIDE DES DOUBLONS (Mode analyse uniquement)")
print("=" * 60)
duplicates = find_duplicates(train_dir, test_dir, remove_from_test=True)

Pour supprimer les doublons, décommentez la ligne suivante:
find_duplicates(train_dir, test_dir, remove_from_test=True)



# ============================================
# FONCTION SIMPLIFIÉE ET SYNTHÉTISÉE
# ============================================
import hashlib
from collections import defaultdict
import json
from datetime import datetime

def find_duplicates_simple(train_dir, test_dir, remove_duplicates=False, remove_from='test'):
    """
    Fonction SIMPLIFIÉE pour détecter et supprimer les doublons entre train et test
    
    IMPORTANT: 
    - Prend 100% des fichiers du dossier test (pas de pourcentage)
    - Vérifie les doublons entre test et train
    - Code synthétisé et simplifié
    
    Args:
        train_dir: Dossier d'entraînement
        test_dir: Dossier de test
        remove_duplicates: Si True, supprime les doublons du test
        remove_from: 'test' (supprime du test) ou 'train' (supprime du train)
    """
    print("=" * 80)
    print("🔍 DÉTECTION DES DOUBLONS (100% des fichiers test)")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    train_path = Path(train_dir).resolve()
    test_path = Path(test_dir).resolve()
    
    if not train_path.exists() or not test_path.exists():
        print(f"❌ Dossiers introuvables")
        return []
    
    # ============================================
    # COLLECTE ET CALCUL DES HASH (SYNTHÉTISÉ)
    # ============================================
    print("📂 Collecte des fichiers et calcul des hash...")
    
    train_hash_to_files = defaultdict(list)
    test_hash_to_files = defaultdict(list)
    
    # Train
    train_count = 0
    for emotion in EMOTIONS:
        emotion_dir = train_path / emotion
        if emotion_dir.exists():
            for img_file in list(emotion_dir.glob("*.jpg")) + list(emotion_dir.glob("*.png")):
                file_hash = get_file_hash_fast(img_file)
                if file_hash:
                    train_hash_to_files[file_hash].append(img_file.resolve())
                train_count += 1
                if train_count % 1000 == 0:
                    print(f"   Train: {train_count} fichiers...")
    
    # Test (100% - TOUS les fichiers)
    test_count = 0
    for emotion in EMOTIONS:
        emotion_dir = test_path / emotion
        if emotion_dir.exists():
            for img_file in list(emotion_dir.glob("*.jpg")) + list(emotion_dir.glob("*.png")):
                file_hash = get_file_hash_fast(img_file)
                if file_hash:
                    test_hash_to_files[file_hash].append(img_file.resolve())
                test_count += 1
                if test_count % 1000 == 0:
                    print(f"   Test: {test_count} fichiers...")
    
    print(f"   ✅ Train: {train_count} fichiers, {len(train_hash_to_files)} uniques")
    print(f"   ✅ Test: {test_count} fichiers (100%), {len(test_hash_to_files)} uniques")
    
    # ============================================
    # DÉTECTION DES DOUBLONS (SYNTHÉTISÉ)
    # ============================================
    print("\n🔍 Détection des doublons entre train et test...")
    
    duplicates = []
    for file_hash in test_hash_to_files:
        if file_hash in train_hash_to_files:
            # Fichier présent dans train ET test = doublon
            for test_file in test_hash_to_files[file_hash]:
                duplicates.append({
                    'hash': file_hash,
                    'train_file': train_hash_to_files[file_hash][0],
                    'test_file': test_file
                })
    
    print(f"   ✅ {len(duplicates)} doublons trouvés")
    
    if len(duplicates) == 0:
        print("\n✅ Aucun doublon détecté!")
        return []
    
    # Afficher quelques exemples
    print(f"\n📋 Exemples (premiers 5):")
    for i, dup in enumerate(duplicates[:5]):
        print(f"   {i+1}. {dup['test_file'].name}")
    
    # ============================================
    # SUPPRESSION (SIMPLIFIÉE)
    # ============================================
    if remove_duplicates:
        print(f"\n🗑️  Suppression de {len(duplicates)} doublons...")
        
        def delete_file(file_path):
            """Supprime un fichier"""
            try:
                file_path = Path(file_path).resolve()
                if file_path.exists():
                    file_path.unlink()
                    return True
                return False
            except Exception as e:
                print(f"   ⚠️ Erreur: {file_path.name} - {e}")
                return False
        
        removed = 0
        for dup in duplicates:
            file_to_delete = dup['test_file'] if remove_from == 'test' else dup['train_file']
            if delete_file(file_to_delete):
                removed += 1
        
        print(f"✅ {removed} fichiers supprimés avec succès")
    else:
        print("\n⚠️ Suppression désactivée. Mettez remove_duplicates=True pour supprimer")
    
    print("\n" + "=" * 80)
    return duplicates

# Exécuter la détection
# duplicates = find_duplicates_simple(train_dir, test_dir, remove_duplicates=False)


Exécuter la détection des doublons (version simplifiée)
=======================================================

Détection sans suppression
duplicates = find_duplicates_simple(train_dir, test_dir, remove_duplicates=False)

Pour supprimer les doublons, décommentez la ligne suivante:
duplicates = find_duplicates_simple(train_dir, test_dir, remove_duplicates=True, remove_from='test')

# ============================================
# FONCTION SIMPLIFIÉE DE DÉTECTION DE DOUBLONS
# ============================================
import hashlib
from collections import defaultdict
import json
from datetime import datetime

def find_all_duplicates_exhaustive(train_dir, test_dir, 
                                     check_train_internal=True,
                                     check_test_internal=True,
                                     check_cross=True,
                                     remove_duplicates=False,
                                     remove_from='test',
                                     export_report=False):
    """
    Fonction EXHAUSTIVE pour détecter TOUS les doublons possibles
    
    Détecte:
    1. Doublons à l'intérieur du dossier train
    2. Doublons à l'intérieur du dossier test
    3. Doublons entre train et test
    
    Args:
        train_dir: Dossier d'entraînement
        test_dir: Dossier de test
        check_train_internal: Vérifier les doublons dans train
        check_test_internal: Vérifier les doublons dans test
        check_cross: Vérifier les doublons entre train et test
        remove_duplicates: Si True, supprime les doublons
        remove_from: 'test', 'train', ou 'both' - d'où supprimer
        export_report: Si True, exporte un rapport JSON
    
    Returns:
        dict: Rapport complet avec tous les doublons trouvés
    """
    print("=" * 80)
    print("🔍 ANALYSE EXHAUSTIVE DES DOUBLONS")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    train_path = Path(train_dir)
    test_path = Path(test_dir)
    
    if not train_path.exists():
        print(f"❌ Dossier train introuvable: {train_dir}")
        return None
    if not test_path.exists():
        print(f"❌ Dossier test introuvable: {test_dir}")
        return None
    
    # ============================================
    # ÉTAPE 1: COLLECTE DE TOUS LES FICHIERS
    # ============================================
    print("📂 Étape 1: Collecte de tous les fichiers...")
    
    train_files = {}  # {hash: [list of files]}
    test_files = {}   # {hash: [list of files]}
    
    # Collecter les fichiers train
    train_file_list = []
    for emotion in EMOTIONS:
        emotion_dir = train_path / emotion
        if emotion_dir.exists():
            for img_file in list(emotion_dir.glob("*.jpg")) + list(emotion_dir.glob("*.png")):
                train_file_list.append(img_file)
    
    # Collecter les fichiers test
    test_file_list = []
    for emotion in EMOTIONS:
        emotion_dir = test_path / emotion
        if emotion_dir.exists():
            for img_file in list(emotion_dir.glob("*.jpg")) + list(emotion_dir.glob("*.png")):
                test_file_list.append(img_file)
    
    print(f"   ✅ {len(train_file_list)} fichiers dans train")
    print(f"   ✅ {len(test_file_list)} fichiers dans test")
    
    # ============================================
    # ÉTAPE 2: CALCUL DES HASH (avec progression)
    # ============================================
    print("\n⚡ Étape 2: Calcul des hash MD5...")
    
    def calculate_hashes_batch(file_list, label):
        """Calcule les hashs pour une liste de fichiers"""
        file_hash_map = {}  # {file_path: hash}
        hash_to_files = defaultdict(list)  # {hash: [files]}
        
        total = len(file_list)
        for i, img_file in enumerate(file_list):
            if (i + 1) % 500 == 0 or i == 0:
                print(f"   {label}: {i+1}/{total} fichiers traités...")
            
            file_hash = get_file_hash_fast(img_file)
            if file_hash:
                file_hash_map[img_file] = file_hash
                hash_to_files[file_hash].append(img_file)
        
        print(f"   ✅ {label}: {total} fichiers traités")
        return file_hash_map, hash_to_files
    
    train_hash_map, train_hash_to_files = calculate_hashes_batch(train_file_list, "Train")
    test_hash_map, test_hash_to_files = calculate_hashes_batch(test_file_list, "Test")
    
    # ============================================
    # ÉTAPE 3: DÉTECTION DES DOUBLONS
    # ============================================
    print("\n🔍 Étape 3: Détection des doublons...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'train_dir': str(train_dir),
        'test_dir': str(test_dir),
        'train_internal_duplicates': [],
        'test_internal_duplicates': [],
        'cross_duplicates': [],
        'statistics': {}
    }
    
    # 3.1 Doublons dans train (interne)
    if check_train_internal:
        print("\n   📊 Analyse des doublons dans TRAIN...")
        train_internal = []
        for file_hash, files in train_hash_to_files.items():
            if len(files) > 1:
                train_internal.append({
                    'hash': file_hash,
                    'count': len(files),
                    'files': [str(f) for f in files],
                    'emotions': [f.parent.name for f in files]
                })
        report['train_internal_duplicates'] = train_internal
        print(f"      ✅ {len(train_internal)} groupes de doublons trouvés dans train")
        if train_internal:
            total_dups = sum(d['count'] - 1 for d in train_internal)
            print(f"      📋 {total_dups} fichiers en doublon (peuvent être supprimés)")
    
    # 3.2 Doublons dans test (interne)
    if check_test_internal:
        print("\n   📊 Analyse des doublons dans TEST...")
        test_internal = []
        for file_hash, files in test_hash_to_files.items():
            if len(files) > 1:
                test_internal.append({
                    'hash': file_hash,
                    'count': len(files),
                    'files': [str(f) for f in files],
                    'emotions': [f.parent.name for f in files]
                })
        report['test_internal_duplicates'] = test_internal
        print(f"      ✅ {len(test_internal)} groupes de doublons trouvés dans test")
        if test_internal:
            total_dups = sum(d['count'] - 1 for d in test_internal)
            print(f"      📋 {total_dups} fichiers en doublon (peuvent être supprimés)")
    
    # 3.3 Doublons entre train et test
    if check_cross:
        print("\n   📊 Analyse des doublons entre TRAIN et TEST...")
        cross_duplicates = []
        for file_hash in train_hash_to_files:
            if file_hash in test_hash_to_files:
                train_files_list = train_hash_to_files[file_hash]
                test_files_list = test_hash_to_files[file_hash]
                
                for test_file in test_files_list:
                    cross_duplicates.append({
                        'hash': file_hash,
                        'train_file': str(train_files_list[0]),  # Prendre le premier
                        'test_file': str(test_file),
                        'train_emotion': train_files_list[0].parent.name,
                        'test_emotion': test_file.parent.name
                    })
        
        report['cross_duplicates'] = cross_duplicates
        print(f"      ✅ {len(cross_duplicates)} doublons trouvés entre train et test")
    
    # ============================================
    # ÉTAPE 4: STATISTIQUES DÉTAILLÉES
    # ============================================
    print("\n📊 Étape 4: Génération des statistiques...")
    
    stats = {
        'total_train_files': len(train_file_list),
        'total_test_files': len(test_file_list),
        'unique_train_files': len(train_hash_to_files),
        'unique_test_files': len(test_hash_to_files),
        'train_internal': {
            'duplicate_groups': len(report['train_internal_duplicates']),
            'duplicate_files': sum(d['count'] - 1 for d in report['train_internal_duplicates']),
            'space_wasted_mb': 0  # Sera calculé
        },
        'test_internal': {
            'duplicate_groups': len(report['test_internal_duplicates']),
            'duplicate_files': sum(d['count'] - 1 for d in report['test_internal_duplicates']),
            'space_wasted_mb': 0
        },
        'cross_duplicates': len(report['cross_duplicates'])
    }
    
    # Calculer l'espace gaspillé
    def calculate_wasted_space(duplicates_list):
        total_size = 0
        for dup_group in duplicates_list:
            if dup_group['files']:
                try:
                    file_size = Path(dup_group['files'][0]).stat().st_size
                    # Compter les fichiers en doublon (count - 1)
                    total_size += file_size * (dup_group['count'] - 1)
                except:
                    pass
        return total_size / (1024 * 1024)  # En MB
    
    stats['train_internal']['space_wasted_mb'] = calculate_wasted_space(report['train_internal_duplicates'])
    stats['test_internal']['space_wasted_mb'] = calculate_wasted_space(report['test_internal_duplicates'])
    
    report['statistics'] = stats
    
    # ============================================
    # ÉTAPE 5: AFFICHAGE DU RAPPORT
    # ============================================
    print("\n" + "=" * 80)
    print("📊 RAPPORT COMPLET DES DOUBLONS")
    print("=" * 80)
    print(f"\n📁 Fichiers:")
    print(f"   - Train: {stats['total_train_files']} fichiers ({stats['unique_train_files']} uniques)")
    print(f"   - Test: {stats['total_test_files']} fichiers ({stats['unique_test_files']} uniques)")
    
    if check_train_internal:
        print(f"\n🔍 Doublons dans TRAIN:")
        print(f"   - Groupes de doublons: {stats['train_internal']['duplicate_groups']}")
        print(f"   - Fichiers en doublon: {stats['train_internal']['duplicate_files']}")
        print(f"   - Espace gaspillé: {stats['train_internal']['space_wasted_mb']:.2f} MB")
    
    if check_test_internal:
        print(f"\n🔍 Doublons dans TEST:")
        print(f"   - Groupes de doublons: {stats['test_internal']['duplicate_groups']}")
        print(f"   - Fichiers en doublon: {stats['test_internal']['duplicate_files']}")
        print(f"   - Espace gaspillé: {stats['test_internal']['space_wasted_mb']:.2f} MB")
    
    if check_cross:
        print(f"\n🔍 Doublons entre TRAIN et TEST:")
        print(f"   - Nombre de doublons: {stats['cross_duplicates']}")
        if stats['cross_duplicates'] > 0:
            # Afficher quelques exemples
            print(f"\n   Exemples (premiers 5):")
            for i, dup in enumerate(report['cross_duplicates'][:5]):
                print(f"      {i+1}. Train: {Path(dup['train_file']).name} ({dup['train_emotion']})")
                print(f"         Test: {Path(dup['test_file']).name} ({dup['test_emotion']})")
    
    # ============================================
    # ÉTAPE 6: SUPPRESSION (si demandée) - VERSION SIMPLIFIÉE
    # ============================================
    if remove_duplicates:
        print("\n" + "=" * 80)
        print("🗑️  SUPPRESSION DES DOUBLONS")
        print("=" * 80)
        
        def delete_file(file_path_str):
            """Fonction simple pour supprimer un fichier"""
            try:
                # Convertir en Path et résoudre le chemin absolu
                file_path = Path(file_path_str).resolve()
                
                if not file_path.exists():
                    return False, f"Fichier introuvable: {file_path}"
                
                # Supprimer le fichier
                file_path.unlink()
                
                # Vérifier que la suppression a réussi
                if file_path.exists():
                    return False, f"Échec de la suppression: {file_path}"
                
                return True, "OK"
            except Exception as e:
                return False, f"Erreur: {e}"
        
        total_removed = 0
        
        # 1. Supprimer les doublons cross (train/test) du TEST
        if check_cross and remove_from in ['test', 'both']:
            print(f"\n🗑️  Suppression des doublons cross du TEST...")
            print(f"   {len(report['cross_duplicates'])} fichiers à supprimer")
            
            count = 0
            for dup in report['cross_duplicates']:
                success, msg = delete_file(dup['test_file'])
                if success:
                    count += 1
                    total_removed += 1
                elif "introuvable" not in msg.lower():
                    print(f"   ⚠️ {Path(dup['test_file']).name}: {msg}")
            
            print(f"   ✅ {count} fichiers supprimés")
        
        # 2. Supprimer les doublons internes du TEST
        if check_test_internal and remove_from in ['test', 'both']:
            print(f"\n🗑️  Suppression des doublons internes du TEST...")
            
            count = 0
            for dup_group in report['test_internal_duplicates']:
                # Garder le premier, supprimer les autres
                for file_path_str in dup_group['files'][1:]:
                    success, msg = delete_file(file_path_str)
                    if success:
                        count += 1
                        total_removed += 1
                    elif "introuvable" not in msg.lower():
                        print(f"   ⚠️ {Path(file_path_str).name}: {msg}")
            
            print(f"   ✅ {count} fichiers supprimés")
        
        # 3. Supprimer les doublons internes du TRAIN
        if check_train_internal and remove_from in ['train', 'both']:
            print(f"\n🗑️  Suppression des doublons internes du TRAIN...")
            
            count = 0
            for dup_group in report['train_internal_duplicates']:
                # Garder le premier, supprimer les autres
                for file_path_str in dup_group['files'][1:]:
                    success, msg = delete_file(file_path_str)
                    if success:
                        count += 1
                        total_removed += 1
                    elif "introuvable" not in msg.lower():
                        print(f"   ⚠️ {Path(file_path_str).name}: {msg}")
            
            print(f"   ✅ {count} fichiers supprimés")
        
        print(f"\n✅ TOTAL: {total_removed} fichiers supprimés avec succès")
    
    # ============================================
    # ÉTAPE 7: EXPORT DU RAPPORT (si demandé)
    # ============================================
    if export_report:
        report_file = f"duplicates_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Rapport exporté: {report_file}")
    
    print("\n" + "=" * 80)
    print("✅ Analyse terminée!")
    print("=" * 80)
    
    return report

# Exemple d'utilisation:
# report = find_all_duplicates_exhaustive(
     train_dir, test_dir,
     check_train_internal=True ,
     check_test_internal=True ,
     check_cross= True,
     remove_duplicates= True ,  # Mettre True pour supprimer
     remove_from='test',  # 'test', 'train', ou 'both'
     export_report= True )


Exécuter l'analyse exhaustive des doublons
============================================

Analyse complète (sans suppression)
report = find_all_duplicates_exhaustive(
    train_dir, test_dir,
    check_train_internal=True,    # Vérifier les doublons dans train
    check_test_internal=True,     # Vérifier les doublons dans test
    check_cross=True,              # Vérifier les doublons entre train et test
    remove_duplicates=True,       # Mettre True pour supprimer automatiquement
    remove_from='test',            # 'test', 'train', ou 'both'
    export_report=True             # Exporter un rapport JSON
)

Pour supprimer les doublons, modifiez remove_duplicates=True ci-dessus
ATTENTION: La suppression est irréversible!
