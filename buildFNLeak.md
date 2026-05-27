cd "/Users/zachandelman/Desktop/Coding Crap/ClaudeCode/FNLeak"

# 1. Nuke all old build artifacts
rm -rf build dist

# 2. Rebuild clean
python3 -m PyInstaller FNLeak.spec

# 3. Zip when done
cd dist && zip -r ../FNLeak-v1.2.0-macOS.zip FNLeak.app