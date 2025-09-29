@echo off
echo Building APK...
cd flutter_app
call flutter build apk --release
cd ..

echo Adding APK to git...
git add -f flutter_app/build/app/outputs/flutter-apk/app-release.apk
git add -f flutter_app/android/app/release/app-release.apk 2>nul

echo APK built and added to git successfully!
echo Main APK location: flutter_app/build/app/outputs/flutter-apk/app-release.apk
echo Alternative location: flutter_app/android/app/release/app-release.apk