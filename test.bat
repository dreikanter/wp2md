@echo off
echo Runing WP2MD on test data...
set out_path=..\paradigm.ru\pages\
rmdir /s /q %out_path%
python wp2md.py -l export.log -d %out_path% -m -n abc wordpress.xml
