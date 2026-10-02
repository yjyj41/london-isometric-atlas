"""Restore generated assets offline; upgrade unchanged legacy assets, preserve user edits."""
from pathlib import Path
import hashlib,zipfile,subprocess,contextlib,sys
root=Path(__file__).resolve().parent
bundles=[['london-atlas-catalogue-models.zip', '425a5962a1d5ca9175f5b1c215edab3af76383b94a81aca09e89c5de5a3a880d'], ['london-atlas-catalogue-central.zip', '0a170cab2f6f29d61be30b2be9dace78c73ea6d2177a03efec165b46b1cb3d34'], ['london-atlas-catalogue-outer.zip', 'e8b11a015b6fd1c3023b7118c5fd330ef322fa431411fd876532f0764c224ff2'], ['london-atlas-english-landmarks-models.zip', '42ddc490c8528cd6916b6bc1a8a0ca9ad53e614fe6aea331e39b57e02c6a9c10'], ['london-atlas-english-landmarks-regions.zip', '8473d114e8230377509443428f21340348cdb3cb10549df1569327d4d015eec1'], ['london-atlas-landmark-detail-models.zip', 'e5c634f5970556d9b66364acc1a40bfdd8d4265899ff981fd81d5e9173d52a2b'], ['london-atlas-landmark-detail-regions.zip', '7b85a55b0b948d08cbbc7a4b9e6232ec63301f397158cfd59d42d05d375ac839'], ['london-atlas-east-south-models.zip', 'a327cbaf1750605ec8f6baa211ff931337eb56cc23b30722ce73b115e2e1fc80'], ['london-atlas-east-south-regions.zip', 'db2dc1ebc203369478f5a7039fb1941e872d2835e56b8aa0958a46122e532762'], ['london-atlas-north-assets.zip', 'd39e6404a603711bad3a9f3fc9f6f2e15ad507f144afef849505ddad0d2bcd78'], ['london-atlas-cloud-source.zip', 'd80ca92a815c10387d701c7535c75ca03f4458fbf237427a7778a2adb226ddcd']]
tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0'))
restored=updated=0;conflicts=[];handled=set()
with contextlib.ExitStack() as stack:
 archives=[]
 for filename,checksum in bundles:
  archive=root/filename
  assert hashlib.sha256(archive.read_bytes()).hexdigest()==checksum,'Asset bundle checksum mismatch: '+filename
  archives.append(stack.enter_context(zipfile.ZipFile(archive)))
 for i,z in enumerate(archives):
  for info in z.infolist():
   name=info.filename
   if name in ['dist/assets/rhino/london-mass-city.zip','dist/assets/rhino/london-mass-city-rhino6.zip'] or (name.startswith('dist/assets/rhino/catalog-') and name.endswith('.3dm') and not name.endswith('-rhino6.3dm')):continue
   if name in handled or info.is_dir() or not name.startswith(('dist/assets/','dist/vendor/')):continue
   handled.add(name)
   if name in tracked:continue
   target=(root/name).resolve();assert target.is_relative_to(root)
   new=z.read(info)
   if target.exists():
    old=target.read_bytes()
    if old==new:continue
    # Only replace bytes from a verified prior bundle, never arbitrary local changes.
    legacy=any(name in archive.namelist() and old==archive.read(name) for archive in archives[i+1:])
    if not legacy:conflicts.append(name);continue
    updated+=1
   else:restored+=1
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(new)
print('Restored',restored,'missing assets; upgraded',updated,'unchanged legacy assets offline.')
if conflicts:
 print('Preserved locally modified assets; reconcile them with the new map before rebuilding:')
 for name in conflicts:print(' -',name)
 sys.exit(2)

# Restore the complete editable catalogue only when absent; preserve local edits.
full=root/"tools/city-full.json"
if not full.exists():
 with zipfile.ZipFile(root/"dist/assets/city-data.zip") as z: full.write_bytes(z.read("city.json"))
 print("Restored complete editable city source.")
