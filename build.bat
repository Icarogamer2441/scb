@echo off
setlocal enabledelayedexpansion

set EXAMPLES_DIR=examples
set EXAMPLES= vars hello funcs labels char structs structs2 enums stringbuff pointer pointer2 arrays shifts get_value stack struct_bytes

if "%1" == "all" (
    for %%e in (%EXAMPLES%) do (
        echo Compiling %EXAMPLES_DIR%\%%e.scb
        python scbc.py --target win64 -c %EXAMPLES_DIR%\%%e.scb
    )
    exit /b 0
)

if "%1" == "clean" (
    echo Cleaning examples...
    del /Q %EXAMPLES_DIR%\*.exe 2>nul
    del /Q %EXAMPLES_DIR%\*.s 2>nul
    echo Done.
    exit /b 0
)

if "%1" == "runall" (
    for %%e in (%EXAMPLES%) do (
        echo Running %%e
        call %EXAMPLES_DIR%\%%e.exe
        echo.
    )
    exit /b 0
)

if "%1" == "build" (
    pyinstaller --onefile scbc.py
    exit /b 0
)

if "%1" == "scbclean" (
    echo Cleaning build artifacts...
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul
    rmdir /s /q __pycache__ 2>nul
    del *.spec 2>nul
    del *.pyc 2>nul
    del *.pyo 2>nul
    echo Done.
    exit /b 0
)

echo Usage: build.bat [command]
echo Commands:
echo   all       - Build all examples
echo   clean     - Remove compiled examples
echo   runall    - Run all examples
echo   build     - Create standalone executable
echo   install   - Install system-wide
echo   uninstall - Remove system-wide installation
echo   scbclean  - Clean build artifacts
exit /b 1 