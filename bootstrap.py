"""Restore bundled assets only; never overwrite source or edited assets."""
from pathlib import Path
import hashlib,zipfile
root=Path(__file__).resolve().parent
archive=root/'london-atlas-cloud-source.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='d80ca92a815c10387d701c7535c75ca03f4458fbf237427a7778a2adb226ddcd','Asset archive checksum mismatch'
count=0
with zipfile.ZipFile(archive) as z:
 for info in z.infolist():
  if not info.filename.startswith(('dist/assets/','dist/vendor/')) or info.is_dir():continue
  target=(root/info.filename).resolve()
  assert target.is_relative_to(root),'Unsafe path'
  if target.exists():continue
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(z.read(info))
  count+=1
print(f'London atlas: {count} missing assets restored')
