@echo off
REM ===============================
REM OneKillOneClip Release 1.0 打包脚本
REM ===============================

echo ===============================
echo 清理旧的 build/dist/temp 文件
echo ===============================
rmdir /s /q build
rmdir /s /q dist
del /q OneKillOneClip.spec

REM ===============================
REM 打包
pyinstaller --noconfirm --clean ^
    --name "OneKillOneClip" ^
    --windowed ^
    --add-data "match_templates;match_templates" ^
    --add-data "UI_interface;UI_interface" ^
    --add-data "code;code" ^
    main.py

REM 删除临时 spec 文件
del /q OneKillOneClip.spec

echo ===============================
echo 打包完成！Release 文件在 dist 文件夹中
echo ===============================
pause
