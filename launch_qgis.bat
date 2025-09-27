@REM @echo off
@REM SET PYTHONPATH=C:\Program Files\QGIS 3.28.14\apps\qgis-ltr\python;C:\Program Files\QGIS 3.28.14\apps\qgis-ltr\python\plugins;C:\Program Files\QGIS 3.28.14\apps\Qt5\plugins;C:\Program Files\QGIS 3.28.14\apps\gdal\share\gdal;
@REM SET PATH=C:\Program Files\QGIS 3.28.14\apps\Python39%PATH%
@REM "C:\Program Files\QGIS 3.28.14\apps\Python39\pyqgis.exe" main.py



@REM ===================================================================================================

@echo off

SET PYTHONPATH=C:\Program Files\QGIS 3.28.14\apps\qgis-ltr\python;C:\Program Files\QGIS 3.28.14\apps\qgis-ltr\python\plugins;C:\Program Files\QGIS 3.28.14\apps\Qt5\plugins;C:\Program Files\QGIS 3.28.14\apps\gdal\share\gdal;
SET PATH=C:\Program Files\QGIS 3.28.14\apps\Python39;%PATH%

@REM where python
@REM python --version

REM === Run your Python script ===
echo ====== Running Prediction Automation =====
"C:\Program Files\QGIS 3.28.14\apps\Python39\pyqgis.exe" main.py


echo ==== Prediction Automation Script completed =======
pause
