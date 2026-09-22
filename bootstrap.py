"""One-time cloud bootstrap for the London atlas. No network or dependencies."""
from pathlib import Path
import zipfile,hashlib
root=Path(__file__).resolve().parent
archive=root/'london-atlas-cloud-source.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='d80ca92a815c10387d701c7535c75ca03f4458fbf237427a7778a2adb226ddcd','Source archive checksum mismatch'
with zipfile.ZipFile(archive) as z:
 for info in z.infolist():
  target=(root/info.filename).resolve()
  assert target.is_relative_to(root) and '.git' not in Path(info.filename).parts,'Unsafe archive path'
 z.extractall(root)
print('London atlas source ready. Run: node serve.cjs')
