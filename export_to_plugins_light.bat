
REM Copy the plugin to the QGIS plugins folder
REM xcopy /e /q /y ".\mod_check" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\"

REM Copy only the files that are likely to be updated.
REM For a full copy use "export_to_plugins.bat"
REM xcopy /q /y ".\mod_check\forms.py" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\mod_check\forms.py"
REM xcopy /q /y ".\mod_check\mod_check_dialog_base.py" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\mod_check\mod_check_dialog_base.py"
REM xcopy /q /y ".\mod_check\mod_check_dialog_base.ui" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\mod_check\mod_check_dialog_base.ui"

xcopy /q /y ".\mod_check\menu.py" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\mod_check\menu.py"
xcopy /q /y ".\mod_check\dialogs.py" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\mod_check\dialogs.py"
xcopy /q /y ".\mod_check\mod_check.py" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\mod_check\mod_check.py"
xcopy /e /q /y ".\mod_check\tools" "C:\Users\ermev\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\mod_check\tools"

::PAUSE