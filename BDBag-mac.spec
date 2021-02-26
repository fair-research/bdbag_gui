# -*- mode: python -*-

block_cipher = None

from PyInstaller.utils.hooks import copy_metadata

metadata = []
metadata.append(copy_metadata('bagit')[0])
metadata.append(copy_metadata('bagit_profile')[0])
metadata.append(copy_metadata('bdbag')[0])
metadata.append(copy_metadata('bdbag_gui')[0])

a = Analysis(['bdbag_gui/__main__.py'],
             pathex=[],
             binaries=None,
             datas=metadata,
             hiddenimports=['bdbag', 'bagit', 'boto3', 'botocore', 's3transfer', 'globus_sdk'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='BDBag',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='bdbag_gui/images/bag.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='BDBagGUI')

app = BUNDLE(coll,
         name='BDBag.app',
         icon='bdbag_gui/images/bag.icns',
         bundle_identifier='edu.isi.isrd.BDBag',
         info_plist={
            'CFBundleDisplayName': 'BDBag',
            'CFBundleShortVersionString':'1.1.0',
            'NSPrincipalClass':'NSApplication',
            'NSHighResolutionCapable': 'True'
         })
