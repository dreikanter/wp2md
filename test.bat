@echo off
rem Runs the script on test data
rem Usage:
rem	test wordpress-dump.xml
rem	test -v wordpress-dump.xml

set out_path=out
rmdir /s /q %out_path%
python wp2md.py -l export.log -d %out_path% %*
