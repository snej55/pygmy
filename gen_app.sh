#!/usr/bin/env bash
if [ ! -d "release/bin" ]; then
    mkdir -p release/bin
fi

arch="$(uname -m)"
os="$OSTYPE"
dest=pygmy-$os-$arch
icon=release/icon.ico

if [ ! -d "$dest" ]; then
    mkdir $dest
else
    rm -rf $dest
    mkdir $dest
fi

cd release/bin
pyinstaller "../../main.py" --onefile --icon "../icon.ico" --splash ../../splash.png --optimize 2
cd ..

APPDIR=Pygmy.AppDir
rm -rf $APPDIR
mkdir -p $APPDIR/usr/bin
cp bin/dist/main  $APPDIR/usr/bin/
cp -r ../data $APPDIR/usr/bin
cp icon.png $APPDIR/
cp Pygmy.desktop $APPDIR/
echo '#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="$HERE/usr/lib:$LD_LIBRARY_PATH"
exec "$HERE/usr/bin/main" "$@"' > $APPDIR/AppRun
chmod +x $APPDIR/AppRun

curl -L "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" > "appimagetool"
chmod +x ./appimagetool

set -x ARCH x86_64
./appimagetool $APPDIR

# set APPDIR "release/DuckBowling.AppDir"
# rm -rf $APPDIR
# mkdir -p $APPDIR/usr/bin
# # copy assets
# cp build/main $APPDIR/usr/bin/
# cp -r build/data $APPDIR/usr/bin/
# cp -r build/shaders $APPDIR/usr/bin/
# cp release/icon.png $APPDIR/
# cp release/DuckBowling.desktop $APPDIR/
# echo '#!/bin/bash
# HERE="$(dirname "$(readlink -f "${0}")")"
# export LD_LIBRARY_PATH="$HERE/usr/lib:$LD_LIBRARY_PATH"
# exec "$HERE/usr/bin/main" "$@"' > $APPDIR/AppRun
# chmod +x $APPDIR/AppRun

# if not test -f release/appimagetool
#     curl -L "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" > "release/appimagetool"
#     chmod +x ./release/appimagetool
# end

# set -x ARCH x86_64
# cd release; ./appimagetool DuckBowling.AppDir