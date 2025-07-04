import py7zr
from pathlib import Path

INPUT_PATH = Path(r'\\10.35.51.152\Biomeca\Projets\25_AIT_Challenge')
CAMERAS_PATH = INPUT_PATH / '_cameras-dev.7z'
POSES_PATH = INPUT_PATH / '_poses-dev.7z'
EXTRACTION_PATH = INPUT_PATH / './extracted_files'

# Créer le dossier d'extraction s'il n'existe pas
EXTRACTION_PATH.mkdir(exist_ok=True)

# Vérification de l'existence des fichiers
if not CAMERAS_PATH.exists():
    print(f"❌ Fichier cameras introuvable: {CAMERAS_PATH}")
    exit(1)

if not POSES_PATH.exists():
    print(f"❌ Fichier poses introuvable: {POSES_PATH}")
    exit(1)

print("\n🔍 Extraction des données cameras...")
try:
    with py7zr.SevenZipFile(CAMERAS_PATH, mode='r') as archive:
        all_files = archive.getnames()
        print(f"📋 Contenu total de l'archive cameras: {len(all_files)} fichiers")
        
        # Filtrer les fichiers .npz
        npz_files = [f for f in all_files if f.endswith('.npz')]
        print(f"🎯 Fichiers .npz trouvés: {len(npz_files)}")
        
        if npz_files:
            for npz_file in npz_files:
                print(f"   📄 {npz_file}")
            
            # Extraire tous les fichiers .npz
            print(f"\n📦 Extraction de {len(npz_files)} fichiers .npz...")
            archive.extract(path=str(EXTRACTION_PATH), targets=npz_files)
            print("✅ Extraction cameras terminée!")
        else:
            print("⚠️ Aucun fichier .npz trouvé dans l'archive cameras")
        
except Exception as e:
    print(f"❌ Erreur lors de l'extraction cameras: {e}")

print("\n🔍 Extraction des données poses...")
try:
    with py7zr.SevenZipFile(POSES_PATH, mode='r') as archive:
        all_files = archive.getnames()
        print(f"📋 Contenu total de l'archive poses: {len(all_files)} fichiers")
        
        # Filtrer les fichiers .npz
        npz_files = [f for f in all_files if f.endswith('.npz')]
        print(f"🎯 Fichiers .npz trouvés: {len(npz_files)}")
        
        if npz_files:
            for npz_file in npz_files:
                print(f"   📄 {npz_file}")
            
            # Extraire tous les fichiers .npz
            print(f"\n📦 Extraction de {len(npz_files)} fichiers .npz...")
            archive.extract(path=str(EXTRACTION_PATH), targets=npz_files)
            print("✅ Extraction poses terminée!")
        else:
            print("⚠️ Aucun fichier .npz trouvé dans l'archive poses")
        
except Exception as e:
    print(f"❌ Erreur lors de l'extraction poses: {e}")

print(f"\n🎉 Extraction terminée!")
print(f"📁 Fichiers extraits dans: {EXTRACTION_PATH}")

# Lister les fichiers extraits
if EXTRACTION_PATH.exists():
    extracted_files = list(EXTRACTION_PATH.rglob('*.npz'))
    print(f"📊 Total de fichiers .npz extraits: {len(extracted_files)}")
    for file in extracted_files:
        print(f"   ✅ {file}") 