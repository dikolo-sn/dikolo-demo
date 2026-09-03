a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('data', 'data')], # si tu as des dossiers
    hiddenimports=['requests', 'qrcode', 'qrcode.image.pil', 'qrcode.image.svg'], # <-- AJOUTE CA
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)