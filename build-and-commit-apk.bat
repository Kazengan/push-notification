@echo off
echo Building APK...
cd flutter_app
call flutter build apk --release
cd ..

echo Adding APK to git...
git add -f flutter_app/build/app/outputs/flutter-apk/app-release.apk

echo APK built and added to git successfully!
echo File location: flutter_app/build/app/outputs/flutter-apk/app-release.apk