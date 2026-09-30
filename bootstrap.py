from pathlib import Path
import hashlib,zipfile
root=Path(__file__).resolve().parent
# Extension first, then the original vendor/base assets. Existing edited assets survive.
bundles=[('london-atlas-north-assets.zip','d39e6404a603711bad3a9f3fc9f6f2e15ad507f144afef849505ddad0d2bcd78'),('london-atlas-cloud-source.zip','d80ca92a815c10387d701c7535c75ca03f4458fbf237427a7778a2adb226ddcd')]
count=0
for filename,checksum in bundles:
 archive=root/filename
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==checksum,'Asset bundle checksum mismatch'
 with zipfile.ZipFile(archive) as z:
  for info in z.infolist():
   if not info.filename.startswith(('dist/assets/','dist/vendor/')) or info.is_dir():continue
   target=(root/info.filename).resolve()
   assert target.is_relative_to(root)
   if target.exists():continue
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(z.read(info));count+=1
print('Restored',count,'missing assets offline.')
